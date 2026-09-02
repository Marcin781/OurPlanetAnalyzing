from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from planet_db import init_db, insert_observation
from planet_engine import source_status


def _dt(value):
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value / 1000 if value > 10_000_000_000 else value, tz=timezone.utc)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
    else:
        return datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def collect(data: dict) -> int:
    saved = 0
    t = data.get("temperature", {}).get("latest", {})
    if t.get("annual_anomaly_c") is not None:
        insert_observation("NASA GISS", "global_temperature_anomaly", datetime(int(t["year"]), 12, 31, tzinfo=timezone.utc), t["annual_anomaly_c"], "°C", metadata={"base_period": "1951-1980"})
        saved += 1
    cp = data.get("copernicus", {}).get("latest", {})
    if cp.get("value") is not None:
        insert_observation("Copernicus C3S", "global_temperature_daily", _dt(cp.get("date")), cp["value"], "°C", metadata={"baseline": "1991-2020"})
        saved += 1
    co2 = data.get("co2", {}).get("latest", {})
    if co2.get("co2") is not None:
        insert_observation("NOAA GML", "co2_mauna_loa", datetime(int(co2["year"]), int(co2["month"]), 1, tzinfo=timezone.utc), co2["co2"], "ppm")
        saved += 1
    lg = data.get("legnica", {})
    current = lg.get("current") or {}
    if current.get("temperature_2m") is not None:
        insert_observation("Open-Meteo", "legnica_temperature", _dt(current.get("time")), current["temperature_2m"], "°C", metadata={"mushroom_score": lg.get("mushroom_score")})
        saved += 1
    if lg.get("mushroom_score") is not None:
        insert_observation("Dziennik Planety", "legnica_mushroom_score", datetime.now(timezone.utc), lg["mushroom_score"], "score/100", metadata={"method": lg.get("mushroom_method")})
        saved += 1
    return saved


async def main() -> None:
    init_db()
    data = await source_status()
    saved = collect(data)
    print(f"collector: saved {saved} observations")


if __name__ == "__main__":
    asyncio.run(main())
