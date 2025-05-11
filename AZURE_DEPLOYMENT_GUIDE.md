# Azure Deployment Guide for Growth Accelerator Staffing Platform

This guide walks you through the process of deploying the Growth Accelerator Staffing Platform to Azure App Service using GitHub Actions.

## Prerequisites

- GitHub account with access to the repository
- Azure subscription
- Domain name ownership (for custom domain setup)
- API keys for: Workable, LinkedIn, Squarespace

## Deployment Steps

### 1. Create GitHub Repository

The deployment files have already been pushed to the GitHub repository:
```
https://github.com/bart-wetselaar/growth-accelerator-deployment
```

### 2. Create Azure Service Principal

Create a Service Principal in Azure for GitHub Actions to use:

```bash
az login

# List subscriptions and note your subscription ID
az account list --output table

# Create service principal with Contributor role
az ad sp create-for-rbac --name "github-actions-growth-accelerator" \
                        --role contributor \
                        --scopes /subscriptions/<subscription-id> \
                        --sdk-auth
```

Save the JSON output from this command - you'll need it for GitHub Secrets.

### 3. Set Up GitHub Secrets

Set up the required secrets in your GitHub repository:

1. In the repository, go to Settings > Secrets and variables > Actions
2. Add the following secrets:

| Secret Name | Description |
|-------------|-------------|
| AZURE_CREDENTIALS | The JSON output from the service principal creation |
| AZURE_RESOURCE_GROUP | The name of your Azure resource group |
| AZURE_APP_NAME | The name for your Azure App Service |
| WORKABLE_API_KEY | Your Workable API key |
| LINKEDIN_CLIENT_ID | Your LinkedIn OAuth client ID |
| LINKEDIN_CLIENT_SECRET | Your LinkedIn OAuth client secret |
| SQUARESPACE_API_KEY | Your Squarespace API key |
| DATABASE_URL | PostgreSQL database URL (will be created by Azure) |
| SESSION_SECRET | Random string for session encryption |

You can use the setup_github_secrets.py script to help set up these secrets:

```bash
python setup_github_secrets.py --repo bart-wetselaar/growth-accelerator-deployment --token YOUR_GITHUB_TOKEN
```

### 4. Deploy Infrastructure with ARM Template

You can deploy the infrastructure using the Azure CLI:

```bash
# Create resource group if it doesn't exist
az group create --name <resource-group-name> --location westeurope

# Deploy ARM template
az deployment group create \
  --resource-group <resource-group-name> \
  --template-file azure/azuredeploy.json \
  --parameters appName=growth-accelerator-staffing \
               location=westeurope \
               customDomainName=app.growthaccelerator.nl \
               dockerRegistryUsername=<github-username> \
               dockerRegistryPassword=<github-token> \
               databaseAdminLogin=<admin-username> \
               databaseAdminPassword=<admin-password> \
               workableApiKey=<workable-api-key> \
               linkedinClientId=<linkedin-client-id> \
               linkedinClientSecret=<linkedin-client-secret> \
               squarespaceApiKey=<squarespace-api-key>
```

### 5. Configure DNS Records

After deployment, you'll need to configure DNS records for your custom domain:

1. Get the domain verification ID from the ARM template output
2. Create TXT record: `asuid.app.growthaccelerator.nl TXT <verification-id>`
3. Create CNAME record: `app.growthaccelerator.nl CNAME growth-accelerator-staffing.azurewebsites.net`

Detailed instructions are available in the DNS_CONFIGURATION.md file.

### 6. Trigger GitHub Actions Workflow

The workflow will automatically run when you push to the main branch. You can also manually trigger it:

1. In the GitHub repository, go to Actions
2. Select the "Deploy to Azure App Service" workflow
3. Click "Run workflow"

### 7. Verify Deployment

After the GitHub Actions workflow completes:

1. Access your application at https://app.growthaccelerator.nl
2. Verify that the application is running correctly
3. Check that all API integrations are working

### 8. Set Up Monitoring

Configure monitoring for your application:

1. In the Azure Portal, go to your App Service
2. Navigate to "Monitoring" > "Alerts"
3. Set up alerts for errors and availability issues

## Troubleshooting

### DNS Configuration Issues

Use the DNS checker script to verify your DNS configuration:

```bash
python check_dns_configuration.py --domain app.growthaccelerator.nl --verification-id YOUR_VERIFICATION_ID
```

### Deployment Failures

Check the GitHub Actions logs for details on deployment failures.

### Application Issues

Check the application logs in Azure App Service:

```bash
az webapp log tail --resource-group <resource-group-name> --name growth-accelerator-staffing
```

## Additional Resources

- DNS Configuration: See DNS_CONFIGURATION.md
- Deployment Checklist: See DEPLOYMENT_CHECKLIST.md
- Azure ARM Template: See azure/azuredeploy.json
- GitHub Actions Workflow: See .github/workflows/azure-deploy.yml

## Testing Deployment

After deployment, use the deployment testing script to verify all components:

```bash
python azure_deployment_test.py --url https://app.growthaccelerator.nl
```

This script will check all key endpoints and features of the application.