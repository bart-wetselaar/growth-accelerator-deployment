# Azure Deployment for Growth Accelerator Staffing Platform

This document provides instructions for deploying the Growth Accelerator Staffing Platform to Azure using our Python-based deployment script.

## Prerequisites

- Python 3.10 or higher
- Azure subscription and credentials
- Service Principal with Contributor permissions
- API keys for Workable, LinkedIn, and Squarespace
- GitHub account with personal access token (for container registry)

## Setup Instructions

### 1. Create Azure Service Principal

You need a service principal with Contributor rights to deploy resources to Azure:

```bash
az login
az account set --subscription <subscription-id>
az ad sp create-for-rbac --name "growth-accelerator-deployment" --role contributor --scopes /subscriptions/<subscription-id>
```

Save the JSON output from this command, which contains:
- tenant_id
- client_id
- client_secret

### 2. Install Required Packages

```bash
pip install azure-identity azure-mgmt-resource azure-mgmt-web azure-mgmt-rdbms
```

### 3. Run the Deployment Script

```bash
python deploy_to_azure_simplified.py
```

The script will prompt you for:
- Azure tenant ID, client ID, and client secret (from the service principal)
- Azure subscription ID
- Resource group name
- Location for resources
- App name
- Custom domain name
- API keys (Workable, LinkedIn, Squarespace)
- Container registry credentials
- Database configuration

### 4. Configure DNS Records

After deployment, you need to configure DNS records for your custom domain:

1. Create a TXT record:
   - Host: `asuid.<your-domain>`
   - Value: `<verification-id>` (provided by the script)

2. Create a CNAME record:
   - Host: `<your-subdomain>` (e.g., app)
   - Value: `<app-name>.azurewebsites.net`

### 5. Add Custom Domain in Azure Portal

1. Go to your App Service in the Azure Portal
2. Navigate to Custom domains
3. Add your custom domain
4. Set up an SSL binding using App Service Managed Certificate

## Deployment Options

### Direct Script Deployment

The `deploy_to_azure_simplified.py` script provides a one-step deployment process that creates all necessary resources.

### GitHub Actions Deployment

For continuous deployment, use the GitHub Actions workflow:

1. Push your code to GitHub
2. Set up the required GitHub secrets (see `setup_github_secrets.py`)
3. The workflow will automatically build a Docker image and deploy to Azure App Service

### ARM Template Deployment

For infrastructure-as-code deployment:

```bash
az group create --name <resource-group> --location <location>
az deployment group create --resource-group <resource-group> --template-file azure/azuredeploy.json --parameters @azure/parameters.json
```

## Additional Resources

- [DNS Configuration Guide](DNS_CONFIGURATION.md)
- [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)

## Troubleshooting

### Common Issues

1. **Service Principal Authentication Failure**
   - Ensure the service principal has Contributor role
   - Check if the credentials have expired

2. **Resource Name Conflicts**
   - Azure resource names must be globally unique
   - Try a different name if you get a conflict

3. **DNS Configuration Issues**
   - DNS changes can take up to 48 hours to propagate
   - Verify records using `dig` or online DNS tools

4. **Container Registry Access**
   - Ensure your GitHub token has package:read and package:write permissions

For additional help, run the deployment test script:
```bash
python azure_deployment_test.py --url https://<your-domain>
```