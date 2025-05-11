#!/bin/bash
# Example script to deploy Growth Accelerator Staffing Platform to Azure
# Replace the values below with your actual Azure and API credentials

python deploy_to_azure_simplified.py \
  --tenant-id "00000000-0000-0000-0000-000000000000" \
  --client-id "00000000-0000-0000-0000-000000000000" \
  --client-secret "your-client-secret" \
  --subscription-id "00000000-0000-0000-0000-000000000000" \
  --resource-group "growth-accelerator-rg" \
  --location "westeurope" \
  --app-name "growth-accelerator-staffing" \
  --custom-domain "app.growthaccelerator.nl" \
  --db-server "growth-accelerator-staffing-db" \
  --db-name "growth_accelerator" \
  --db-admin "dbadmin" \
  --db-password "your-secure-password" \
  --github-username "bart-wetselaar" \
  --github-token "your-github-token" \
  --container-image "ghcr.io/bart-wetselaar/growth-accelerator-staffing:latest" \
  --workable-api-key "your-workable-api-key" \
  --linkedin-client-id "your-linkedin-client-id" \
  --linkedin-client-secret "your-linkedin-client-secret" \
  --squarespace-api-key "your-squarespace-api-key" \
  --session-secret "your-session-secret-or-leave-empty-to-generate"