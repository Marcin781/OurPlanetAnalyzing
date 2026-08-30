from __future__ import annotations

import asyncio
import csv
import io
from datetime import datetime, timezone
from statistics import mean
from typing import Any

import httpx

TIMEOUT = 20


async def get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def get_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def usgs_earthquakes() -> dict[str, Any]:
    data = await get_json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
    events = []
    for feature in data.get("features", []):
        p = feature.get("properties", {})
        events.append({
            "id": feature.get("id"),
            "place": p.get("place"),
            "magnitude": p.get("mag"),
            "time": p.get("time"),
            "depth_km": (feature.get("geometry", {}).get("coordinates") or [None, None, None])[2],
            "url": p.get("url"),
        })
    return {"source": "USGS", "status": "ok", "updated": datetime.now(timezone.utc).isoformat(), "events": events}


async def noaa_co2() -> dict[str, Any]:
    text = await get_text("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv")
    rows = []
    for row in csv.reader(io.StringIO(text)):
        if not row or row[0].startswith("#") or row[0] == "year":
            continue
        try:
            rows.append({"year": int(row[0]), "month": int(row[1]), "co2": float(row[4])})
        except (ValueError, IndexError):
            continue
    return {"source": "NOAA GML / Mauna Loa", "status": "ok", "unit": "ppm", "rows": rows[-120:]}


async def legnica_weather() -> dict[str, Any]:
    lat, lon = 51.207, 16.161
    data = await get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,soil_moisture_0_to_7cm",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_moisture_0_to_7cm",
            "past_days": 30,
            "forecast_days": 7,
            "timezone": "Europe/Warsaw",
        },
    )
    h = data.get("hourly", {})
    temps = h.get("temperature_2m", [])
    rain = h.get("precipitation", [])
    humidity = h.get("relative_humidity_2m", [])
    soil = h.get("soil_moisture_0_to_7cm", [])

    def window(values, n):
        return [float(v) for v in values[-n:] if v is not None]

    rain_7 = window(rain, 168)
    temp_7 = window(temps, 168)
    hum_7 = window(humidity, 168)
    soil_7 = window(soil, 168)
    rain_14 = window(rain, 336)

    rain7 = sum(rain_7)
    rain14 = sum(rain_14)
    avg_temp = mean(temp_7) if temp_7 else None
    avg_hum = mean(hum_7) if hum_7 else None
    avg_soil = mean(soil_7) if soil_7 else None

    score = 0
    score += min(40, rain7 * 2)
    if avg_temp is not None and 10 <= avg_temp <= 24:
        score += 30
    if avg_hum is not None:
        score += min(20, max(0, (avg_hum - 60) * 0.5))
    if avg_soil is not None:
        score += min(10, max(0, avg_soil * 50))
    score = round(max(0, min(100, score)))

    return {
        "source": "Open-Meteo",
        "status": "ok",
        "location": {"name": "Legnica", "lat": lat, "lon": lon},
        "current": data.get("current"),
        "history": {"rain_7d_mm": round(rain7, 1), "rain_14d_mm": round(rain14, 1), "avg_temp_7d_c": round(avg_temp, 1) if avg_temp is not None else None, "avg_humidity_7d_pct": round(avg_hum, 1) if avg_hum is not None else None, "avg_soil_moisture": round(avg_soil, 3) if avg_soil is not None else None},
        "forecast": {"times": data.get("hourly", {}).get("time", [])[-168:], "rain_mm": data.get("hourly", {}).get("precipitation", [])[-168:]},
        "mushroom_score": score,
        "mushroom_method": "Heurystyka: opad + temperatura + wilgotność + wilgotność gleby. Nie jest prognozą biologiczną.",
    }


async def cneos_close_approaches() -> dict[str, Any]:
    data = await get_json(
        "https://ssd-api.jpl.nasa.gov/cad.api",
        {"date-min": datetime.now(timezone.utc).date().isoformat(), "date-max": (datetime.now(timezone.utc).date()).isoformat(), "dist-max": "0.05", "sort": "date", "body": "ALL"},
    )
    fields = data.get("fields", [])
    rows = [dict(zip(fields, row)) for row in data.get("data", [])]
    return {"source": "NASA/JPL CNEOS", "status": "ok", "updated": datetime.now(timezone.utc).isoformat(), "events": rows}


async def source_status() -> dict[str, Any]:
    jobs = {
        "co2": noaa_co2(),
        "earthquakes": usgs_earthquakes(),
        "legnica": legnica_weather(),
        "neo": cneos_close_approaches(),
    }
    results = {}
    gathered = await asyncio.gather(*jobs.values(), return_exceptions=True)
    for name, result in zip(jobs, gathered):
        results[name] = result if not isinstance(result, Exception) else {"source": name, "status": "error", "error": str(result)}
    return results
