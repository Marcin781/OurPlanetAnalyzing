from app import AnalyzeRequest, analyze, app, generate_report, status


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
    report = generate_report(request)
    health = status()

    if analysis.risk_level != "wysoki":
        raise RuntimeError("Analyze endpoint returned unexpected risk level")
    if report.status != "generated":
        raise RuntimeError("Report endpoint did not generate a report")
    if health.status != "ok":
        raise RuntimeError("Status endpoint is not OK")

    print("Smoke test passed")


if __name__ == "__main__":
    main()
