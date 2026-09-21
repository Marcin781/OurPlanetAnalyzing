from fastapi.testclient import TestClient

import app as app_module


client = TestClient(app_module.app)


def test_planet_journal_endpoint_uses_deterministic_builder(monkeypatch):
    async def fake_temperature(points, region_name):
        return {
            "live_data": True,
            "provider": "NASA POWER",
            "region": region_name,
            "period": {"start": "2019", "end": "2025"},
            "method": "one representative point per region",
            "retrieved_at": "2026-09-21T00:00:00+00:00",
            "points": {
                "A": {
                    "mean": 10.0,
                    "trend": {"direction": "wzrost"},
                    "source_url": "https://example.test/a",
                    "data_quality": {"quality": "complete"},
                }
            },
        }

    monkeypatch.setattr(app_module, "build_regional_temperature", fake_temperature)
    response = client.get("/planet-journal")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Dziennik Planety — Polska"
    assert body["provider"] == "NASA POWER"
    assert body["coverage"]["valid_points"] == 1
