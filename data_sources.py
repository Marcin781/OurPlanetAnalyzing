from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx


NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
MAX_CONCURRENT_REQUESTS = 5


class DataSourceError(RuntimeError):
    pass


async def fetch_nasa_power_temperature(
    latitude: float,
    longitude: float,
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    """Fetch monthly 2-m air temperature from NASA POWER public API."""
    params = {
        "parameters": "T2M",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_year,
        "end": end_year,
        "format": "JSON",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(NASA_POWER_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DataSourceError(f"NASA POWER request failed: {exc}") from exc

    properties = payload.get("properties", {})
    parameter = properties.get("parameter", {})
    temperature = parameter.get("T2M", {})

    return {
        "provider": "NASA POWER",
        "parameter": "T2M",
        "unit": "degC",
        "location": {"latitude": latitude, "longitude": longitude},
        "period": {"start": start_year, "end": end_year},
        "data": temperature,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": str(response.url),
    }


async def fetch_nasa_power_temperature_points(
    points: dict[str, dict[str, Any]],
    start_year: int,
    end_year: int,
) -> dict[str, Any]:
    """Fetch the same temperature series for multiple named representative points.

    Requests are performed concurrently with a small semaphore limit so regional
    analyses are faster without creating an uncontrolled burst of API traffic.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def fetch_one(key: str, point: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        async with semaphore:
            try:
                result = await fetch_nasa_power_temperature(
                    latitude=float(point["latitude"]),
                    longitude=float(point["longitude"]),
                    start_year=start_year,
                    end_year=end_year,
                )
                return key, result
            except (DataSourceError, KeyError, TypeError, ValueError) as exc:
                return key, {"error": str(exc), "location": point}

    pairs = await asyncio.gather(*(fetch_one(key, point) for key, point in points.items()))
    results = dict(pairs)

    return {
        "provider": "NASA POWER",
        "period": {"start": start_year, "end": end_year},
        "points": results,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
