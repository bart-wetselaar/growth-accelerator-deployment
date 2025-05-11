# Azure Service Principal Creation Guide

This guide explains how to create an Azure Service Principal with the necessary permissions to deploy the Growth Accelerator Staffing Platform to Azure App Services.

## Prerequisites

- An Azure account with an active subscription
- Access to Azure Portal with permissions to create service principals

## Step 1: Create a Service Principal in Azure Portal

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click on **+ New registration**
4. Enter the following details:
   - Name: `growth-accelerator-sp`
   - Supported account types: **Accounts in this organizational directory only**
   - Redirect URI: (Leave blank)
5. Click **Register**
6. Note the **Application (client) ID** and **Directory (tenant) ID** displayed on the overview page

## Step 2: Create a Client Secret

1. In the service principal you just created, navigate to **Certificates & secrets**
2. Under **Client secrets**, click **+ New client secret**
3. Enter a description (e.g., "Deployment Secret")
4. Choose an expiration period (recommended: 12 months)
5. Click **Add**
6. **IMPORTANT**: Copy the secret **Value** (not the Secret ID) and store it securely. You won't be able to view it again!

## Step 3: Assign Contributor Role

1. Navigate to **Subscriptions** in the Azure Portal
2. Select your subscription
3. Click on **Access control (IAM)**
4. Click **+ Add** > **Add role assignment**
5. Select the **Contributor** role
6. In the **Assign access to** field, select **User, group, or service principal**
7. Click **+ Select members**
8. Search for `growth-accelerator-sp` and select it
9. Click **Select**
10. Click **Review + assign** to complete the role assignment

## Step 4: Create Credentials File

Create a file named `azure_credentials.json` with the following content, replacing the placeholder values:

```json
{
  "tenantId": "YOUR_TENANT_ID",
  "clientId": "YOUR_CLIENT_ID",
  "clientSecret": "YOUR_CLIENT_SECRET",
  "subscriptionId": "YOUR_SUBSCRIPTION_ID"
}
```

## Step 5: Use Credentials for Deployment

Now you can use these credentials with the deployment script:

```bash
# Using the deployment script directly
python deploy_to_app_services.py \
  --tenant-id "YOUR_TENANT_ID" \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --subscription-id "YOUR_SUBSCRIPTION_ID" \
  --resource-group "growth-accelerator-rg" \
  --location "westeurope" \
  --app-name "growth-accelerator" \
  --domain "app.growthaccelerator.nl"

# Or using the deploy_now.sh script
./deploy_now.sh
```

## Security Considerations

- Store the credentials securely
- Consider using Azure Key Vault for production environments
- Rotate the client secret periodically
- Limit the service principal's permissions to only what is necessary
- In GitHub Actions, use repository secrets to store these credentials