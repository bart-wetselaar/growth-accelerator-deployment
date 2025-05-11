#!/bin/bash
# Growth Accelerator Staffing Platform - Azure Deployment Script
# This script deploys the application to Azure App Service using ARM templates

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to display section headers
header() {
    echo -e "\n${MAGENTA}${BOLD}==== $1 ====${NC}\n"
}

# Function to display success messages
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to display warnings
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to display errors
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to display commands
cmd() {
    echo -e "${BLUE}$ $1${NC}"
}

# Check if Azure CLI is installed
check_azure_cli() {
    header "CHECKING PREREQUISITES"
    
    if ! command -v az &> /dev/null; then
        error "Azure CLI is not installed."
        echo -e "Please install it using:\n${BLUE}$ curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash${NC}"
        exit 1
    fi
    
    success "Azure CLI is installed"
    
    # Check if logged in
    az account show &> /dev/null
    if [ $? -ne 0 ]; then
        warning "You are not logged in to Azure. Please login."
        cmd "az login"
        az login
        if [ $? -ne 0 ]; then
            error "Failed to login to Azure."
            exit 1
        fi
    fi
    
    success "Logged in to Azure"
}

# Get deployment parameters
get_parameters() {
    header "DEPLOYMENT PARAMETERS"
    
    # Default values
    DEFAULT_RESOURCE_GROUP="growth-accelerator-rg"
    DEFAULT_LOCATION="westeurope"
    DEFAULT_APP_NAME="growth-accelerator-staffing"
    DEFAULT_CUSTOM_DOMAIN="app.growthaccelerator.nl"
    DEFAULT_DATABASE_ADMIN="dbadmin"
    DEFAULT_DATABASE_NAME="growth_accelerator"
    DEFAULT_APP_SERVICE_PLAN_SKU="P1v2"
    DEFAULT_DOCKER_REGISTRY_URL="https://ghcr.io"
    DEFAULT_DOCKER_IMAGE_NAME="ghcr.io/growthaccelerator/growth-accelerator-staffing:latest"
    DEFAULT_ENABLE_CDN="true"
    
    # Get parameters from user with defaults
    echo -e "Please provide the following deployment parameters (press Enter to use defaults):"
    
    read -p "Resource Group Name [$DEFAULT_RESOURCE_GROUP]: " RESOURCE_GROUP
    RESOURCE_GROUP=${RESOURCE_GROUP:-$DEFAULT_RESOURCE_GROUP}
    
    read -p "Location [$DEFAULT_LOCATION]: " LOCATION
    LOCATION=${LOCATION:-$DEFAULT_LOCATION}
    
    read -p "App Name [$DEFAULT_APP_NAME]: " APP_NAME
    APP_NAME=${APP_NAME:-$DEFAULT_APP_NAME}
    
    read -p "Custom Domain [$DEFAULT_CUSTOM_DOMAIN]: " CUSTOM_DOMAIN
    CUSTOM_DOMAIN=${CUSTOM_DOMAIN:-$DEFAULT_CUSTOM_DOMAIN}
    
    read -p "Database Admin Username [$DEFAULT_DATABASE_ADMIN]: " DATABASE_ADMIN
    DATABASE_ADMIN=${DATABASE_ADMIN:-$DEFAULT_DATABASE_ADMIN}
    
    read -p "Database Name [$DEFAULT_DATABASE_NAME]: " DATABASE_NAME
    DATABASE_NAME=${DATABASE_NAME:-$DEFAULT_DATABASE_NAME}
    
    read -p "App Service Plan SKU [$DEFAULT_APP_SERVICE_PLAN_SKU]: " APP_SERVICE_PLAN_SKU
    APP_SERVICE_PLAN_SKU=${APP_SERVICE_PLAN_SKU:-$DEFAULT_APP_SERVICE_PLAN_SKU}
    
    read -p "Docker Registry URL [$DEFAULT_DOCKER_REGISTRY_URL]: " DOCKER_REGISTRY_URL
    DOCKER_REGISTRY_URL=${DOCKER_REGISTRY_URL:-$DEFAULT_DOCKER_REGISTRY_URL}
    
    read -p "Docker Image Name [$DEFAULT_DOCKER_IMAGE_NAME]: " DOCKER_IMAGE_NAME
    DOCKER_IMAGE_NAME=${DOCKER_IMAGE_NAME:-$DEFAULT_DOCKER_IMAGE_NAME}
    
    read -p "Docker Registry Username: " DOCKER_REGISTRY_USERNAME
    while [ -z "$DOCKER_REGISTRY_USERNAME" ]; do
        warning "Docker Registry Username is required."
        read -p "Docker Registry Username: " DOCKER_REGISTRY_USERNAME
    done
    
    read -sp "Docker Registry Password: " DOCKER_REGISTRY_PASSWORD
    echo
    while [ -z "$DOCKER_REGISTRY_PASSWORD" ]; do
        warning "Docker Registry Password is required."
        read -sp "Docker Registry Password: " DOCKER_REGISTRY_PASSWORD
        echo
    done
    
    read -sp "Database Admin Password: " DATABASE_PASSWORD
    echo
    while [ -z "$DATABASE_PASSWORD" ]; do
        warning "Database Admin Password is required."
        read -sp "Database Admin Password: " DATABASE_PASSWORD
        echo
    done
    
    read -sp "Workable API Key: " WORKABLE_API_KEY
    echo
    while [ -z "$WORKABLE_API_KEY" ]; do
        warning "Workable API Key is required."
        read -sp "Workable API Key: " WORKABLE_API_KEY
        echo
    done
    
    read -sp "LinkedIn Client ID: " LINKEDIN_CLIENT_ID
    echo
    while [ -z "$LINKEDIN_CLIENT_ID" ]; do
        warning "LinkedIn Client ID is required."
        read -sp "LinkedIn Client ID: " LINKEDIN_CLIENT_ID
        echo
    done
    
    read -sp "LinkedIn Client Secret: " LINKEDIN_CLIENT_SECRET
    echo
    while [ -z "$LINKEDIN_CLIENT_SECRET" ]; do
        warning "LinkedIn Client Secret is required."
        read -sp "LinkedIn Client Secret: " LINKEDIN_CLIENT_SECRET
        echo
    done
    
    read -sp "Squarespace API Key: " SQUARESPACE_API_KEY
    echo
    while [ -z "$SQUARESPACE_API_KEY" ]; do
        warning "Squarespace API Key is required."
        read -sp "Squarespace API Key: " SQUARESPACE_API_KEY
        echo
    done
    
    read -sp "Session Secret (leave empty to generate): " SESSION_SECRET
    echo
    if [ -z "$SESSION_SECRET" ]; then
        SESSION_SECRET=$(uuidgen)
        success "Generated Session Secret"
    fi
    
    read -p "Enable CDN [$DEFAULT_ENABLE_CDN]: " ENABLE_CDN
    ENABLE_CDN=${ENABLE_CDN:-$DEFAULT_ENABLE_CDN}
    
    echo
    echo -e "${CYAN}Deployment Parameters Summary:${NC}"
    echo -e "Resource Group: ${BOLD}$RESOURCE_GROUP${NC}"
    echo -e "Location: ${BOLD}$LOCATION${NC}"
    echo -e "App Name: ${BOLD}$APP_NAME${NC}"
    echo -e "Custom Domain: ${BOLD}$CUSTOM_DOMAIN${NC}"
    echo -e "Database Admin: ${BOLD}$DATABASE_ADMIN${NC}"
    echo -e "Database Name: ${BOLD}$DATABASE_NAME${NC}"
    echo -e "App Service Plan SKU: ${BOLD}$APP_SERVICE_PLAN_SKU${NC}"
    echo -e "Docker Registry: ${BOLD}$DOCKER_REGISTRY_URL${NC}"
    echo -e "Docker Image: ${BOLD}$DOCKER_IMAGE_NAME${NC}"
    echo -e "Enable CDN: ${BOLD}$ENABLE_CDN${NC}"
    
    # Confirm deployment
    echo
    read -p "Proceed with deployment? (y/n) [y]: " CONFIRM
    CONFIRM=${CONFIRM:-y}
    
    if [[ "${CONFIRM,,}" != "y" && "${CONFIRM,,}" != "yes" ]]; then
        warning "Deployment cancelled by user."
        exit 0
    fi
}

# Create Resource Group
create_resource_group() {
    header "CREATING RESOURCE GROUP"
    
    cmd "az group create --name $RESOURCE_GROUP --location $LOCATION"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
    
    success "Resource Group '$RESOURCE_GROUP' created"
}

# Deploy ARM Template
deploy_arm_template() {
    header "DEPLOYING ARM TEMPLATE"
    
    cmd "az deployment group create --resource-group $RESOURCE_GROUP --template-file azure/azuredeploy.json --parameters ..."
    
    # Deploy using Azure ARM Template
    DEPLOYMENT_OUTPUT=$(az deployment group create \
        --resource-group "$RESOURCE_GROUP" \
        --template-file "azure/azuredeploy.json" \
        --parameters \
            appName="$APP_NAME" \
            location="$LOCATION" \
            customDomainName="$CUSTOM_DOMAIN" \
            dockerImageName="$DOCKER_IMAGE_NAME" \
            dockerRegistryUrl="$DOCKER_REGISTRY_URL" \
            dockerRegistryUsername="$DOCKER_REGISTRY_USERNAME" \
            dockerRegistryPassword="$DOCKER_REGISTRY_PASSWORD" \
            databaseAdminLogin="$DATABASE_ADMIN" \
            databaseAdminPassword="$DATABASE_PASSWORD" \
            databaseName="$DATABASE_NAME" \
            workableApiKey="$WORKABLE_API_KEY" \
            linkedinClientId="$LINKEDIN_CLIENT_ID" \
            linkedinClientSecret="$LINKEDIN_CLIENT_SECRET" \
            squarespaceApiKey="$SQUARESPACE_API_KEY" \
            sessionSecret="$SESSION_SECRET" \
            appServicePlanSku="$APP_SERVICE_PLAN_SKU" \
            enableCdn="$ENABLE_CDN")
    
    if [ $? -ne 0 ]; then
        error "Deployment failed."
        exit 1
    fi
    
    success "ARM template deployed successfully"
    
    # Extract outputs
    WEB_APP_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.webAppUrl.value')
    CDN_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.cdnUrl.value')
    DOMAIN_VERIFICATION_ID=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.customDomainVerificationId.value')
    DB_SERVER_FQDN=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.databaseServerFqdn.value')
    APP_INSIGHTS_KEY=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.appInsightsKey.value')
}

# Print DNS Configuration Instructions
print_dns_instructions() {
    header "CUSTOM DOMAIN CONFIGURATION"
    
    echo -e "To set up your custom domain ${BOLD}$CUSTOM_DOMAIN${NC}, add the following DNS records:"
    echo
    echo -e "1. ${BOLD}TXT Record${NC}"
    echo -e "   Name: ${CYAN}asuid.$CUSTOM_DOMAIN${NC}"
    echo -e "   Value: ${CYAN}$DOMAIN_VERIFICATION_ID${NC}"
    echo
    echo -e "2. ${BOLD}CNAME Record${NC}"
    echo -e "   Name: ${CYAN}${CUSTOM_DOMAIN%%.*}${NC}"
    echo -e "   Value: ${CYAN}$APP_NAME.azurewebsites.net${NC}"
    echo
    if [ "$ENABLE_CDN" = "true" ]; then
        echo -e "3. ${BOLD}Optional: CNAME for CDN${NC}"
        echo -e "   Name: ${CYAN}cdn${NC}"
        echo -e "   Value: ${CYAN}${APP_NAME}-endpoint.azureedge.net${NC}"
        echo
    fi
    
    echo -e "After DNS propagation, add the custom domain in Azure Portal:"
    echo -e "1. Go to Azure Portal > App Services > $APP_NAME > Custom domains"
    echo -e "2. Add '$CUSTOM_DOMAIN' and validate the domain"
    echo -e "3. Add a managed certificate for HTTPS"
}

# Print deployment summary
print_summary() {
    header "DEPLOYMENT SUMMARY"
    
    echo -e "${GREEN}${BOLD}Growth Accelerator Staffing Platform deployed successfully!${NC}"
    echo
    echo -e "Web App URL: ${CYAN}$WEB_APP_URL${NC}"
    if [ "$ENABLE_CDN" = "true" ]; then
        echo -e "CDN URL: ${CYAN}$CDN_URL${NC}"
    fi
    echo -e "Database Server: ${CYAN}$DB_SERVER_FQDN${NC}"
    echo
    echo -e "Application Insights is set up at:"
    echo -e "Azure Portal > Application Insights > ${APP_NAME}-insights"
    echo
    echo -e "Monitor the application at:"
    echo -e "Azure Portal > App Services > $APP_NAME > Monitoring"
    echo
    echo -e "${YELLOW}NOTE:${NC} It may take a few minutes for the application to fully start. "
    echo -e "You can check the deployment status on Azure Portal."
}

# Main function
main() {
    header "GROWTH ACCELERATOR STAFFING PLATFORM DEPLOYMENT"
    
    check_azure_cli
    get_parameters
    create_resource_group
    deploy_arm_template
    print_dns_instructions
    print_summary
}

# Run main function
main