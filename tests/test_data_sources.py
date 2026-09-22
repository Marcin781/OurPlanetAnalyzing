from data_sources import assess_monthly_completeness


def test_monthly_completeness_marks_full_series_complete():
    data = {f"2025{month:02d}": 10.0 for month in range(1, 13)}
    result = assess_monthly_completeness(data, 2025, 2025)

    assert result["expected_months"] == 12
    assert result["valid_months"] == 12
    assert result["missing_months"] == 0
    assert result["completeness_ratio"] == 1.0
    assert result["quality"] == "complete"


def test_monthly_completeness_excludes_nasa_missing_sentinel():
    data = {"202501": 1.0, "202502": -999.0, "202503": 3.0}
    result = assess_monthly_completeness(data, 2025, 2025)

    assert result["valid_months"] == 2
    assert result["missing_months"] == 10
    assert result["completeness_ratio"] == round(2 / 12, 3)
    assert result["quality"] == "partial"


def test_monthly_completeness_handles_empty_data():
    result = assess_monthly_completeness({}, 2025, 2025)

    assert result["valid_months"] == 0
    assert result["missing_months"] == 12
    assert result["completeness_ratio"] == 0.0
    assert result["quality"] == "no_valid_data"


def test_mushroom_history_produces_daily_scores():
    from data_sources import calculate_mushroom_history

    result = calculate_mushroom_history({
        "daily": {
            "time": ["2026-09-20", "2026-09-21"],
            "temperature_2m_max": [18.0, 25.0],
            "precipitation_sum": [8.0, 0.0],
            "relative_humidity_2m_mean": [80.0, 50.0],
        }
    })
    assert len(result) == 2
    assert result[0]["score"] > result[1]["score"]
    assert 0 <= result[0]["score"] <= 100


def test_mushroom_conditions_explain_inputs():
    from data_sources import calculate_mushroom_conditions

    result = calculate_mushroom_conditions(
        {
            "current": {"relative_humidity_2m": 80},
            "daily": {"precipitation_sum": [2, 2, 2], "temperature_2m_max": [18, 19, 20]},
        },
        {"daily": {"precipitation_sum": [5, 5, 5]}},
    )
    assert 0 <= result["score"] <= 100
    assert result["level"] in {"słabe", "umiarkowane", "sprzyjające"}
    assert len(result["reasons"]) >= 3
    assert "orientacyjny" in result["warning"]
