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
