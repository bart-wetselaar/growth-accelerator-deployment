#!/bin/bash
# Growth Accelerator Staffing Platform - Azure Deployment Script
# Replace the placeholder values with your actual Azure credentials

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== GROWTH ACCELERATOR STAFFING PLATFORM - AZURE DEPLOYMENT ====${NC}"
echo ""
echo "This script will deploy the application to Azure App Service."
echo ""

# Check if required Python packages are installed
echo -e "${BLUE}Installing required Python packages...${NC}"
pip install azure-identity azure-mgmt-resource azure-mgmt-web azure-mgmt-rdbms

# Run the deployment script with command line arguments
python deploy_to_azure_simplified.py \
  --tenant-id "YOUR_TENANT_ID" \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --subscription-id "YOUR_SUBSCRIPTION_ID" \
  --resource-group "growth-accelerator-rg" \
  --location "westeurope" \
  --app-name "growth-accelerator-staffing" \
  --custom-domain "app.growthaccelerator.nl" \
  --db-server "growth-accelerator-staffing-db" \
  --db-name "growth_accelerator" \
  --db-admin "dbadmin" \
  --db-password "YOUR_SECURE_PASSWORD" \
  --github-username "bart-wetselaar" \
  --github-token "YOUR_GITHUB_TOKEN" \
  --container-image "ghcr.io/bart-wetselaar/growth-accelerator-staffing:latest" \
  --workable-api-key "Wwo5b9mjXvFypF04nTxBkpGu8ibvMRd1Po63NHh1SKo" \
  --linkedin-client-id "YOUR_LINKEDIN_CLIENT_ID" \
  --linkedin-client-secret "YOUR_LINKEDIN_CLIENT_SECRET" \
  --squarespace-api-key "dc66a1c6-6049-4ad1-a0d5-a545fce63b88"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Deployment completed successfully!${NC}"
  echo ""
  echo -e "${BLUE}Next Steps:${NC}"
  echo "1. Configure DNS records for app.growthaccelerator.nl as shown above"
  echo "2. Verify domain ownership in the Azure Portal"
  echo "3. Set up SSL/TLS binding"
  echo "4. Test the application"
else
  echo -e "${RED}Deployment failed. Please check the error messages above.${NC}"
fi