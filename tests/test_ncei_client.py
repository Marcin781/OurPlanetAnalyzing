import pytest

from data.ncei_client import NCEIError, normalize_daily_records


def test_normalize_daily_records_keeps_analysis_fields():
    records = normalize_daily_records([
        {"DATE": "2026-01-01", "STATION": "TEST", "NAME": "Test Station", "TAVG": "4.2", "PRCP": "1.5"},
        {"DATE": "2026-01-02", "STATION": "TEST", "TAVG": "5.0"},
    ])
    assert records[0]["date"] == "2026-01-01"
    assert records[0]["temperature_avg"] == "4.2"
    assert records[1]["station"] == "TEST"


def test_ncei_error_is_distinct():
    assert issubclass(NCEIError, RuntimeError)
