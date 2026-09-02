from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from history_service import period_comparison
from planet_db import connection

METRICS = (
    "global_temperature_anomaly",
    "global_temperature_daily",
    "co2_mauna_loa",
    "legnica_temperature",
    "legnica_mushroom_score",
)


def generate_weekly_report(week_start: date | None = None) -> dict:
    start = week_start or (datetime.now(timezone.utc).date() - timedelta(days=datetime.now(timezone.utc).weekday()))
    report = {"week_start": start.isoformat(), "generated_at": datetime.now(timezone.utc).isoformat(), "metrics": {}}
    for metric in METRICS:
        report["metrics"][metric] = period_comparison(metric, 7)
    return report


def save_weekly_report(report: dict) -> None:
    with connection() as conn:
        conn.execute(
            """INSERT INTO weekly_reports(week_start, generated_at, report)
               VALUES (%s,%s,%s)
               ON CONFLICT (week_start) DO UPDATE SET generated_at=EXCLUDED.generated_at, report=EXCLUDED.report""",
            (report["week_start"], datetime.now(timezone.utc), report),
        )
        conn.commit()


def latest_weekly_report() -> dict | None:
    with connection() as conn:
        row = conn.execute("SELECT report FROM weekly_reports ORDER BY week_start DESC LIMIT 1").fetchone()
    return dict(row["report"]) if row else None
