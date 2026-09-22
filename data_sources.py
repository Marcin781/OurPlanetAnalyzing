from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx


NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MAX_CONCURRENT_REQUESTS = 5
MISSING_VALUE = -999.0


class DataSourceError(RuntimeError):
    pass


def assess_monthly_completeness(data: dict[str, Any], start_year: int, end_year: int) -> dict[str, Any]:
    """Assess expected monthly observations without treating NASA missing sentinels as measurements."""
    expected = max(0, (end_year - start_year + 1) * 12)
    valid = 0
    missing = 0

    for value in data.values():
        if isinstance(value, (int, float)):
            if float(value) == MISSING_VALUE:
                missing += 1
            else:
                valid += 1

    observed = valid + missing
    missing += max(0, expected - observed)
    return {
        "expected_months": expected,
        "valid_months": valid,
        "missing_months": missing,
        "completeness_ratio": round(valid / expected, 3) if expected else None,
        "quality": "complete" if expected and valid == expected else "partial" if valid else "no_valid_data",
    }


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
    quality = assess_monthly_completeness(temperature, start_year, end_year)

    return {
        "provider": "NASA POWER",
        "parameter": "T2M",
        "unit": "degC",
        "location": {"latitude": latitude, "longitude": longitude},
        "period": {"start": start_year, "end": end_year},
        "data": temperature,
        "data_quality": quality,
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


async def fetch_open_meteo_forecast(latitude: float, longitude: float, forecast_days: int = 7) -> dict[str, Any]:
    """Fetch a compact current + daily weather forecast from Open-Meteo."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "Europe/Warsaw",
        "forecast_days": forecast_days,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DataSourceError(f"Open-Meteo request failed: {exc}") from exc

    return {
        "provider": "Open-Meteo",
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": payload.get("timezone"),
        "current": payload.get("current", {}),
        "daily": payload.get("daily", {}),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": str(response.url),
    }
