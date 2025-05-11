#!/bin/bash
# Quick Deploy Script for Growth Accelerator Staffing Platform
# This script downloads the necessary deployment files from GitHub and runs the deployment

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== GROWTH ACCELERATOR STAFFING PLATFORM - QUICK DEPLOY ====${NC}"
echo ""
echo "This script will download all necessary deployment files and deploy the platform to Azure."
echo ""

# Check for required commands
for cmd in curl python pip jq; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is required but not installed. Please install it and try again.${NC}"
        exit 1
    fi
done

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo -e "${YELLOW}Using temporary directory: $TEMP_DIR${NC}"

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
    echo -e "${GREEN}Cleanup complete.${NC}"
}

# Set trap to clean up on exit
trap cleanup EXIT

# Step 1: Download deployment files from GitHub
echo -e "${BLUE}==== DOWNLOADING DEPLOYMENT FILES ====${NC}"
REPO="bart-wetselaar/growth-accelerator-deployment"
FILES=(
    "deploy_to_azure_simplified.py"
    "deploy_to_azure_example.sh"
    "AZURE_README.md"
    "DNS_CONFIGURATION.md"
    "azure/azuredeploy.json"
)

mkdir -p "$TEMP_DIR/azure"

for file in "${FILES[@]}"; do
    echo "Downloading $file..."
    
    # Create directory if needed
    dir=$(dirname "$TEMP_DIR/$file")
    mkdir -p "$dir"
    
    # Download file
    curl -s "https://raw.githubusercontent.com/$REPO/main/$file" -o "$TEMP_DIR/$file"
    
    if [ $? -ne 0 ] || [ ! -s "$TEMP_DIR/$file" ]; then
        echo -e "${RED}Failed to download $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}All deployment files downloaded successfully.${NC}"

# Step 2: Install required Python packages
echo -e "${BLUE}==== INSTALLING REQUIRED PACKAGES ====${NC}"
pip install azure-identity azure-mgmt-resource azure-mgmt-web azure-mgmt-rdbms

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install required packages.${NC}"
    exit 1
fi

echo -e "${GREEN}Required packages installed successfully.${NC}"

# Step 3: Prompt for deployment parameters
echo -e "${BLUE}==== DEPLOYMENT CONFIGURATION ====${NC}"
echo "Please provide the following information to deploy the platform:"
echo ""

# Azure authentication
read -p "Azure Tenant ID: " TENANT_ID
read -p "Azure Client ID: " CLIENT_ID
read -sp "Azure Client Secret: " CLIENT_SECRET
echo ""
read -p "Azure Subscription ID: " SUBSCRIPTION_ID

# Resource configuration
read -p "Resource Group Name [growth-accelerator-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-growth-accelerator-rg}

read -p "Location [westeurope]: " LOCATION
LOCATION=${LOCATION:-westeurope}

read -p "App Name [growth-accelerator-staffing]: " APP_NAME
APP_NAME=${APP_NAME:-growth-accelerator-staffing}

read -p "Custom Domain [app.growthaccelerator.nl]: " CUSTOM_DOMAIN
CUSTOM_DOMAIN=${CUSTOM_DOMAIN:-app.growthaccelerator.nl}

# Database configuration
read -p "Database Server Name [${APP_NAME}-db]: " DB_SERVER
DB_SERVER=${DB_SERVER:-${APP_NAME}-db}

read -p "Database Name [growth_accelerator]: " DB_NAME
DB_NAME=${DB_NAME:-growth_accelerator}

read -p "Database Admin Username [dbadmin]: " DB_ADMIN
DB_ADMIN=${DB_ADMIN:-dbadmin}

read -sp "Database Admin Password: " DB_PASSWORD
echo ""

# Container configuration
read -p "GitHub Username: " GITHUB_USERNAME
read -sp "GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

read -p "Container Image [ghcr.io/${GITHUB_USERNAME}/${APP_NAME}:latest]: " CONTAINER_IMAGE
CONTAINER_IMAGE=${CONTAINER_IMAGE:-ghcr.io/${GITHUB_USERNAME}/${APP_NAME}:latest}

# API keys and secrets
read -sp "Workable API Key: " WORKABLE_API_KEY
echo ""
read -sp "LinkedIn Client ID: " LINKEDIN_CLIENT_ID
echo ""
read -sp "LinkedIn Client Secret: " LINKEDIN_CLIENT_SECRET
echo ""
read -sp "Squarespace API Key: " SQUARESPACE_API_KEY
echo ""
read -sp "Session Secret (leave empty to generate): " SESSION_SECRET
echo ""

# Step 4: Run deployment
echo -e "${BLUE}==== RUNNING DEPLOYMENT ====${NC}"
echo "Deploying to Azure..."

# Change to the temporary directory
cd "$TEMP_DIR"

# Run the deployment script
python deploy_to_azure_simplified.py \
  --tenant-id "$TENANT_ID" \
  --client-id "$CLIENT_ID" \
  --client-secret "$CLIENT_SECRET" \
  --subscription-id "$SUBSCRIPTION_ID" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --app-name "$APP_NAME" \
  --custom-domain "$CUSTOM_DOMAIN" \
  --db-server "$DB_SERVER" \
  --db-name "$DB_NAME" \
  --db-admin "$DB_ADMIN" \
  --db-password "$DB_PASSWORD" \
  --github-username "$GITHUB_USERNAME" \
  --github-token "$GITHUB_TOKEN" \
  --container-image "$CONTAINER_IMAGE" \
  --workable-api-key "$WORKABLE_API_KEY" \
  --linkedin-client-id "$LINKEDIN_CLIENT_ID" \
  --linkedin-client-secret "$LINKEDIN_CLIENT_SECRET" \
  --squarespace-api-key "$SQUARESPACE_API_KEY" \
  ${SESSION_SECRET:+--session-secret "$SESSION_SECRET"}

if [ $? -ne 0 ]; then
    echo -e "${RED}Deployment failed. Please check the error messages above.${NC}"
    exit 1
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Configure DNS records as described above"
echo "2. Set up SSL/TLS binding in the Azure Portal"
echo "3. Visit https://${APP_NAME}.azurewebsites.net to verify the deployment"
echo "4. After DNS propagation, visit https://${CUSTOM_DOMAIN}"
echo ""
echo -e "${BLUE}For more information, see:${NC}"
echo "- DNS Configuration Guide: https://github.com/${REPO}/blob/main/DNS_CONFIGURATION.md"
echo "- Azure Deployment Guide: https://github.com/${REPO}/blob/main/AZURE_DEPLOYMENT_GUIDE.md"
echo "- Azure Documentation: https://docs.microsoft.com/en-us/azure/app-service/"