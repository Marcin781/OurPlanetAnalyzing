from app import build_analysis

import pytest


@pytest.mark.asyncio
async def test_keyword_detection_does_not_create_unvalidated_risk_score():
    _, risk_level, _, _, _ = await build_analysis("CO2 i zmiany klimatyczne")
    assert risk_level == "brak_oceny"
