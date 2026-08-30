param location string = resourceGroup().location
param appName string = 'dziennik-planety'
param postgresName string = 'dziennik-planety-db'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${appName}-logs'
  location: location
  properties: {
    retentionInDays: 30
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: postgresName
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: 'planetadmin'
    administratorLoginPassword: 'CHANGE_ME_IN_AZURE_PORTAL'
    storage: { storageSizeGB: 32 }
    authConfig: { activeDirectoryAuth: 'Disabled', passwordAuth: 'Enabled' }
  }
}

resource db 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'planet'
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${appName}-env'
  location: location
  properties: {
    appLogsConfiguration: { destination: 'log-analytics', logAnalyticsConfiguration: { customerId: logAnalytics.properties.customerId, sharedKey: logAnalytics.listKeys().primarySharedKey } }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: { ingress: { external: true, targetPort: 8000, transport: 'auto' } }
    template: {
      containers: [{ name: 'web', image: 'ghcr.io/Marcin781/OurPlanetAnalyzing:latest', resources: { cpu: 0.5, memory: '1Gi' } }]
      scale: { minReplicas: 0, maxReplicas: 2 }
    }
  }
}

output appUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
output postgresHost string = postgres.properties.fullyQualifiedDomainName
