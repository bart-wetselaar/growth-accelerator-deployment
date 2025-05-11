#!/bin/bash
# Quick script to deploy the Growth Accelerator Staffing Platform to Azure App Services

# Check for Azure authentication details in environment variables
if [ -z "$AZURE_TENANT_ID" ] || [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ] || [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    if [ -f azure_credentials.json ]; then
        echo "Loading Azure credentials from azure_credentials.json..."
        AZURE_TENANT_ID=$(grep -oP '"tenantId": *"\K[^"]*' azure_credentials.json)
        AZURE_CLIENT_ID=$(grep -oP '"clientId": *"\K[^"]*' azure_credentials.json)
        AZURE_CLIENT_SECRET=$(grep -oP '"clientSecret": *"\K[^"]*' azure_credentials.json)
        AZURE_SUBSCRIPTION_ID=$(grep -oP '"subscriptionId": *"\K[^"]*' azure_credentials.json)
    else
        echo "Azure credentials not found. Please create azure_credentials.json using setup_service_principal.py or set environment variables."
        exit 1
    fi
fi

# Deploy directly to Azure App Services
python deploy_to_app_services.py \
    --tenant-id "$AZURE_TENANT_ID" \
    --client-id "$AZURE_CLIENT_ID" \
    --client-secret "$AZURE_CLIENT_SECRET" \
    --subscription-id "$AZURE_SUBSCRIPTION_ID" \
    --resource-group "growth-accelerator-rg" \
    --location "westeurope" \
    --app-name "growth-accelerator" \
    --domain "app.growthaccelerator.nl" \
    --db-server-name "growth-accelerator-db" \
    --db-username "gadmin" \
    --db-password "GrowthAccelerator2025!" \
    --db-name "growth_accelerator_db" \
    --docker-image "ghcr.io/bart-wetselaar/growth-accelerator-deployment:latest" \
    --env-vars "WORKABLE_API_KEY=$WORKABLE_API_KEY" "LINKEDIN_CLIENT_ID=$LINKEDIN_CLIENT_ID" "LINKEDIN_CLIENT_SECRET=$LINKEDIN_CLIENT_SECRET" "SQUARESPACE_API_KEY=$SQUARESPACE_API_KEY"