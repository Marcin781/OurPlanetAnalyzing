# OurPlanetAnalyzing

OurPlanetAnalyzing is a small FastAPI web application and API prototype for exploring climate, environmental and geophysical topics.

> **Current status:** prototype. The analysis engine currently uses deterministic keyword-based logic. It does **not** yet fetch live NASA/ESA/WMO/IPCC data and does not claim to provide scientific conclusions.

## Features

- Web interface at `/`
- `POST /analyze` for topic analysis
- `POST /generate-report` for JSON or Markdown reports
- `GET /status` health/status endpoint
- OpenAPI documentation at `/docs`
- Automated smoke tests and pytest
- Docker and Docker Compose support

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

The application is available at `http://127.0.0.1:8000`.

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

## OpenAPI

Regenerate the committed OpenAPI files:

```bash
python generate_openapi_files.py
```

The CI workflow verifies that generated OpenAPI files are reproducible and that tests pass.

## Roadmap

1. Connect verified public environmental data sources.
2. Add source metadata, timestamps and data-quality indicators.
3. Separate data acquisition, analysis and reporting layers.
4. Add real trend analysis instead of keyword detection.
5. Add reproducible reports and visualizations.
6. Add stronger integration tests for external data providers.

## Scientific-use disclaimer

This project is an engineering prototype. Until verified live data sources and validated analytical methods are implemented, its output should not be treated as scientific measurement, forecasting or environmental advice.
