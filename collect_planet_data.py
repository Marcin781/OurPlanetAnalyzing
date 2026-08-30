from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from planet_db import init_db, insert_observation
from planet_engine import cneos_close_approaches, legnica_weather, nasa_global_temperature, noaa_co2, usgs_earthquakes


def collect_temperature(data):
    latest = data.get("latest") or {}
    if latest.get("annual_anomaly_c") is not None:
        insert_observation("NASA GISS", "global_temperature_annual_anomaly", datetime(int(latest["year"]), 12, 31, tzinfo=timezone.utc), latest["annual_anomaly_c"], "°C")


def collect_co2(data):
    for row in data.get("rows", []):
        insert_observation("NOAA GML", "co2_mauna_loa", datetime(row["year"], row["month"], 1, tzinfo=timezone.utc), row["co2"], "ppm")


def collect_legnica(data):
    now = datetime.now(timezone.utc)
    h = data.get("history", {})
    metrics = {
        "legnica_rain_7d": (h.get("rain_7d_mm"), "mm"),
        "legnica_rain_14d": (h.get("rain_14d_mm"), "mm"),
        "legnica_avg_temperature_7d": (h.get("avg_temp_7d_c"), "°C"),
        "legnica_avg_humidity_7d": (h.get("avg_humidity_7d_pct"), "%"),
        "legnica_avg_soil_moisture": (h.get("avg_soil_moisture"), "m³/m³"),
        "legnica_mushroom_score": (data.get("mushroom_score"), "score"),
    }
    for metric, (value, unit) in metrics.items():
        if value is not None:
            insert_observation("Open-Meteo", metric, now, value, unit)


def collect_earthquakes(data):
    for event in data.get("events", []):
        if event.get("magnitude") is not None and event.get("time"):
            observed = datetime.fromtimestamp(event["time"] / 1000, tz=timezone.utc)
            insert_observation("USGS", "earthquake_magnitude", observed, event["magnitude"], "M", metadata={"id": event.get("id"), "place": event.get("place"), "depth_km": event.get("depth_km")})


def collect_neo(data):
    now = datetime.now(timezone.utc)
    insert_observation("NASA/JPL CNEOS", "neo_close_approaches_7d", now, len(data.get("events", [])), "events")


async def main():
    init_db()
    temperature, co2, quakes, legnica, neo = await asyncio.gather(
        nasa_global_temperature(), noaa_co2(), usgs_earthquakes(), legnica_weather(), cneos_close_approaches()
    )
    collect_temperature(temperature)
    collect_co2(co2)
    collect_earthquakes(quakes)
    collect_legnica(legnica)
    collect_neo(neo)
    print("Planet Diary collector: collection completed")


if __name__ == "__main__":
    asyncio.run(main())
