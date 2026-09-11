# Public deployment

The application is packaged as a Docker web service and can run on Render or Azure Container Apps.

## Deploy on Render

1. Sign in to Render.
2. Create **New → Blueprint**.
3. Select the `Marcin781/OurPlanetAnalyzing` repository.
4. Render reads `render.yaml` and builds the Docker image.
5. After deployment, verify `/status` returns JSON with `status: ok`.
6. Open the generated `onrender.com` URL and test the web UI.

## Deploy on Azure Container Apps

Azure is the secondary cloud deployment. Keep the Render instance running until Azure has been verified.

The current Dockerfile exposes port `8000` and uses the platform `PORT` variable when one is provided. Azure Container Apps can build the image directly from this repository/Dockerfile. Microsoft documents `az containerapp up` as the fast path for deploying source code or a GitHub repository to Container Apps. See the official Microsoft documentation: https://learn.microsoft.com/en-us/azure/container-apps/containerapp-up

### Recommended resource names

- Resource group: `rg-ourplanet-analyzing`
- Region: `polandcentral`
- Container Apps environment: `env-ourplanet-analyzing`
- Container app: `ourplanet-analyzing`
- Target port: `8000`

Poland Central is an available Azure region; verify that it is enabled for the subscription before deployment.

### Azure CLI deployment

After signing in to Azure CLI and from the repository root:

```bash
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

az containerapp up \
  --name ourplanet-analyzing \
  --resource-group rg-ourplanet-analyzing \
  --location polandcentral \
  --environment env-ourplanet-analyzing \
  --source . \
  --ingress external
```

The command builds the Docker image from the repository, creates/uses the Container Apps environment and Log Analytics workspace, and deploys the application. The resulting FQDN is returned by Azure.

### Required environment variables

The public data endpoints do not require credentials. The Planet Agent requires the OpenAI API key at runtime.

Set the following in Azure Container Apps configuration; **never commit the key to GitHub or put it in source code**:

- `OPENAI_MODEL=gpt-5.6-luna`
- `OPENAI_API_KEY=<your Azure Container Apps secret reference/value>`

Do not paste API keys into GitHub files or into chat.

### Verification

After deployment, test:

```text
/status
/
/security/status
```

Then test `/agent/analyze` only after `OPENAI_API_KEY` has been configured in Azure.

The first verification target is `/status`. The service should report `status: ok` and the Container Apps revision should become healthy.

## Production notes

- The service binds to `0.0.0.0` and uses the platform-provided `PORT`.
- `/status` is the health-check endpoint.
- Do not put secrets in Git; use the hosting provider's environment variables/secrets.
- The current Security Guard is a deterministic defensive baseline, not a guarantee of detecting every attack.
- The current analysis endpoint is a demonstrator. Scientific production use requires verified source-data ingestion and provenance before presenting conclusions as factual.
