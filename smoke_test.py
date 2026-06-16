import json

from app import AnalyzeRequest, analyze, app, generate_report, status
from fastapi.testclient import TestClient


def main() -> None:
    schema = app.openapi()
    expected_paths = {"/analyze", "/generate-report", "/status"}
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

    if analysis.risk_level != "wysoki":
        raise RuntimeError("Analyze endpoint returned unexpected risk level")
    if report_json.status != "generated":
        raise RuntimeError("Report endpoint did not generate a JSON report")
    if json.loads(report_json.content)["risk_level"] != "wysoki":
        raise RuntimeError("JSON report content is missing the expected risk level")
    if report_markdown.status != "generated":
        raise RuntimeError("Report endpoint did not generate a Markdown report")
    if report_markdown.format != "markdown":
        raise RuntimeError("Markdown report returned the wrong format")
    if "# Raport OurPlanetAnalyzing" not in report_markdown.content:
        raise RuntimeError("Markdown report content is missing the report heading")
    if health.status != "ok":
        raise RuntimeError("Status endpoint is not OK")

    client = TestClient(app)
    invalid_response = client.post(
        "/analyze",
        json={"question": "xx", "output_format": "json"},
    )
    if invalid_response.status_code != 422:
        raise RuntimeError(
            f"Expected 422 for invalid analyze request, got {invalid_response.status_code}"
        )

    print("Smoke test passed")


if __name__ == "__main__":
    main()
