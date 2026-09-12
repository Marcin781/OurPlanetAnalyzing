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

The current Dockerfile exposes port `8000` and uses the platform `PORT` variable when one is provided. Azure Container Apps can build the image directly from this repository/Dockerfile. Microsoft documents `az containerapp up` as the fast path for deploying source code or a GitHub repository to Container Apps.

### Recommended resource names

- Resource group: `rg-ourplanet-analyzing`
- Region: `polandcentral`
- Container Apps environment: `env-ourplanet-analyzing`
- Container app: `ourplanet-analyzing`
- Target port: `8000`

Poland Central is an available Azure region; verify that it is enabled for the subscription before deployment.

### Azure CLI deployment

From the repository root:

```bash
az login
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

az containerapp up \
  --name ourplanet-analyzing \
  --resource-group rg-ourplanet-analyzing \
  --location polandcentral \
  --environment env-ourplanet-analyzing \
  --source . \
  --ingress external \
  --target-port 8000
```

The command builds the Docker image from the repository, creates/uses the Container Apps environment and Log Analytics workspace, and deploys the application. The resulting FQDN is returned by Azure.

### GitHub Actions deployment

The repository also contains `.github/workflows/azure-deploy.yml`. It is **manual-only** (`workflow_dispatch`) so adding the workflow cannot unexpectedly replace the current Render deployment.

Before running it, configure a GitHub Actions environment named `azure` with these secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `OPENAI_API_KEY`

The Azure identity should use GitHub OIDC/federated credentials and only the minimum required permissions for the resource group. The workflow stores the OpenAI key as an Azure Container Apps secret and exposes it to the application through `secretref`; the key is never written to the repository.

### Key Vault

Key Vault can be added as a later hardening step once the Azure identity and Container Apps deployment are verified. The current deployment workflow deliberately uses the native Container Apps secret store first, because it keeps the initial deployment smaller and easier to validate.

### Required environment variables

The public data endpoints do not require credentials. The Planet Agent requires the OpenAI API key at runtime.

- `OPENAI_MODEL=gpt-5.6-luna`
- `OPENAI_API_KEY` — stored as an Azure Container Apps secret

Never commit an API key to GitHub or put it in source code or chat.

### Verification

After deployment, verify:

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
