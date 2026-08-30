from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from planet_db import init_db, insert_observation
from planet_engine import (
    cneos_close_approaches,
    legnica_weather,
    nasa_global_temperature,
    noaa_co2,
    usgs_earthquakes,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HISTORY = DATA / "history"


async def collect() -> dict:
    jobs = {
        "temperature": nasa_global_temperature,
        "co2": noaa_co2,
        "earthquakes": usgs_earthquakes,
        "legnica": legnica_weather,
        "neo": cneos_close_approaches,
    }
    result = {"collected_at": datetime.now(timezone.utc).isoformat(), "sources": {}}
    for name, fn in jobs.items():
        try:
            result["sources"][name] = await fn()
        except Exception as exc:
            result["sources"][name] = {"status": "error", "error": str(exc)}
    return result


def persist_summary(payload: dict) -> str:
    if not os.getenv("DATABASE_URL"):
        return "not_configured"
    try:
        init_db()
        now = datetime.now(timezone.utc)
        rows = []
        t = payload["sources"].get("temperature", {}).get("latest") or {}
        if t.get("annual_anomaly_c") is not None:
            rows.append(("NASA GISS", "global_temperature_annual_anomaly", now, t["annual_anomaly_c"], "°C", None, {"year": t.get("year")}))
        c = payload["sources"].get("co2", {}).get("latest") or {}
        if c.get("co2") is not None:
            rows.append(("NOAA GML", "co2_mauna_loa", now, c["co2"], "ppm", None, {"year": c.get("year"), "month": c.get("month")}))
        l = payload["sources"].get("legnica", {})
        h = l.get("history", {})
        if h.get("rain_7d_mm") is not None:
            rows.append(("Open-Meteo", "legnica_rain_7d", now, h["rain_7d_mm"], "mm", None, {}))
        if l.get("mushroom_score") is not None:
            rows.append(("Open-Meteo", "legnica_mushroom_score", now, l["mushroom_score"], "index", None, {}))
        q = payload["sources"].get("earthquakes", {})
        rows.append(("USGS", "earthquakes_24h_count", now, len(q.get("events", [])), "events", None, {}))
        n = payload["sources"].get("neo", {})
        rows.append(("NASA/JPL CNEOS", "neo_7d_count", now, len(n.get("events", [])), "objects", None, {}))
        for source, metric, observed_at, value, unit, anomaly, metadata in rows:
            insert_observation(source, metric, observed_at, value, unit, anomaly, metadata)
        return f"ok:{len(rows)}"
    except Exception as exc:
        return f"error:{exc}"


async def main() -> None:
    DATA.mkdir(exist_ok=True)
    HISTORY.mkdir(parents=True, exist_ok=True)
    payload = await collect()
    payload["database_persistence"] = persist_summary(payload)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (DATA / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (HISTORY / f"{stamp}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Collected weekly snapshot: {stamp}; DB={payload['database_persistence']}")


if __name__ == "__main__":
    asyncio.run(main())
