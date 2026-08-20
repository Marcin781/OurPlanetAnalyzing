from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx


NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"


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
