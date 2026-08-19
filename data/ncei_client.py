"""Small client for NOAA NCEI's public Access Data Service."""

from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://www.ncei.noaa.gov/access/services/data/v1"


class NCEIError(RuntimeError):
    """Raised when NCEI cannot return usable data."""


async def fetch_daily_summaries(
    station: str,
    start_date: str,
    end_date: str,
    data_types: str = "TAVG,PRCP",
) -> list[dict[str, Any]]:
    """Fetch daily-summary observations as JSON from NCEI."""
    if not station.strip():
        raise ValueError("station must not be empty")
    if not start_date or not end_date:
        raise ValueError("start_date and end_date are required")
    if not data_types.strip():
        raise ValueError("data_types must not be empty")

    params = {
        "dataset": "daily-summaries",
        "stations": station.strip(),
        "startDate": start_date,
        "endDate": end_date,
        "dataTypes": data_types,
        "format": "json",
        "units": "metric",
        "includeStationName": "true",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise NCEIError(f"NCEI data request failed: {exc}") from exc

    if not isinstance(payload, list):
        raise NCEIError("NCEI returned an unexpected data shape")
    return payload


def normalize_daily_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize NCEI records to fields consumed by the analysis layer."""
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or "DATE" not in record:
            continue
        normalized.append(
            {
                "date": record["DATE"],
                "station": record.get("STATION"),
                "station_name": record.get("NAME"),
                "temperature_avg": record.get("TAVG"),
                "precipitation": record.get("PRCP"),
            }
        )
    return normalized
