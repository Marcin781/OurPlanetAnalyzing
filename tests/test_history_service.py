from datetime import datetime, timezone

import history_service


def test_period_comparison_uses_two_periods(monkeypatch):
    now = datetime.now(timezone.utc)
    rows = [
        {"observed_at": now, "value": 12},
        {"observed_at": now.replace(day=max(1, now.day - 1)), "value": 10},
    ]
    monkeypatch.setattr(history_service, "history", lambda metric, limit: rows)
    result = history_service.period_comparison("demo", 7)
    assert result["current"]["count"] == 2
    assert result["current"]["average"] == 11
