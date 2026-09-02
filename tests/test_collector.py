from collector import collect


def test_collect_without_database(monkeypatch):
    calls = []
    monkeypatch.setattr("collector.insert_observation", lambda *args, **kwargs: calls.append((args, kwargs)))
    data = {
        "temperature": {"latest": {"year": 2025, "annual_anomaly_c": 1.2}},
        "copernicus": {"latest": {"date": "2026-09-01", "value": 16.4}},
        "co2": {"latest": {"year": 2026, "month": 8, "co2": 425.1}},
        "legnica": {"current": {"time": "2026-09-01T12:00:00+02:00", "temperature_2m": 19.0}, "mushroom_score": 63, "mushroom_method": "test"},
    }
    assert collect(data) == 5
    assert len(calls) == 5


def test_collect_skips_missing_values(monkeypatch):
    calls = []
    monkeypatch.setattr("collector.insert_observation", lambda *args, **kwargs: calls.append(args))
    assert collect({}) == 0
    assert calls == []
