from planet_journal import build_planet_journal, render_weekly_journal_markdown


def _analysis():
    return {
        "provider": "NASA POWER",
        "period": {"start": "2019", "end": "2025"},
        "method": "one representative point per region",
        "retrieved_at": "2026-09-21T00:00:00+00:00",
        "points": {
            "A": {
                "mean": 10.0,
                "trend": {"direction": "wzrost"},
                "source_url": "https://example.test/a",
                "data_quality": {"quality": "complete"},
                "anomalies": [{"date": "2025-07", "value": 13.0, "deviation": 2.1}],
            },
            "B": {
                "mean": 9.0,
                "trend": {"direction": "spadek"},
                "source_url": "https://example.test/b",
                "data_quality": {"quality": "partial"},
            },
            "C": {"error": "upstream unavailable"},
        },
    }


def test_journal_preserves_provenance_and_coverage():
    result = build_planet_journal(_analysis())
    assert result["provider"] == "NASA POWER"
    assert result["coverage"] == {
        "valid_points": 2,
        "total_points": 3,
        "complete_points": 1,
        "partial_points": 1,
    }
    assert result["source_urls"] == [
        "https://example.test/a",
        "https://example.test/b",
    ]
    assert result["period"]["start"] == "2019"
    assert result["period"]["end"] == "2025"


def test_journal_does_not_turn_trend_into_forecast():
    result = build_planet_journal(_analysis())
    assert any("prognozą" in item for item in result["limitations"])
    assert any("Wzrost" in item for item in result["observations"])
    assert any("Spadek" in item for item in result["observations"])


def test_journal_handles_no_valid_points():
    result = build_planet_journal({
        "provider": "NASA POWER",
        "points": {"A": {"error": "timeout"}},
    })
    assert result["coverage"]["valid_points"] == 0
    assert result["source_urls"] == []


def test_journal_exposes_anomaly_signals():
    result = build_planet_journal(_analysis())
    assert result["anomalies"]["count"] == 1
    assert result["anomalies"]["items"][0]["point"] == "A"
    assert any("odchyleń" in item for item in result["observations"])


def test_weekly_markdown_contains_provenance_and_limitations():
    journal = build_planet_journal(_analysis())
    markdown = render_weekly_journal_markdown(journal)
    assert "# Dziennik Planety" in markdown
    assert "NASA POWER" in markdown
    assert "Metoda i ograniczenia" in markdown
    assert "https://example.test/a" in markdown
