"""Plan a batch import of Horizon's six configured datasets."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

type Bounds = tuple[float, float, float, float]

TERRAIN = "USGS 3DEP 1m"
WEATHER = "National Weather Service API"
BUILDINGS = "FEMA USA Structures"
SPECIAL_USE = "FAA Special Use Airspace"
FACILITY_MAP = "FAA UAS Facility Map"
NASR = "FAA NASR"

# The FAA publishes NASR on a 28-day cycle.
NASR_CYCLE = timedelta(days=28)
NASR_REFERENCE = datetime(2026, 10, 1, 9, 1, tzinfo=UTC)


@dataclass(frozen=True)
class Resource:
    """A provider request and the scope needed to acquire and transform it."""

    source: str
    url: str
    bounds: Bounds
    start: datetime
    end: datetime
    version: str | None = None


def query_url(url: str, **parameters: object) -> str:
    """Append provider query parameters to a base URL."""

    return f"{url}?{urlencode(parameters)}"


def plan(bounds: Bounds, start: datetime, end: datetime) -> list[Resource]:
    """Plan a WGS 84 bounding box and a half-open interval of aware datetimes."""

    # Validate the request before making any provider calls.
    west, south, east, north = bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Expected WGS 84 bounds ordered west, south, east, north")
    if start.utcoffset() is None or end.utcoffset() is None:
        raise ValueError("Expected timezone-aware start and end")
    start, end = start.astimezone(UTC), end.astimezone(UTC)
    if start >= end:
        raise ValueError("Start must precede end")

    # Plan source discovery and the three spatial feature queries.
    terrain = query_url(
        "https://tnmaccess.nationalmap.gov/api/v1/products",
        datasets="Digital Elevation Model (DEM) 1 meter",
        bbox=",".join(map(str, bounds)),
        max=100,
    )
    latitude, longitude = (south + north) / 2, (west + east) / 2
    resources = [
        Resource(TERRAIN, terrain, bounds, start, end),
        Resource(
            WEATHER,
            f"https://api.weather.gov/points/{latitude:.4f},{longitude:.4f}",
            bounds,
            start,
            end,
        ),
    ]
    layers = {
        BUILDINGS: "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/"
        "USA_Structures_View/FeatureServer/0",
        SPECIAL_USE: "https://services6.arcgis.com/ssFJjBXIUyZDrSYZ/arcgis/rest/services/"
        "Special_Use_Airspace/FeatureServer/0",
        FACILITY_MAP: "https://services6.arcgis.com/ssFJjBXIUyZDrSYZ/arcgis/rest/services/"
        "FAA_UAS_FacilityMap_Data/FeatureServer/0",
    }
    for source, layer in layers.items():
        url = query_url(
            f"{layer}/query",
            f="geojson",
            where="1=1",
            geometry=",".join(map(str, bounds)),
            geometryType="esriGeometryEnvelope",
            spatialRel="esriSpatialRelIntersects",
            inSR=4326,
            outSR=4326,
            returnZ="false",
            outFields="*",
            orderByFields="OBJECTID",
            resultRecordCount=500,
        )
        resources.append(Resource(source, url, bounds, start, end))

    # Request each NASR edition whose effective interval overlaps the request.
    cycle = NASR_REFERENCE + ((start - NASR_REFERENCE) // NASR_CYCLE) * NASR_CYCLE
    while cycle < end:
        version = cycle.date().isoformat()
        url = f"https://nfdc.faa.gov/webContent/28DaySub/{version}/class_airspace_shape_files.zip"
        resources.append(Resource(NASR, url, bounds, cycle, cycle + NASR_CYCLE, version))
        cycle += NASR_CYCLE
    return resources
