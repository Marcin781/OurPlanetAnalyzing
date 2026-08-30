from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

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


async def main() -> None:
    DATA.mkdir(exist_ok=True)
    HISTORY.mkdir(parents=True, exist_ok=True)
    payload = await collect()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (DATA / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (HISTORY / f"{stamp}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Collected weekly snapshot: {stamp}")


if __name__ == "__main__":
    asyncio.run(main())
