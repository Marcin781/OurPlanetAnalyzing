# Project map

## Which branch should I use?

| Branch | Role | Status |
|---|---|---|
| `main` | **Production / current project** | 🟢 Use this |
| `planet-dashboard-mvp` | Older Dziennik Planety + Render/Postgres implementation | 🟡 Legacy; keep only for database recovery/history |
| `audit-improvements` | Earlier audit work | ⚪ Historical |
| `codex/build-web-app` | Earlier web/PWA work | ⚪ Historical |
| `codex/github-audit-fixes` | Earlier GitHub audit fixes | ⚪ Historical |
| `refactor/project-structure` | Earlier structure refactor | ⚪ Historical |

**Rule:** new development goes to `main`. Do not build new features on the legacy dashboard branch.

## Main application

- `app.py` — FastAPI application, API routes and PWA home page.
- `data_sources.py` — external data providers and data-quality handling.
- `planet_journal.py` — deterministic Dziennik Planety generation.
- `planet_agent.py` — optional OpenAI Agents SDK integration.
- `security_guard.py` — deterministic defensive request guard.
- `analysis/trends.py` — trends, comparisons and anomaly signals.
- `regions.py` / `cities.py` — geographic reference points.
- `manifest.webmanifest` — PWA metadata.
- `sw.js` — PWA service worker and cache lifecycle.
- `Dockerfile` / `docker-compose.yml` — container deployment.
- `.github/workflows/ci.yml` — automated tests and validation.

## Tests

Tests live under `tests/`. Run:

```bash
python -m pytest -q
python smoke_test.py
```

## Data interpretation

The current climate analysis uses representative NASA POWER points. It is **not** an area-weighted regional average and is not a scientific forecast.

The Legnica mushroom module is a weather-derived indicator. It does **not** confirm mushroom fruiting in a forest.

## Deployment

The production Render service follows `main` and is the version represented by the public PWA.

Before changing deployment configuration:

1. Check CI.
2. Check the Render deployment.
3. Check `/status`.
4. Only then treat the change as production-ready.

## Database

The older `planet-dashboard-mvp` branch contains the legacy PostgreSQL integration. Its Render database is separate from the current main application architecture.

The database backup is **not stored in this public repository**. Keep SQL dumps private.

## Where to look first

If you want to understand the project quickly:

1. Start with this file.
2. Read `README.md`.
3. Open `app.py`.
4. Then `data_sources.py`.
5. Then `planet_journal.py`.
6. Look at `tests/` before changing behavior.
