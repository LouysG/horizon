"""CRUD, batch ingestion, and viewport queries for Horizon tables.

Pass a caller-owned connection from horizon.db.connection.connect. CRUD and
viewport queries participate in any open transaction. Batch ingestion owns its
transaction. DuckDB errors propagate to the caller.
Geometry values are WKT in EPSG:4326 (longitude, latitude). Timestamp results are
UTC-aware datetime objects. Pass aware datetimes or strings with an explicit offset.
"""

from collections.abc import Iterable, Mapping
from contextlib import suppress
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from duckdb import DuckDBPyConnection, TransactionException

# ---------------------------------------------------------------------------
# Horizon table metadata and SQL identifiers
# ---------------------------------------------------------------------------

_PRIMARY_KEYS = {
    "data_source": ("source_id",),
    "ingestion_run": ("ingestion_id",),
    "building": ("feature_id",),
    "terrain": ("terrain_id",),
    "airspace_restriction": ("restriction_id",),
    "controlled_airspace": ("airspace_id",),
    "uas_facility_grid": ("grid_id",),
    "aircraft": ("aircraft_id",),
    "aircraft_telemetry": ("aircraft_id", "timestamp"),
    "weather_sensor": ("sensor_id",),
    "weather_observations": ("observed_at", "sensor_id"),
}

_TIMESTAMPTZ = "TIMESTAMP WITH TIME ZONE"
_SPATIAL_COLUMNS = {
    "building": "geometry",
    "terrain": "coverage",
    "airspace_restriction": "geometry",
    "controlled_airspace": "geometry",
    "uas_facility_grid": "geometry",
    "aircraft_telemetry": "location",
    "weather_sensor": "location",
    "weather_observations": "location",
}
_OBSERVATION_TIMES = {"aircraft_telemetry": "timestamp", "weather_observations": "observed_at"}
_INGESTION_LOCK = Lock()

type Row = dict[str, Any]
type Bounds = tuple[float, float, float, float]


def _identifier(name: str) -> str:

    # Escape embedded quotes before delimiting the SQL identifier.
    return '"' + name.replace('"', '""') + '"'


class DataAccess:
    """Read and write Horizon rows using the supplied database connection."""

    def __init__(self, connection: DuckDBPyConnection) -> None:

        # Keep the caller's connection and prepare the Horizon table cache.
        self._connection = connection
        self._columns: dict[str, dict[str, str]] = {table: {} for table in _PRIMARY_KEYS}

        # Load column types in table order for validation and row conversion.
        for table, column, data_type in connection.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_catalog = current_database() AND table_schema = 'main'
            ORDER BY ordinal_position
            """
        ).fetchall():
            if table in self._columns:
                self._columns[table][column] = data_type

    # -----------------------------------------------------------------------
    # Create, read, update, and delete
    # -----------------------------------------------------------------------

    def create(self, table: str, values: Mapping[str, Any]) -> Row:
        """Insert a row and return it, including any generated ID and defaults."""

        # Build the insert from validated column names and bound values.
        columns = self._validate_columns(table, values)
        target = f"main.{_identifier(table)}"
        if values:
            names = ", ".join(_identifier(name) for name in values)
            placeholders = ", ".join("?" for _ in values)
            insert = f"INSERT INTO {target} ({names}) VALUES ({placeholders})"
        else:
            insert = f"INSERT INTO {target} DEFAULT VALUES"

        # Return the stored row with database-generated fields filled in.
        result = self._connection.execute(
            f"{insert} RETURNING {self._projection(columns)}", list(values.values())
        ).fetchall()
        return self._row(columns, result[0])

    def get(self, table: str, key: Mapping[str, Any]) -> Row | None:
        """Return the row identified by its full primary key, or None."""

        # Fetch a single row using its full primary key.
        where, parameters = self._key_filter(table, key)
        columns = self._columns[table]
        result = self._connection.execute(
            f"SELECT {self._projection(columns)} FROM main.{_identifier(table)} WHERE {where}",
            parameters,
        ).fetchone()
        return None if result is None else self._row(columns, result)

    def list_rows(self, table: str) -> list[Row]:
        """Return all rows ordered by their primary key."""

        # Fetch and convert rows in a stable primary-key order.
        columns = self._validate_columns(table, {})
        order = ", ".join(_identifier(name) for name in _PRIMARY_KEYS[table])
        rows = self._connection.execute(
            f"SELECT {self._projection(columns)} FROM main.{_identifier(table)} ORDER BY {order}"
        ).fetchall()
        return [self._row(columns, row) for row in rows]

    def update(self, table: str, key: Mapping[str, Any], changes: Mapping[str, Any]) -> bool:
        """Change the supplied non-key columns. Return whether a row matched."""

        # Validate the target key and restrict changes to non-key columns.
        self._validate_columns(table, changes)
        where, parameters = self._key_filter(table, key)
        if not changes or changes.keys() & key.keys():
            raise ValueError("Supply at least one change and omit primary-key columns.")

        # Use plain UPDATE to get a row count and avoid DuckDB's referenced-row rewrite.
        assignments = ", ".join(f"{_identifier(name)} = ?" for name in changes)
        result = self._connection.execute(
            f"UPDATE main.{_identifier(table)} SET {assignments} WHERE {where}",
            [*changes.values(), *parameters],
        ).fetchone()
        return bool(result and result[0])

    def delete(self, table: str, key: Mapping[str, Any]) -> bool:
        """Delete a row by primary key. Return whether a row matched."""

        # Delete by the complete key and report whether a row was affected.
        where, parameters = self._key_filter(table, key)
        result = self._connection.execute(
            f"DELETE FROM main.{_identifier(table)} WHERE {where}", parameters
        ).fetchone()
        return bool(result and result[0])

    # -----------------------------------------------------------------------
    # Batch ingestion and retry handling
    # -----------------------------------------------------------------------

    def ingest_rows(
        self,
        table: str,
        rows: Iterable[Mapping[str, Any]],
        *,
        source_id: int,
        ingestion_id: int,
        acquired_at: datetime,
    ) -> int:
        """Insert a batch for one source and run. Return the number inserted.

        Each row supplies a unique nonblank source_record_id within the batch.
        The batch supplies the other provenance fields. Existing rows for the
        same (source_id, source_record_id) are kept as-is on retry. Use update
        to apply corrections. Ambiguous existing matches abort the batch.
        Call outside an open transaction. Route concurrent ingestion batches
        through this method for process-local retry protection.
        """

        # Check that the table supports ingestion and assemble shared provenance.
        columns = self._validate_columns(table, {})
        if "source_record_id" not in columns:
            raise ValueError(f"{table} does not store ingested records.")
        if acquired_at.utcoffset() is None:
            raise ValueError("acquired_at must be timezone-aware.")
        provenance = {
            "source_id": source_id,
            "ingestion_id": ingestion_id,
            "acquired_at": acquired_at,
        }

        # Validate the batch and index incoming rows by source record ID.
        batch: dict[str, Mapping[str, Any]] = {}
        for row in rows:
            self._validate_columns(table, row)
            if row.keys() & provenance.keys():
                raise ValueError("Supply source_id, ingestion_id, and acquired_at for the batch.")
            record_id = row.get("source_record_id")
            if not isinstance(record_id, str) or not record_id.strip():
                raise ValueError("Each row must have a nonblank source_record_id.")
            if record_id in batch:
                raise ValueError(f"Duplicate source_record_id in batch: {record_id!r}")
            batch[record_id] = dict(row)
        if not batch:
            return 0

        # Serialize ingestion batches so concurrent retries see committed rows.
        with _INGESTION_LOCK:
            self._connection.begin()
            try:
                # Verify the ingestion run belongs to the batch's source.
                run = self.get("ingestion_run", {"ingestion_id": ingestion_id})
                if run is None or run["source_id"] != source_id:
                    raise ValueError("The ingestion run must belong to the batch's source.")

                # Find previously ingested records and reject ambiguous matches.
                matches = self._connection.execute(
                    f"""
                    SELECT source_record_id, count(*)
                    FROM main.{_identifier(table)}
                    WHERE source_id = ? AND source_record_id IN (SELECT unnest(?))
                    GROUP BY source_record_id
                    """,
                    [source_id, list(batch)],
                ).fetchall()
                for record_id, count in matches:
                    if count > 1:
                        raise ValueError(
                            f"Multiple existing rows for source_record_id {record_id!r}"
                        )
                existing = {record_id for record_id, _ in matches}

                # Insert new records and commit the batch together.
                for record_id, row in batch.items():
                    if record_id not in existing:
                        self.create(table, {**row, **provenance})
                self._connection.commit()
            except BaseException:
                # Roll back the batch and preserve the original exception.
                with suppress(TransactionException):
                    self._connection.rollback()
                raise

        # Count only records inserted by this batch.
        return len(batch) - len(existing)

    # -----------------------------------------------------------------------
    # Spatial and temporal queries for visualization
    # -----------------------------------------------------------------------

    def query_viewport(
        self,
        table: str,
        bounds: Bounds,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Row]:
        """Return rows intersecting (west, south, east, north) in EPSG:4326.

        Bounds may cross the antimeridian. Telemetry and weather observations
        accept optional timezone-aware time bounds, inclusive at start and
        exclusive at end. Weather observations include their sensor's current
        location as WKT. Rows are ordered by primary key.
        """

        # Validate the target table and geographic bounds.
        if table not in _SPATIAL_COLUMNS:
            raise ValueError(f"{table!r} has no viewport query.")
        west, south, east, north = bounds
        if (
            not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south < north <= 90)
            or west == east
            or (west, east) == (180, -180)
        ):
            raise ValueError("Supply valid longitude and latitude bounds with positive area.")

        # Validate the time window for tables with observations.
        time_column = _OBSERVATION_TIMES.get(table)
        if time_column is None and (start is not None or end is not None):
            raise ValueError("Time bounds apply to telemetry and weather observations.")
        if any(bound is not None and bound.utcoffset() is None for bound in (start, end)):
            raise ValueError("Time bounds must be timezone-aware.")
        if start is not None and end is not None and start.astimezone(UTC) >= end.astimezone(UTC):
            raise ValueError("The time bound start must precede end.")

        # Select the feature geometry, joining the sensor for weather observations.
        columns = self._columns[table]
        projection = self._projection(columns, qualifier="feature.")
        relation = f"main.{_identifier(table)} AS feature"
        geometry = f"feature.{_identifier(_SPATIAL_COLUMNS[table])}"
        if table == "weather_observations":
            geometry = "sensor.location"
            relation += " JOIN main.weather_sensor AS sensor USING (sensor_id)"
            projection += ", ST_AsText(sensor.location)"
            columns = {**columns, "location": "GEOMETRY"}

        # Split a viewport that crosses the antimeridian into two envelopes.
        boxes = [bounds] if west < east else [(west, south, 180, north), (-180, south, east, north)]
        intersects = (
            f"ST_Intersects({geometry}, ST_MakeEnvelope(?, ?, ?, ?)::GEOMETRY('EPSG:4326'))"
        )
        predicates = ["(" + " OR ".join(intersects for _ in boxes) + ")"]
        parameters: list[Any] = [coordinate for box in boxes for coordinate in box]

        # Add the supplied boundaries for the half-open time window.
        if time_column is not None:
            for operator, bound in ((">=", start), ("<", end)):
                if bound is not None:
                    predicates.append(f"feature.{_identifier(time_column)} {operator} ?")
                    parameters.append(bound)

        # Fetch and convert the matching rows in primary-key order.
        where = " AND ".join(predicates)
        order = ", ".join(f"feature.{_identifier(name)}" for name in _PRIMARY_KEYS[table])
        rows = self._connection.execute(
            f"SELECT {projection} FROM {relation} WHERE {where} ORDER BY {order}", parameters
        ).fetchall()
        return [self._row(columns, row) for row in rows]

    # -----------------------------------------------------------------------
    # Column validation and row conversion
    # -----------------------------------------------------------------------

    def _validate_columns(self, table: str, values: Mapping[str, Any]) -> dict[str, str]:
        """Return the table's column types, raising ValueError for unknown names."""

        # Check the table name before accessing its column metadata.
        if table not in self._columns:
            raise ValueError(f"Unknown Horizon table: {table!r}")

        # Confirm that each supplied column belongs to the table.
        columns = self._columns[table]
        if unknown := values.keys() - columns.keys():
            raise ValueError(f"Unknown columns for {table}: {sorted(unknown)}")
        return columns

    def _key_filter(self, table: str, key: Mapping[str, Any]) -> tuple[str, list[Any]]:
        """Build a SQL predicate and ordered parameters from a complete, non-null primary key."""

        # Require exactly the table's primary-key fields with non-null values.
        self._validate_columns(table, key)
        primary_key = _PRIMARY_KEYS[table]
        if key.keys() != set(primary_key) or any(value is None for value in key.values()):
            raise ValueError(f"{table} requires these primary-key fields: {', '.join(primary_key)}")

        # Match the parameter order to the primary-key predicate.
        where = " AND ".join(f"{_identifier(name)} = ?" for name in primary_key)
        return where, [key[name] for name in primary_key]

    @staticmethod
    def _projection(columns: Mapping[str, str], qualifier: str = "") -> str:
        """Build a SQL column list that returns geometries as WKT and timestamps in UTC."""

        # Apply SQL conversions while preserving the table's column order.
        expressions = []
        for name, data_type in columns.items():
            column = qualifier + _identifier(name)
            if data_type.startswith("GEOMETRY"):
                column = f"ST_AsText({column})"
            elif data_type == _TIMESTAMPTZ:
                # Fetch UTC wall time so DuckDB's Python client need not load pytz.
                column = f"{column} AT TIME ZONE 'UTC'"
            expressions.append(column)

        return ", ".join(expressions)

    @staticmethod
    def _row(columns: Mapping[str, str], values: tuple[Any, ...]) -> Row:
        """Map projected values to column names and attach UTC timezone info to timestamps."""

        # Pair values with their column names and mark projected timestamps as UTC.
        return {
            name: value.replace(tzinfo=UTC) if value is not None and kind == _TIMESTAMPTZ else value
            for (name, kind), value in zip(columns.items(), values, strict=True)
        }
