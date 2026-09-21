from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_home_contains_planet_journal_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dziennik Planety" in response.text
    assert "/planet-journal" in response.text
