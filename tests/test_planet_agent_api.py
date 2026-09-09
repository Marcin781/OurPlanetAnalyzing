from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_planet_agent_endpoint_validates_question():
    response = client.post("/agent/analyze", json={})
    assert response.status_code == 422


def test_planet_agent_endpoint_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/agent/analyze",
        json={"question": "Jaka jest temperatura w Polsce?"},
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
