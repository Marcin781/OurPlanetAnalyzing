from fastapi.testclient import TestClient

from app import app
from security_guard import inspect_request


client = TestClient(app)


def test_path_traversal_is_blocked():
    response = client.get("/search?q=%2e%2e%2fsecret")
    assert response.status_code == 403
    payload = response.json()
    assert payload["category"] == "path_traversal"
    assert payload["severity"] == "critical"
    assert payload["event_id"].startswith("sec-")


def test_normal_request_is_not_blocked():
    findings = inspect_request("/status", "", "GET")
    assert findings == []


def test_security_status_is_non_sensitive():
    response = client.get("/security/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["mode"] == "deterministic_guard"
