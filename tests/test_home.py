from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_home_contains_planet_journal_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dziennik Planety" in response.text
    assert "/planet-journal" in response.text


def test_manifest_is_served_as_webmanifest():
    response = client.get("/manifest.webmanifest")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
    assert "Dziennik Planety" in response.text


def test_legnica_environment_endpoint_is_available():
    assert any(route.path == "/legnica/environment" for route in app.routes)


def test_legnica_weather_endpoint_is_available():
    assert any(route.path == "/legnica/weather" for route in app.routes)


def test_legnica_mushroom_endpoint_is_available():
    assert any(route.path == "/legnica/mushrooms" for route in app.routes)


def test_legnica_mushroom_history_endpoint_is_available():
    assert any(route.path == "/legnica/mushrooms/history" for route in app.routes)
