from __future__ import annotations

from datetime import datetime, timedelta, timezone

from planet_db import recent_observations


def history(metric: str, limit: int = 120) -> list[dict]:
    rows = recent_observations(metric, max(1, min(limit, 1000)))
    return [dict(row) for row in rows]


def period_comparison(metric: str, days: int = 7) -> dict:
    days = max(1, min(days, 3650))
    rows = history(metric, 1000)
    now = datetime.now(timezone.utc)
    current_cutoff = now - timedelta(days=days)
    previous_cutoff = now - timedelta(days=days * 2)

    current = [r for r in rows if _aware(r["observed_at"]) >= current_cutoff]
    previous = [r for r in rows if previous_cutoff <= _aware(r["observed_at"]) < current_cutoff]
    current_avg = _average(current)
    previous_avg = _average(previous)
    delta = None if current_avg is None or previous_avg is None else current_avg - previous_avg
    pct = None if delta is None or previous_avg in (None, 0) else delta / abs(previous_avg) * 100
    return {
        "metric": metric,
        "period_days": days,
        "current": {"count": len(current), "average": current_avg},
        "previous": {"count": len(previous), "average": previous_avg},
        "delta": delta,
        "delta_percent": pct,
    }


def _aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _average(rows):
    values = [float(r["value"]) for r in rows if r.get("value") is not None]
    return sum(values) / len(values) if values else None
