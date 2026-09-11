# OurPlanetAnalyzing

OurPlanetAnalyzing is a FastAPI application and API for exploring climate, environmental and geophysical topics with explicit source metadata and a defensive application-security layer.

> **Current status:** working engineering prototype. Live NASA POWER temperature data is available for representative analysis points. Results are not automatically treated as scientific forecasts or area-weighted regional measurements.

## Features

- Web interface at `/`
- `POST /analyze` for deterministic topic analysis
- `POST /generate-report` for JSON or Markdown reports
- `POST /agent/analyze` for the Planet Agent
- `GET /status` health/status endpoint
- `GET /security/status` non-sensitive Security Guard telemetry
- OpenAPI documentation at `/docs`
- Live NASA POWER temperature retrieval for Poland, Polish voivodeships, voivodeship-capital cities and Central/Eastern Europe
- Automated smoke tests and pytest
- Docker support
- Non-root container user and container health check
- Deterministic Security Guard for high-confidence request probes

## Planet Agent

The Planet Agent uses the OpenAI Agents SDK and defaults to the configured `OPENAI_MODEL` value, currently `gpt-5.6-luna`. It has a deterministic NASA POWER data tool and is instructed to distinguish observations from interpretation, disclose data limitations and avoid inventing measurements or risk scores.

Set the API key only in the runtime environment; never commit it to GitHub:

```text
OPENAI_API_KEY=<your key>
OPENAI_MODEL=gpt-5.6-luna
```

## Security Guard

The application includes a defensive, deterministic request guard. It can block a limited set of high-confidence probes such as path traversal, common XSS/SQL-injection patterns, selected SSRF indicators and selected command-injection probes.

The guard is intentionally **not** described as protection against every known attack. It is a baseline layer. Production hardening should also include TLS/WAF/rate limiting at the edge, strong authentication and authorization, dependency/container scanning, secret management, centralized immutable logs, alerting, backups and incident-response procedures.

The Security Guard does not give an AI model direct destructive control over the application. Security decisions are bounded by deterministic policy.

## Local development

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Then open `http://127.0.0.1:8000` or `http://127.0.0.1:8000/docs`.

## Docker

```bash
docker compose up --build -d
```

Check health:

```bash
curl http://127.0.0.1:8000/status
```

Stop the service:

```bash
docker compose down
```

## Testing

```bash
python -m pytest -q
python smoke_test.py
```

CI compiles all application modules, runs pytest and the smoke test, and validates that generated OpenAPI JSON/YAML can be parsed.

## Data methodology

NASA POWER temperature data is fetched live for the configured analysis points for 2019–2025. A representative point is not an area-weighted polygon average. The application exposes retrieval timestamps and source URLs where applicable.

## Roadmap

1. Add more verified public environmental sources and cross-source comparison.
2. Add explicit data-quality indicators and provenance records.
3. Replace representative regional points with validated grid/polygon aggregation where appropriate.
4. Add reproducible visualizations and trend-analysis methods with validation.
5. Strengthen external-provider integration tests and resilience.
6. Extend the Security Guard with policy-based rate limiting, centralized audit logging and external edge controls.
7. Later: build the separate defensive Cyber Agent / threat-hunting layer.

## Scientific-use disclaimer

This project is an engineering prototype. Live data retrieval does not by itself make the analysis a validated scientific forecast or environmental advisory service. Interpretations must respect the stated source, period, spatial method and uncertainty limitations.
