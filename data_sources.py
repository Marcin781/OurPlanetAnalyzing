from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx


NCEI_CDO_BASE = "https://www.ncei.noaa.gov/cdo-web/api/v2"


class DataSourceError(RuntimeError):
    pass


async def fetch_ncei_datasets(limit: int = 10) -> dict[str, Any]:
    """Fetch public NOAA/NCEI dataset metadata without requiring an API key."""
    url = f"{NCEI_CDO_BASE}/datasets"
    params = {"limit": limit, "sortfield": "name", "sortorder": "asc"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise DataSourceError(f"NCEI request failed: {exc}") from exc

    return {
        "provider": "NOAA National Centers for Environmental Information",
        "endpoint": str(response.url),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "count": payload.get("count", 0),
        "results": payload.get("results", []),
    }
