# Creating Azure Service Principal for Deployment

This guide walks you through the process of creating an Azure Service Principal that can be used to deploy the Growth Accelerator Staffing Platform to Azure.

## What is a Service Principal?

A Service Principal is an identity created for applications, services, and automation tools to access Azure resources. It's like a user identity (username and password) but for an application instead of a person.

## Prerequisites

- An Azure account with an active subscription
- Azure CLI installed, or access to Azure Cloud Shell

## Step 1: Sign in to Azure

### Using Azure CLI

```bash
az login
```

### Using Azure Cloud Shell

Open [Azure Cloud Shell](https://shell.azure.com/)

## Step 2: Get your Subscription ID

List all subscriptions you have access to:

```bash
az account list --output table
```

Note the `SubscriptionId` of the subscription you want to use.

## Step 3: Set the Active Subscription

If you have multiple subscriptions, set the active one:

```bash
az account set --subscription "your-subscription-id"
```

## Step 4: Create a Service Principal

Create a service principal with the Contributor role scoped to your subscription:

```bash
az ad sp create-for-rbac --name "growth-accelerator-sp" --role Contributor --scopes /subscriptions/your-subscription-id
```

This command will output something like:

```json
{
  "appId": "00000000-0000-0000-0000-000000000000",
  "displayName": "growth-accelerator-sp",
  "password": "random-password",
  "tenant": "00000000-0000-0000-0000-000000000000"
}
```

Note these values, as they map to our deployment script parameters:
- `appId` is the `client_id`
- `password` is the `client_secret`
- `tenant` is the `tenant_id`
- The subscription ID you noted earlier is the `subscription_id`

## Step 5: Verify the Service Principal

Verify that the service principal was created successfully:

```bash
az ad sp show --id "app-id-from-previous-step"
```

## Step 6: Use the Service Principal for Deployment

Now you can use these credentials in our deployment script:

```bash
python deploy_to_azure_simplified.py \
  --tenant-id "tenant-id" \
  --client-id "app-id" \
  --client-secret "password" \
  --subscription-id "subscription-id" \
  # ... other parameters
```

## Security Best Practices

1. **Limit Permissions**: If possible, assign more specific roles instead of Contributor for the entire subscription.
2. **Rotate Credentials**: Periodically rotate the service principal password.
3. **Secure Storage**: Store the credentials securely, preferably in a key vault or secure environment variables.
4. **Audit Usage**: Regularly review the activities of your service principals.

## Troubleshooting

### Authentication Failures

If you encounter "Insufficient privileges" or authentication errors:

1. Verify that the service principal has the correct role assignment
2. Check that the credentials are correctly entered
3. Ensure the service principal hasn't been disabled or expired

```bash
# Check role assignments
az role assignment list --assignee "app-id"
```

### Creating Service Principal with More Restricted Permissions

For production use, you may want to create a service principal with more limited permissions:

```bash
# Create a resource group first
az group create --name growth-accelerator-rg --location westeurope

# Create service principal with Contributor role at resource group level only
az ad sp create-for-rbac --name "growth-accelerator-sp" --role Contributor --scopes /subscriptions/your-subscription-id/resourceGroups/growth-accelerator-rg
```

This limits the service principal to only manage resources within the specified resource group.

## Cleaning Up

If you need to remove the service principal later:

```bash
az ad sp delete --id "app-id"
```