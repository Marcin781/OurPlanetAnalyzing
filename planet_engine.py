from __future__ import annotations

import asyncio
import csv
import io
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

import httpx

TIMEOUT = 20

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

async def get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

async def get_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": "Dziennik-Planety/4.0"}) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

async def usgs_earthquakes() -> dict[str, Any]:
    data = await get_json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
    events = []
    for feature in data.get("features", []):
        p = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates") or [None, None, None]
        lon = coords[0] if len(coords) > 0 else None
        lat = coords[1] if len(coords) > 1 else None
        depth = coords[2] if len(coords) > 2 else None
        events.append({"id": feature.get("id"), "place": p.get("place"), "magnitude": p.get("mag"), "time": p.get("time"), "depth_km": depth, "latitude": lat, "longitude": lon, "geometry": {"type": "Point", "coordinates": [lon, lat]} if lat is not None and lon is not None else None, "url": p.get("url")})
    return {"source": "USGS", "status": "ok", "updated": utc_now(), "events": events}

async def noaa_co2() -> dict[str, Any]:
    text = await get_text("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv")
    rows = []
    for row in csv.reader(io.StringIO(text)):
        if not row or row[0].strip().startswith("#") or row[0].strip().lower() == "year": continue
        try: rows.append({"year": int(row[0]), "month": int(row[1]), "co2": float(row[3])})
        except (ValueError, IndexError): continue
    if not rows: raise RuntimeError("NOAA CO2 returned no usable rows")
    latest = rows[-1]
    previous_year = next((r for r in reversed(rows[:-1]) if r["year"] == latest["year"] - 1 and r["month"] == latest["month"]), None)
    return {"source": "NOAA GML / Mauna Loa", "status": "ok", "unit": "ppm", "rows": rows[-120:], "latest": latest, "year_over_year": round(latest["co2"] - previous_year["co2"], 2) if previous_year else None}

async def nasa_global_temperature() -> dict[str, Any]:
    text = None; last_error = None
    for url in ["https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt", "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"]:
        try:
            candidate = await get_text(url)
            if candidate and "Land-Ocean: Global Means" in candidate: text = candidate; break
        except Exception as exc: last_error = exc
    if not text: raise RuntimeError(f"NASA GISTEMP unavailable: {last_error}")
    rows = []
    for row in csv.reader(io.StringIO(text)):
        if not row or not row[0].strip().isdigit(): continue
        try:
            year = int(row[0].strip()); months = [None if v.strip() in ("", "***") else float(v.strip()) for v in row[1:13]]
            annual = None if len(row) <= 13 or row[13].strip() in ("", "***") else float(row[13].strip())
            rows.append({"year": year, "annual_anomaly_c": annual, "months": months})
        except (ValueError, IndexError): continue
    if not rows: raise RuntimeError("NASA GISTEMP returned no parseable records")
    return {"source": "NASA GISS", "status": "ok", "unit": "°C anomaly", "base_period": "1951-1980", "rows": rows[-10:], "latest": rows[-1]}

async def copernicus_climate_pulse() -> dict[str, Any]:
    text = await get_text("https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv")
    rows = []
    for row in csv.reader(io.StringIO(text)):
        if not row or row[0].lower().startswith("date") or row[0].startswith("#"): continue
        try:
            date = row[0].strip(); values = [float(v) for v in row[1:] if v.strip() not in ("", "nan", "NaN")]
            if values: rows.append({"date": date, "value": values[0], "raw": values})
        except (ValueError, IndexError): continue
    if not rows: raise RuntimeError("Copernicus Climate Pulse returned no parseable rows")
    return {"source": "Copernicus C3S / ECMWF Climate Pulse", "status": "ok", "unit": "°C", "baseline": "1991-2020", "updated": utc_now(), "latest": rows[-1], "rows": rows[-365:]}

async def legnica_weather() -> dict[str, Any]:
    lat, lon = 51.207, 16.161
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,precipitation,rain", "hourly": "temperature_2m,relative_humidity_2m,precipitation", "past_days": 30, "forecast_days": 7, "timezone": "Europe/Warsaw"}
    data = await get_json("https://api.open-meteo.com/v1/forecast", params)
    soil_data = None
    try:
        soil_params = dict(params); soil_params["hourly"] = "soil_moisture_0_to_7cm"
        soil_data = await get_json("https://api.open-meteo.com/v1/forecast", soil_params)
    except Exception: pass
    h = data.get("hourly", {}); temps, rain, humidity = h.get("temperature_2m", []), h.get("precipitation", []), h.get("relative_humidity_2m", [])
    soil = (soil_data or {}).get("hourly", {}).get("soil_moisture_0_to_7cm", [])
    def window(values, n): return [float(v) for v in values[-n:] if v is not None]
    rain7, rain14 = window(rain, 168), window(rain, 336); temp7, hum7, soil7 = window(temps, 168), window(humidity, 168), window(soil, 168)
    rain7_total, rain14_total = sum(rain7), sum(rain14); avg_temp, avg_hum, avg_soil = (mean(temp7) if temp7 else None), (mean(hum7) if hum7 else None), (mean(soil7) if soil7 else None)
    score = min(40, rain7_total * 2)
    if avg_temp is not None and 10 <= avg_temp <= 24: score += 30
    if avg_hum is not None: score += min(20, max(0, (avg_hum - 60) * 0.5))
    if avg_soil is not None: score += min(10, max(0, avg_soil * 50))
    return {"source": "Open-Meteo", "status": "ok", "location": {"name": "Legnica", "lat": lat, "lon": lon}, "current": data.get("current"), "history": {"rain_7d_mm": round(rain7_total, 1), "rain_14d_mm": round(rain14_total, 1), "avg_temp_7d_c": round(avg_temp, 1) if avg_temp is not None else None, "avg_humidity_7d_pct": round(avg_hum, 1) if avg_hum is not None else None, "avg_soil_moisture": round(avg_soil, 3) if avg_soil is not None else None}, "forecast": {"times": data.get("hourly", {}).get("time", [])[-168:], "rain_mm": data.get("hourly", {}).get("precipitation", [])[-168:]}, "mushroom_score": round(max(0, min(100, score))), "mushroom_method": "Heurystyka: opad + temperatura + wilgotność + opcjonalna wilgotność gleby. Nie jest prognozą biologiczną."}

async def cneos_close_approaches() -> dict[str, Any]:
    today = datetime.now(timezone.utc).date(); end = today + timedelta(days=7)
    data = await get_json("https://ssd-api.jpl.nasa.gov/cad.api", {"date-min": today.isoformat(), "date-max": end.isoformat(), "dist-max": "0.05", "sort": "date", "body": "ALL"})
    fields = data.get("fields", [])
    return {"source": "NASA/JPL CNEOS", "status": "ok", "updated": utc_now(), "events": [dict(zip(fields, row)) for row in data.get("data", [])]}

async def nasa_eonet_events() -> dict[str, Any]:
    data = await get_json("https://eonet.gsfc.nasa.gov/api/v3/events", {"status": "open", "limit": 500})
    events = []
    for event in data.get("events", []):
        categories = [c.get("id") for c in event.get("categories", [])]
        if any(c in {"wildfires", "volcanoes", "severeStorms", "seaLakeIce"} for c in categories):
            geo = event.get("geometry") or []; latest = geo[-1] if geo else {}
            events.append({"id": event.get("id"), "title": event.get("title"), "categories": categories, "date": latest.get("date"), "geometry": latest.get("coordinates")})
    counts = {}
    for e in events:
        for c in e["categories"]: counts[c] = counts.get(c, 0) + 1
    return {"source": "NASA EONET", "status": "ok", "updated": utc_now(), "counts": counts, "events": events[:300]}

async def noaa_space_weather() -> dict[str, Any]:
    kp = await get_json("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json")
    solar = await get_json("https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle.json")
    return {"source": "NOAA SWPC", "status": "ok", "updated": utc_now(), "latest_kp": kp[-1] if isinstance(kp, list) and kp else None, "latest_solar_cycle": solar[-1] if isinstance(solar, list) and solar else None, "classification": "Kp >= 5 oznacza burzę geomagnetyczną; interpretacja wymaga kontekstu prognozy SWPC."}

async def gbif_biodiversity() -> dict[str, Any]:
    data = await get_json("https://api.gbif.org/v1/occurrence/search", {"country": "PL", "limit": 0})
    current = await get_json("https://api.gbif.org/v1/occurrence/search", {"country": "PL", "limit": 0, "year": str(datetime.now(timezone.utc).year)})
    return {"source": "GBIF", "status": "ok", "updated": utc_now(), "poland_occurrences_total": int(data.get("count", 0)), "poland_occurrences_current_year": int(current.get("count", 0)), "note": "Liczba rekordów obserwacyjnych nie jest bezpośrednią miarą liczebności populacji ani trendu bioróżnorodności."}

async def noaa_ocean_indicator() -> dict[str, Any]:
    text = await get_text("https://psl.noaa.gov/data/correlation/amon.us.data")
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 14 and parts[0].isdigit():
            try: rows.append({"year": int(parts[0]), "months": [float(x) for x in parts[1:13]]})
            except ValueError: pass
    if not rows: raise RuntimeError("NOAA ocean indicator returned no usable rows")
    return {"source": "NOAA PSL", "status": "ok", "indicator": "AMO", "rows": rows[-10:], "note": "AMO jest wskaźnikiem oceanicznym, a nie globalną temperaturą oceanów."}

async def nsidc_ice() -> dict[str, Any]:
    urls = {"north": "https://noaadata.apps.nsidc.org/NOAA/G02135/north/daily/data/N_seaice_extent_daily_v4.0.csv", "south": "https://noaadata.apps.nsidc.org/NOAA/G02135/south/daily/data/S_seaice_extent_daily_v4.0.csv"}
    out = {}
    for hemisphere, url in urls.items():
        text = await get_text(url); rows = []
        for row in csv.reader(io.StringIO(text)):
            if not row or not row[0].strip().isdigit(): continue
            try: rows.append({"year": int(row[0]), "month": int(row[1]), "day": int(row[2]), "extent_million_km2": float(row[3])})
            except (ValueError, IndexError): continue
        if rows: out[hemisphere] = {"latest": rows[-1], "rows": rows[-365:]}
    if not out: raise RuntimeError("NSIDC Sea Ice Index returned no usable data")
    return {"source": "NSIDC / NOAA Sea Ice Index v4", "status": "ok", "updated": utc_now(), "unit": "million km²", "data": out, "baseline": "1981-2010 climatology available from NSIDC"}

async def source_status() -> dict[str, Any]:
    jobs = [("temperature", nasa_global_temperature), ("copernicus", copernicus_climate_pulse), ("co2", noaa_co2), ("earthquakes", usgs_earthquakes), ("legnica", legnica_weather), ("neo", cneos_close_approaches), ("fires_volcanoes", nasa_eonet_events), ("space_weather", noaa_space_weather), ("biodiversity", gbif_biodiversity), ("ocean_indicator", noaa_ocean_indicator), ("ice", nsidc_ice)]
    async def run(name: str, fn):
        try: return name, await fn()
        except Exception as exc: return name, {"source": name, "status": "error", "error_type": type(exc).__name__, "error": str(exc), "updated": utc_now()}
    return dict(await asyncio.gather(*(run(name, fn) for name, fn in jobs)))
