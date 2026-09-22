from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx


NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
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
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
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



async def fetch_open_meteo_recent_weather(latitude: float, longitude: float, days: int = 7) -> dict[str, Any]:
    """Fetch recent daily weather used as an indicative mushroom-condition input."""
    from datetime import date, timedelta

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=max(1, days) - 1)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "timezone": "Europe/Warsaw",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPEN_METEO_ARCHIVE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DataSourceError(f"Open-Meteo archive request failed: {exc}") from exc

    return {
        "provider": "Open-Meteo Archive",
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "daily": payload.get("daily", {}),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": str(response.url),
    }

def calculate_mushroom_conditions(weather: dict[str, Any], recent: dict[str, Any] | None = None) -> dict[str, Any]:
    """Calculate a transparent 0-100 indicative score; it is not a mushroom forecast."""
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    recent_daily = (recent or {}).get("daily", {})
    humidity = current.get("relative_humidity_2m")
    future_rain = daily.get("precipitation_sum", []) or []
    past_rain = recent_daily.get("precipitation_sum", []) or []
    temps = daily.get("temperature_2m_max", []) or []

    components = []
    reasons = []

    if humidity is not None:
        h = float(humidity)
        components.append((max(0.0, 100.0 - abs(h - 80.0) * 2.5), 0.30))
        reasons.append(f"wilgotność bieżąca: {h:.0f}%")
    recent_rain = sum(float(x or 0) for x in past_rain)
    forecast_rain = sum(float(x or 0) for x in future_rain[:3])
    components.append((min(100.0, recent_rain * 5.0), 0.30))
    components.append((min(100.0, forecast_rain * 10.0), 0.15))
    reasons.append(f"opad ostatnich dni: {recent_rain:.1f} mm")
    reasons.append(f"prognoza opadu 3 dni: {forecast_rain:.1f} mm")

    if temps:
        suitable = sum(1 for x in temps if 8.0 <= float(x) <= 22.0)
        components.append((100.0 * suitable / len(temps), 0.25))
        reasons.append(f"dni z temperaturą maks. 8–22°C: {suitable}/{len(temps)}")

    total_weight = sum(weight for _, weight in components)
    score = round(sum(value * weight for value, weight in components) / total_weight) if total_weight else 0
    level = "sprzyjające" if score >= 70 else "umiarkowane" if score >= 45 else "słabe"
    return {
        "score": max(0, min(100, score)),
        "level": level,
        "reasons": reasons,
        "warning": "Wskaźnik orientacyjny; nie potwierdza występowania grzybów w lesie.",
    }


def calculate_mushroom_history(recent: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a simple daily condition history from archived weather observations."""
    daily = recent.get("daily", {})
    dates = daily.get("time", []) or []
    highs = daily.get("temperature_2m_max", []) or []
    rains = daily.get("precipitation_sum", []) or []
    humidity = daily.get("relative_humidity_2m_mean", []) or []
    history = []
    for i, day in enumerate(dates):
        temp = highs[i] if i < len(highs) else None
        rain = rains[i] if i < len(rains) else 0
        hum = humidity[i] if i < len(humidity) else None
        parts = []
        weights = []
        if temp is not None:
            t = float(temp)
            weights.append((100.0 if 8 <= t <= 22 else max(0.0, 100 - min(abs(t-8), abs(t-22))*8), 0.4))
        if hum is not None:
            h = float(hum)
            weights.append((max(0.0, 100 - abs(h-80)*2.5), 0.3))
        r = float(rain or 0)
        weights.append((min(100.0, r*10), 0.3))
        total = sum(w for _, w in weights)
        score = round(sum(v*w for v,w in weights)/total) if total else 0
        history.append({"date": day, "score": max(0,min(100,score)), "temperature_max": temp, "precipitation_mm": r, "humidity_mean": hum})
    return history
