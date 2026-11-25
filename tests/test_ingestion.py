"""Regression coverage for NWS pagination during batch acquisition."""

import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

from horizon.ingestion import acquire
from horizon.ingestion.plan import WEATHER, plan


def test_nws_pagination_stops_at_empty_pages_and_keeps_time_bounds(monkeypatch, tmp_path):
    # Model the NWS station endpoint's empty page with a continuation link.
    start = datetime(2026, 11, 24, tzinfo=UTC)
    bounds = (-77.1, 38.8, -77.0, 38.9)
    resource = next(
        item for item in plan(bounds, start, start + timedelta(hours=1)) if item.source == WEATHER
    )
    stations_url = "https://api.weather.gov/gridpoints/LWX/96,69/stations"
    empty_url = "https://api.weather.gov/stations?cursor=empty"
    station = {
        "geometry": {"type": "Point", "coordinates": [-77.05, 38.85]},
        "properties": {"stationIdentifier": "KDCA"},
    }

    def response(request, *, timeout):
        # Reject any request that follows the spurious link past the empty page.
        url = request.full_url
        if url == resource.url:
            payload = {"properties": {"observationStations": stations_url}}
        elif url == stations_url:
            payload = {"features": [station], "pagination": {"next": empty_url}}
        elif url == empty_url:
            payload = {"features": [], "pagination": {"next": f"{empty_url}2"}}
        else:
            assert url.startswith("https://api.weather.gov/stations/KDCA/observations?")
            parameters = parse_qs(urlsplit(url).query)
            assert parameters["start"] == [resource.start.isoformat()]
            assert parameters["end"] == [resource.end.isoformat()]
            payload = (
                {"features": []}
                if "cursor" in parameters
                else {
                    "features": [station],
                    "pagination": {
                        "next": "https://api.weather.gov/stations/KDCA/observations?cursor=next"
                    },
                }
            )
        return BytesIO(json.dumps(payload).encode())

    # Check that both raw station responses and the requested observations were landed.
    monkeypatch.setattr(acquire, "urlopen", response)
    result = acquire.acquire(resource, tmp_path)
    assert set(result.files) == {
        "point.json",
        "stations-0.json",
        "stations-1.json",
        "observations-0-0.json",
        "observations-0-1.json",
    }
    assert (result.directory / "manifest.json").is_file()
