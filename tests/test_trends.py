from analysis.trends import build_signal_summary, compare_periods, detect_anomalies, summarize


def test_summarize_detects_rising_trend():
    records = [
        {"date": "2026-01-01", "temperature_avg": 10.0},
        {"date": "2026-01-02", "temperature_avg": 11.0},
        {"date": "2026-01-03", "temperature_avg": 12.0},
    ]
    result = summarize(records)
    assert result["count"] == 3
    assert result["trend"] == "wzrost"
    assert result["delta"] == 2.0


def test_detect_anomalies_uses_explicit_threshold():
    records = [
        {"date": "2026-01-01", "temperature_avg": 10.0},
        {"date": "2026-01-02", "temperature_avg": 10.0},
        {"date": "2026-01-03", "temperature_avg": 13.0},
    ]
    anomalies = detect_anomalies(records, threshold=2.0)
    assert len(anomalies) == 1
    assert anomalies[0]["date"] == "2026-01-03"


def test_empty_data_is_safe():
    result = summarize([])
    assert result["count"] == 0
    assert result["trend"] == "brak danych"
    assert detect_anomalies([]) == []


def test_compare_periods_reports_change():
    result = compare_periods(
        [{"temperature_avg": 12.0}, {"temperature_avg": 14.0}],
        [{"temperature_avg": 10.0}, {"temperature_avg": 11.0}],
    )
    assert result["current_mean"] == 13.0
    assert result["previous_mean"] == 10.5
    assert result["change"] == 2.5
    assert result["direction"] == "wzrost"


def test_signal_summary_is_explainable():
    result = build_signal_summary(
        [
            {"date": "2026-01", "temperature_avg": 10.0},
            {"date": "2026-02", "temperature_avg": 10.0},
            {"date": "2026-03", "temperature_avg": 13.0},
        ],
        anomaly_threshold=2.0,
    )
    assert result["anomaly_count"] == 1
    assert result["anomalies"][0]["date"] == "2026-03"
