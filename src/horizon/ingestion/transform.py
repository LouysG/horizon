"""Normalize landed data and persist it through Horizon's data access layer."""

import json
import logging
from datetime import UTC, datetime
from hashlib import file_digest, sha256
from math import isfinite
from pathlib import Path
from shutil import copyfile
from subprocess import check_output
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import ZipFile

from duckdb import DuckDBPyConnection

from horizon.db.connection import DEFAULT_DATABASE_PATH, connect
from horizon.db.data_access import DataAccess, Row

from .acquire import Acquisition, acquire, select_stations
from .plan import BUILDINGS, FACILITY_MAP, NASR, SPECIAL_USE, TERRAIN, WEATHER, Bounds, plan

logger = logging.getLogger(__name__)


def _features(raw: Acquisition, prefix: str):

    # Read the provider's GeoJSON pages in landing order.
    for name in raw.files:
        if name.startswith(prefix):
            yield from json.loads((raw.directory / name).read_bytes())["features"]


def _number(value: Any, minimum: float = 0) -> float | None:

    # Represent missing and invalid optional measurements as null.
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) and number >= minimum else None


def _geometry(
    connection: DuckDBPyConnection, geometry: Any, bounds: Bounds | None = None
) -> str | None:

    # Ignore invalid shapes and retain full geometries that intersect the request.
    if not isinstance(geometry, dict):
        return None
    kind = ("POINT",) if bounds is None else ("POLYGON", "MULTIPOLYGON")
    where = "" if bounds is None else "AND ST_Intersects(geom, ST_MakeEnvelope(?, ?, ?, ?))"
    result = connection.execute(
        f"""
        SELECT ST_AsText(geom)
        FROM (SELECT TRY(ST_GeomFromGeoJSON(?)) AS geom)
        WHERE ST_GeometryType(geom) IN (SELECT unnest(?))
          AND NOT ST_IsEmpty(geom) AND ST_IsValid(geom) {where}
        """,
        [json.dumps(geometry), list(kind), *(bounds or ())],
    ).fetchone()
    return result[0] if result else None


def _arcgis_rows(connection: DuckDBPyConnection, raw: Acquisition) -> tuple[str, list[Row]]:

    # Map each provider's public fields into its corresponding Horizon table.
    source = raw.resource.source
    table = {
        BUILDINGS: "building",
        SPECIAL_USE: "airspace_restriction",
        FACILITY_MAP: "uas_facility_grid",
    }[source]
    rows = []
    for feature in _features(raw, "features-"):
        geometry = _geometry(connection, feature.get("geometry"), raw.resource.bounds)
        fields = {key.upper(): value for key, value in (feature.get("properties") or {}).items()}
        identifier = fields.get("OBJECTID", feature.get("id"))
        if geometry is None or identifier is None:
            logger.warning("Skipping invalid or out-of-area %s feature %s", source, identifier)
            continue
        row: Row = {"geometry": geometry}
        if source == BUILDINGS:
            row["height_m"] = _number(fields.get("HEIGHT"))
        elif source == SPECIAL_USE:
            row.update(name=fields.get("NAME"), restriction_type=fields.get("TYPE_CODE"))
        else:
            ceiling = _number(fields.get("CEILING"))
            unit = str(fields.get("UNIT") or "").strip().upper()
            row["ceiling_agl_m"] = (
                ceiling * 0.3048
                if ceiling is not None and unit in {"FT", "FEET", "FT AGL"}
                else ceiling
                if unit in {"M", "METERS"}
                else None
            )

        # Keep changed snapshot records alongside previous versions.
        digest = sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        row["source_record_id"] = f"{identifier}:{digest}"
        rows.append(row)
    return table, rows


def _nasr_rows(connection: DuckDBPyConnection, raw: Acquisition) -> list[Row]:

    # Read FAA class boundaries directly from the cycle's shapefile bundle.
    rows: list[Row] = []
    with TemporaryDirectory() as temporary, ZipFile(raw.directory / "airspace.zip") as archive:
        shapes = [name for name in archive.namelist() if name.lower().endswith(".shp")]
        if not shapes:
            raise ValueError("NASR archive contains no shapefiles")
        for name in shapes:
            # Copy only the sidecars sharing this shapefile's exact archive stem.
            stem = Path(name).with_suffix("")
            paths = {
                Path(member).suffix.lower(): Path(archive.extract(member, temporary))
                for member in archive.namelist()
                if Path(member).with_suffix("") == stem
            }
            # DuckDB reads the native CRS when its GDAL driver exposes one.
            result = connection.execute(
                """
                WITH boundaries AS (
                    SELECT * EXCLUDE (geom), ST_Force2D(
                        CASE WHEN ST_CRS(geom) IS NULL
                             THEN ST_Transform(geom, 'EPSG:4269', 'EPSG:4326', true)
                             ELSE ST_Transform(geom, 'EPSG:4326', true)
                        END
                    ) AS geometry
                    FROM ST_Read(?)
                )
                SELECT * EXCLUDE (geometry), ST_AsText(geometry) AS wkt
                FROM boundaries
                WHERE ST_GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')
                  AND NOT ST_IsEmpty(geometry) AND ST_IsValid(geometry)
                  AND ST_Intersects(geometry, ST_MakeEnvelope(?, ?, ?, ?))
                """,
                [str(paths[".shp"]), *raw.resource.bounds],
            )
            columns = [column[0].upper() for column in result.description]
            for values in result.fetchall():
                fields = dict(zip(columns, values, strict=True))
                digest = sha256(repr(values).encode()).hexdigest()
                rows.append(
                    {
                        "source_record_id": f"{raw.resource.version}:{name}:{digest}",
                        "geometry": fields["WKT"],
                        "name": fields.get("NAME") or fields.get("IDENT"),
                        "airspace_class": fields.get("CLASS"),
                        "valid_from": raw.resource.start,
                        "valid_to": raw.resource.end,
                    }
                )
    return rows


def _terrain_rows(connection: DuckDBPyConnection, raw: Acquisition, rasters: Path) -> list[Row]:

    # Read the native raster metadata and preserve the original elevation values.
    rows: list[Row] = []
    for name in raw.files:
        if not name.startswith("terrain-"):
            continue
        tile = raw.directory / name
        info = json.loads(check_output(["gdalinfo", "-json", str(tile)]))
        coverage = _geometry(connection, info.get("wgs84Extent"), raw.resource.bounds)
        crs = info.get("coordinateSystem", {}).get("wkt")
        if coverage is None or not crs:
            logger.warning("Skipping 3DEP tile without usable coverage or CRS: %s", name)
            continue
        vertical_datum = "unknown"
        if "NAVD88" in crs or "North American Vertical Datum 1988" in crs:
            vertical_datum = "NAVD88"

        # Publish a durable content-addressed raster before referring to it in DuckDB.
        with tile.open("rb") as stream:
            digest = file_digest(stream, "sha256").hexdigest()
        rasters.mkdir(parents=True, exist_ok=True)
        target = (rasters / f"{digest}{tile.suffix}").resolve()
        if not target.exists():
            with TemporaryDirectory(dir=rasters) as temporary:
                staged = Path(temporary) / target.name
                copyfile(tile, staged)
                staged.replace(target)
        rows.append(
            {
                "source_record_id": digest,
                "coverage": coverage,
                "raster_uri": target.as_uri(),
                "horizontal_crs": crs,
                "vertical_datum": vertical_datum,
                "resolution_m": 1.0,
                "source": raw.files[name],
            }
        )
    return rows


def _weather_rows(
    connection: DuckDBPyConnection, db: DataAccess, raw: Acquisition, provenance: Row
) -> int:

    # Store the station metadata first so observations can reference it.
    stations: dict[str, Row] = {}
    for feature in select_stations(list(_features(raw, "stations-")), raw.resource.bounds):
        properties = feature.get("properties") or {}
        identifier = properties.get("stationIdentifier")
        location = _geometry(connection, feature.get("geometry"))
        if identifier and location:
            stations[identifier] = {
                "source_record_id": identifier,
                "location": location,
                "name": properties.get("name"),
                "elevation_m": _measurement(properties, "elevation", "m", -float("inf")),
            }
    stored = db.ingest_rows("weather_sensor", stations.values(), **provenance)
    sensor_ids = dict(
        connection.execute(
            "SELECT source_record_id, sensor_id FROM weather_sensor WHERE source_id = ?",
            [provenance["source_id"]],
        ).fetchall()
    )

    # Accept only observations in the request's half-open interval.
    observations: dict[str, Row] = {}
    for feature in _features(raw, "observations-"):
        properties = feature.get("properties") or {}
        station = str(properties.get("station", "")).rstrip("/").rsplit("/", 1)[-1]
        if station not in stations:
            continue
        try:
            observed = datetime.fromisoformat(properties["timestamp"])
            if (
                observed.utcoffset() is None
                or not raw.resource.start <= observed < raw.resource.end
            ):
                continue
            observed = observed.astimezone(UTC)
        except (KeyError, TypeError, ValueError):
            logger.warning("Skipping NWS observation with an invalid timestamp at %s", station)
            continue
        identifier = f"{station}:{observed.isoformat()}"
        observations[identifier] = {
            "source_record_id": identifier,
            "sensor_id": sensor_ids[station],
            "observed_at": observed,
            "temperature": _measurement(properties, "temperature", "degC", -273.15),
            "humidity": _measurement(properties, "relativeHumidity", "percent"),
            "precipitation": _measurement(properties, "precipitationLastHour", "mm"),
            "visibility": _measurement(properties, "visibility", "m"),
        }
    return stored + db.ingest_rows("weather_observations", observations.values(), **provenance)


def _measurement(properties: Row, field: str, unit: str, minimum: float = 0) -> float | None:

    # NWS quantitative values include a unit code and can be null.
    measurement = properties.get(field) or {}
    if measurement.get("unitCode") != f"wmoUnit:{unit}":
        return None
    return _number(measurement.get("value"), minimum)


def transform(
    connection: DuckDBPyConnection, raw: Acquisition, rasters: Path = Path("data/rasters")
) -> int:
    """Transform one completed acquisition and return the number of new rows."""

    # Find or register the provider and record the transform attempt.
    db = DataAccess(connection)
    resource = raw.resource
    existing = connection.execute(
        "SELECT source_id FROM data_source WHERE source_name = ? ORDER BY source_id LIMIT 1",
        [resource.source],
    ).fetchone()
    source_id = (
        existing[0]
        if existing
        else db.create(
            "data_source",
            {
                "source_name": resource.source,
                "source_type": "batch",
                "source_uri": resource.url.split("?")[0],
            },
        )["source_id"]
    )
    run = db.create(
        "ingestion_run",
        {
            "source_id": source_id,
            "started_at": raw.acquired_at,
            "status": "running",
        },
    )
    key = {"ingestion_id": run["ingestion_id"]}
    provenance: Row = {**key, "source_id": source_id, "acquired_at": raw.acquired_at}

    # Validate and persist a batch using the existing retry-safe data access method.
    try:
        if resource.source == WEATHER:
            count = _weather_rows(connection, db, raw, provenance)
        else:
            if resource.source == TERRAIN:
                table, rows = "terrain", _terrain_rows(connection, raw, rasters)
            elif resource.source == NASR:
                table, rows = "controlled_airspace", _nasr_rows(connection, raw)
            else:
                table, rows = _arcgis_rows(connection, raw)
            unique = {row["source_record_id"]: row for row in rows}
            count = db.ingest_rows(table, unique.values(), **provenance)
    except Exception:
        db.update("ingestion_run", key, {"status": "failed", "completed_at": datetime.now(UTC)})
        raise
    db.update("ingestion_run", key, {"status": "completed", "completed_at": datetime.now(UTC)})
    return count


def ingest(
    bounds: Bounds,
    start: datetime,
    end: datetime,
    *,
    database: str | Path = DEFAULT_DATABASE_PATH,
    landing: Path = Path("data/landing"),
    rasters: Path = Path("data/rasters"),
    user_agent: str = "Horizon/0.1",
) -> dict[str, int]:
    """Attempt every configured import, then report inserted counts or raise failures."""

    # Run all planned imports even if an individual provider fails.
    resources = plan(bounds, start, end)
    counts: dict[str, int] = {}
    failures: list[Exception] = []
    with connect(database) as connection:
        for resource in resources:
            try:
                raw = acquire(resource, landing, user_agent=user_agent)
                counts[resource.source] = counts.get(resource.source, 0) + transform(
                    connection, raw, rasters
                )
            except Exception as error:
                error.add_note(f"{resource.source}: {resource.url}")
                failures.append(error)
    if failures:
        raise ExceptionGroup("One or more Horizon imports failed", failures)
    return counts
