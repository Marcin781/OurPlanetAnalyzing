from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
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
        events.append({"id": feature.get("id"), "place": p.get("place"), "magnitude": p.get("mag"), "time": p.get("time"), "depth_km": (feature.get("geometry", {}).get("coordinates") or [None, None, None])[2], "url": p.get("url")})
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
    latest = rows[-1] if rows else None
    previous_year = None
    if latest:
        previous_year = next((r for r in reversed(rows[:-1]) if r[0] == latest["year"] - 1 and r[1] == latest["month"]), None)
    return {"source": "NOAA GML / Mauna Loa", "status": "ok", "unit": "ppm", "rows": rows[-120:], "latest": latest, "year_over_year": round(latest["co2"] - previous_year["co2"], 2) if latest and previous_year else None}


async def nasa_global_temperature() -> dict[str, Any]:
    text = await get_text("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv")
    rows = []
    reader = csv.reader(io.StringIO(text))
    next(reader, None)
    for row in reader:
        if len(row) < 14 or not row[0].isdigit():
            continue
        try:
            vals = [float(v) for v in row[1:13] if v.strip() not in ("", "***")]
            if vals:
                rows.append({"year": int(row[0]), "annual_anomaly_c": float(row[13]) if row[13].strip() not in ("", "***") else None, "months": vals})
        except ValueError:
            continue
    return {"source": "NASA GISS", "status": "ok", "unit": "°C anomaly", "rows": rows[-10:], "latest": rows[-1] if rows else None}


async def legnica_weather() -> dict[str, Any]:
    lat, lon = 51.207, 16.161
    data = await get_json("https://api.open-meteo.com/v1/forecast", {"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,precipitation,rain,soil_moisture_0_to_7cm", "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_moisture_0_to_7cm", "past_days": 30, "forecast_days": 7, "timezone": "Europe/Warsaw"})
    h = data.get("hourly", {})
    temps, rain, humidity, soil = h.get("temperature_2m", []), h.get("precipitation", []), h.get("relative_humidity_2m", []), h.get("soil_moisture_0_to_7cm", [])

    def window(values, n):
        return [float(v) for v in values[-n:] if v is not None]

    rain7, rain14 = window(rain, 168), window(rain, 336)
    temp7, hum7, soil7 = window(temps, 168), window(humidity, 168), window(soil, 168)
    rain7_total, rain14_total = sum(rain7), sum(rain14)
    avg_temp, avg_hum, avg_soil = (mean(temp7) if temp7 else None), (mean(hum7) if hum7 else None), (mean(soil7) if soil7 else None)
    score = min(40, rain7_total * 2)
    if avg_temp is not None and 10 <= avg_temp <= 24: score += 30
    if avg_hum is not None: score += min(20, max(0, (avg_hum - 60) * 0.5))
    if avg_soil is not None: score += min(10, max(0, avg_soil * 50))
    return {"source": "Open-Meteo", "status": "ok", "location": {"name": "Legnica", "lat": lat, "lon": lon}, "current": data.get("current"), "history": {"rain_7d_mm": round(rain7_total, 1), "rain_14d_mm": round(rain14_total, 1), "avg_temp_7d_c": round(avg_temp, 1) if avg_temp is not None else None, "avg_humidity_7d_pct": round(avg_hum, 1) if avg_hum is not None else None, "avg_soil_moisture": round(avg_soil, 3) if avg_soil is not None else None}, "forecast": {"times": data.get("hourly", {}).get("time", [])[-168:], "rain_mm": data.get("hourly", {}).get("precipitation", [])[-168:]}, "mushroom_score": round(max(0, min(100, score))), "mushroom_method": "Heurystyka: opad + temperatura + wilgotność + wilgotność gleby. Nie jest prognozą biologiczną."}


async def cneos_close_approaches() -> dict[str, Any]:
    today = datetime.now(timezone.utc).date()
    end = today + timedelta(days=7)
    data = await get_json("https://ssd-api.jpl.nasa.gov/cad.api", {"date-min": today.isoformat(), "date-max": end.isoformat(), "dist-max": "0.05", "sort": "date", "body": "ALL"})
    fields = data.get("fields", [])
    return {"source": "NASA/JPL CNEOS", "status": "ok", "updated": datetime.now(timezone.utc).isoformat(), "events": [dict(zip(fields, row)) for row in data.get("data", [])]}


async def source_status() -> dict[str, Any]:
    # Sequential on purpose: CNEOS asks clients not to issue simultaneous requests.
    jobs = [("temperature", nasa_global_temperature), ("co2", noaa_co2), ("earthquakes", usgs_earthquakes), ("legnica", legnica_weather), ("neo", cneos_close_approaches)]
    results = {}
    for name, fn in jobs:
        try:
            results[name] = await fn()
        except Exception as exc:
            results[name] = {"source": name, "status": "error", "error": str(exc)}
    return results
