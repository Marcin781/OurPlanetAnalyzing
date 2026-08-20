# Public deployment

The application is packaged as a Docker web service and includes a Render Blueprint in `render.yaml`.

## Deploy on Render

1. Sign in to Render.
2. Create **New → Blueprint**.
3. Select the `Marcin781/OurPlanetAnalyzing` repository.
4. Render reads `render.yaml` and builds the Docker image.
5. After deployment, verify `/status` returns JSON with `status: ok`.
6. Open the generated `onrender.com` URL and test the web UI.

No Azure subscription or API key is required for the current public MVP. NCEI is accessed through its public data service.

## Production notes

- The service binds to `0.0.0.0` and uses the platform-provided `PORT`.
- `/status` is the health-check endpoint.
- Do not put secrets in Git; use the hosting provider's environment variables when future integrations require credentials.
- The current analysis endpoint is a demonstrator. Scientific production use requires verified source-data ingestion and provenance before presenting conclusions as factual.
