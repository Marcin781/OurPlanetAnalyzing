"""Client for NOAA NCEI's public dataset Search Service.

The client is intentionally limited to dataset discovery. It does not require
an API key and keeps network access isolated from the analysis layer.
"""

from __future__ import annotations

from typing import Any

import httpx

BASE_URL = "https://www.ncei.noaa.gov/access/services/search/v1/datasets"


class NCEIError(RuntimeError):
    """Raised when NCEI cannot return a usable response."""


async def search_datasets(keyword: str, limit: int = 10) -> dict[str, Any]:
    if not keyword.strip():
        raise ValueError("keyword must not be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    params = {"text": keyword.strip(), "limit": limit}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise NCEIError(f"NCEI request failed: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("results", []), list):
        raise NCEIError("NCEI returned an unexpected response shape")
    return payload
