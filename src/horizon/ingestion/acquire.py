"""Download provider responses unchanged into the local landing directory."""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.parse import parse_qsl, quote, urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from .plan import NASR, TERRAIN, WEATHER, Bounds, Resource, query_url


@dataclass(frozen=True)
class Acquisition:
    """A completed landing directory and the request that produced it."""

    resource: Resource
    directory: Path
    acquired_at: datetime
    files: dict[str, str]  # Local filename to original URL


def select_stations(features: list[dict], bounds: Bounds) -> list[dict]:
    """Use in-area stations or fall back to the first nearby NWS station."""

    # NWS orders the midpoint station list by proximity to the forecast grid.
    west, south, east, north = bounds
    nearby = []
    inside = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "Point" or len(coordinates) < 2:
            continue
        longitude, latitude = coordinates[:2]
        nearby.append(feature)
        if west <= longitude <= east and south <= latitude <= north:
            inside.append(feature)
    return inside or nearby[:1]


def acquire(
    resource: Resource, landing: Path = Path("data/landing"), *, user_agent: str = "Horizon/0.1"
) -> Acquisition:
    """Acquire one resource and publish its directory after all responses arrive."""

    # Stage downloads beside the final directory for an atomic rename.
    landing = landing.resolve()
    landing.mkdir(parents=True, exist_ok=True)
    destination = landing / uuid4().hex
    with TemporaryDirectory(dir=landing) as temporary:
        directory = Path(temporary)
        files: dict[str, str] = {}

        def fetch(url: str, name: str) -> Path:

            # Stream large binary assets directly to disk.
            path = directory / name
            request = Request(url, headers={"User-Agent": user_agent})
            with urlopen(request, timeout=60) as response, path.open("wb") as output:
                copyfileobj(response, output)
            files[name] = url
            return path

        def read_json(url: str, name: str) -> dict:

            # Keep the original JSON payload for replay and diagnostics.
            data = json.loads(fetch(url, name).read_bytes())
            if "error" in data:
                raise ValueError(f"{resource.source}: {data['error']}")
            return data

        # Follow the provider's discovery or pagination responses.
        if resource.source == TERRAIN:
            offset = 0
            while True:
                data = read_json(f"{resource.url}&offset={offset}", f"products-{offset}.json")
                items = data["items"]
                for index, item in enumerate(items, start=offset):
                    url = item["downloadURL"]
                    suffix = Path(urlsplit(url).path).suffix.lower()
                    if suffix not in {".tif", ".tiff", ".img"}:
                        raise ValueError(f"Unexpected 3DEP raster format: {url}")
                    fetch(url, f"terrain-{index}{suffix}")
                offset += len(items)
                if offset >= data["total"]:
                    break
                if not items:
                    raise ValueError("3DEP returned an incomplete product list")
        elif resource.source == WEATHER:
            point = read_json(resource.url, "point.json")
            url = point["properties"]["observationStations"]
            stations: list[dict] = []
            page = 0
            while url:
                data = read_json(url, f"stations-{page}.json")
                if not data["features"]:
                    break
                stations.extend(data["features"])
                next_url = (data.get("pagination") or {}).get("next")
                url = next_url if next_url != url else None
                page += 1
            station_ids = {
                station["properties"]["stationIdentifier"]
                for station in select_stations(stations, resource.bounds)
            }
            for index, station_id in enumerate(sorted(station_ids)):
                interval = {
                    "start": resource.start.isoformat(),
                    "end": resource.end.isoformat(),
                    "limit": 500,
                }
                url = query_url(
                    f"https://api.weather.gov/stations/{quote(station_id, safe='')}/observations",
                    **interval,
                )
                page = 0
                while url:
                    data = read_json(url, f"observations-{index}-{page}.json")
                    if not data["features"]:
                        break
                    next_url = (data.get("pagination") or {}).get("next")
                    if next_url:
                        # NWS continuation links omit the requested time window.
                        parts = urlsplit(next_url)
                        parameters = {**dict(parse_qsl(parts.query)), **interval}
                        next_url = parts._replace(query=urlencode(parameters)).geturl()
                    url = next_url if next_url != url else None
                    page += 1
        elif resource.source == NASR:
            fetch(resource.url, "airspace.zip")
        else:
            offset = 0
            while True:
                data = read_json(f"{resource.url}&resultOffset={offset}", f"features-{offset}.json")
                size = len(data["features"])
                more = data.get("exceededTransferLimit") or (data.get("properties") or {}).get(
                    "exceededTransferLimit"
                )
                if not more and size < 500:
                    break
                if not size:
                    raise ValueError(f"{resource.source}: empty page before end of results")
                offset += size

        # Publish the raw files together with their origin and requested coverage.
        acquired_at = datetime.now(UTC)
        manifest = {"resource": asdict(resource), "acquired_at": acquired_at, "files": files}
        (directory / "manifest.json").write_text(
            json.dumps(manifest, default=str, indent=2), encoding="utf-8"
        )
        directory.rename(destination)
    return Acquisition(resource, destination, acquired_at, files)
