import json

from app import AnalyzeRequest, analyze, app, generate_report, security_status, status
from fastapi.testclient import TestClient


def main() -> None:
    schema = app.openapi()
    expected_paths = {"/analyze", "/generate-report", "/status", "/security/status", "/agent/analyze"}
    missing_paths = expected_paths.difference(schema["paths"])

    if missing_paths:
        raise RuntimeError(f"Missing OpenAPI paths: {sorted(missing_paths)}")

    request = AnalyzeRequest(
        question="Sprawdz CO2, klimat i temperature",
        output_format="json",
    )
    analysis = analyze(request)
    report_json = generate_report(request)
    markdown_request = AnalyzeRequest(
        question="Sprawdz CO2, klimat i temperature",
        output_format="markdown",
    )
    report_markdown = generate_report(markdown_request)
    health = status()
    security = security_status()

    if analysis.risk_level != "brak_oceny":
        raise RuntimeError("Analyze endpoint returned an unvalidated risk score")
    if report_json.status != "generated":
        raise RuntimeError("Report endpoint did not generate a JSON report")
    if json.loads(report_json.content)["risk_level"] != "brak_oceny":
        raise RuntimeError("JSON report contains an unvalidated risk score")
    if report_markdown.status != "generated":
        raise RuntimeError("Report endpoint did not generate a Markdown report")
    if report_markdown.format != "markdown":
        raise RuntimeError("Markdown report returned the wrong format")
    if "# Raport OurPlanetAnalyzing" not in report_markdown.content:
        raise RuntimeError("Markdown report content is missing the report heading")
    if health.status != "ok":
        raise RuntimeError("Status endpoint is not OK")
    if security["enabled"] is not True:
        raise RuntimeError("Security Guard is not enabled")

    client = TestClient(app)
    invalid_response = client.post(
        "/analyze",
        json={"question": "xx", "output_format": "json"},
    )
    if invalid_response.status_code != 422:
        raise RuntimeError(
            f"Expected 422 for invalid analyze request, got {invalid_response.status_code}"
        )

    blocked_response = client.get("/search?q=%2e%2e%2fsecret")
    if blocked_response.status_code != 403:
        raise RuntimeError(
            f"Security Guard did not block a traversal probe: {blocked_response.status_code}"
        )
    if "event_id" not in blocked_response.json():
        raise RuntimeError("Security Guard response is missing an event id")

    print("Smoke test passed")


if __name__ == "__main__":
    main()
