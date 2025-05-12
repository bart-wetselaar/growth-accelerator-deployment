#!/usr/bin/env python3
"""
Direct deployment script for Growth Accelerator Staffing Platform to Azure App Services.
This script uses the Azure SDK to deploy directly to Azure App Services.
"""

import os
import sys
import time
from datetime import datetime

# Azure SDK imports
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import Site, SiteConfig, NameValuePair, AppServicePlan

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}✘ {message}{Colors.ENDC}")

def get_credential():
    """Get Azure credential from environment variables."""
    try:
        tenant_id = os.environ.get("AZURE_TENANT_ID")
        client_id = os.environ.get("AZURE_CLIENT_ID")
        client_secret = os.environ.get("AZURE_CLIENT_SECRET")
        
        print_header("Authenticating with Azure...")
        print(f"Tenant ID: {tenant_id}")
        print(f"Client ID: {client_id}")
        
        if not tenant_id or not client_id or not client_secret:
            print_error("Azure credentials not found in environment variables.")
            print("Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET environment variables.")
            sys.exit(1)
        
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        print_success("Successfully authenticated with Azure")
        return credential
    except Exception as e:
        print_error(f"Authentication failed: {e}")
        sys.exit(1)

def ensure_resource_group(credential, subscription_id, resource_group, location):
    """Ensure the resource group exists."""
    print_header("\nEnsuring resource group exists...")
    
    try:
        resource_client = ResourceManagementClient(credential, subscription_id)
        
        # Check if the resource group exists
        groups = list(resource_client.resource_groups.list())
        for group in groups:
            if group.name.lower() == resource_group.lower():
                print_success(f"Resource group '{resource_group}' already exists.")
                return
        
        # Create the resource group
        print(f"Creating resource group '{resource_group}' in location '{location}'...")
        resource_client.resource_groups.create_or_update(
            resource_group,
            {"location": location}
        )
        print_success(f"Resource group '{resource_group}' created successfully.")
    except Exception as e:
        print_error(f"Failed to ensure resource group: {e}")
        sys.exit(1)

def create_app_service_plan(credential, subscription_id, resource_group, location, plan_name):
    """Create an App Service Plan."""
    print_header("\nCreating App Service Plan...")
    
    try:
        web_client = WebSiteManagementClient(credential, subscription_id)
        
        # Check if the plan already exists
        plans = list(web_client.app_service_plans.list_by_resource_group(resource_group))
        for plan in plans:
            if plan.name.lower() == plan_name.lower():
                print_success(f"App Service Plan '{plan_name}' already exists.")
                return plan
        
        # Create the App Service Plan with P1v2 tier
        print(f"Creating App Service Plan '{plan_name}' in location '{location}'...")
        
        poller = web_client.app_service_plans.begin_create_or_update(
            resource_group,
            plan_name,
            {
                "location": location,
                "sku": {
                    "name": "P1v2",
                    "tier": "PremiumV2",
                    "size": "P1v2",
                    "family": "Pv2",
                    "capacity": 1
                },
                "kind": "linux",
                "reserved": True  # For Linux
            }
        )
        
        app_service_plan = poller.result()
        print_success(f"App Service Plan '{plan_name}' created successfully.")
        return app_service_plan
    except Exception as e:
        print_error(f"Failed to create App Service Plan: {e}")
        sys.exit(1)

def deploy_web_app(credential, subscription_id, resource_group, location, app_name, plan_id, docker_image):
    """Deploy the web app to Azure App Services."""
    print_header("\nDeploying Web App to Azure App Services...")
    
    try:
        web_client = WebSiteManagementClient(credential, subscription_id)
        
        # Check if the web app already exists
        sites = list(web_client.web_apps.list_by_resource_group(resource_group))
        web_app = None
        for site in sites:
            if site.name.lower() == app_name.lower():
                print_success(f"Web App '{app_name}' already exists.")
                web_app = site
                break
        
        # Prepare app settings
        app_settings = [
            {"name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE", "value": "false"},
            {"name": "DOCKER_REGISTRY_SERVER_URL", "value": "https://ghcr.io"},
            {"name": "DOCKER_ENABLE_CI", "value": "true"},
            {"name": "SESSION_SECRET", "value": os.urandom(24).hex()},
            {"name": "WORKABLE_API_KEY", "value": os.environ.get("WORKABLE_API_KEY", "")},
            {"name": "LINKEDIN_CLIENT_ID", "value": os.environ.get("LINKEDIN_CLIENT_ID", "")},
            {"name": "LINKEDIN_CLIENT_SECRET", "value": os.environ.get("LINKEDIN_CLIENT_SECRET", "")},
            {"name": "SQUARESPACE_API_KEY", "value": os.environ.get("SQUARESPACE_API_KEY", "")}
        ]
        
        # Add Database URL if available
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            app_settings.append({"name": "DATABASE_URL", "value": database_url})
        
        if not web_app:
            # Create the web app
            print(f"Creating Web App '{app_name}' in location '{location}'...")
            
            poller = web_client.web_apps.begin_create_or_update(
                resource_group,
                app_name,
                {
                    "location": location,
                    "server_farm_id": plan_id,
                    "site_config": {
                        "app_settings": app_settings,
                        "linux_fx_version": f"DOCKER|{docker_image}",
                        "always_on": True
                    }
                }
            )
            
            web_app = poller.result()
            print_success(f"Web App '{app_name}' created and configured successfully.")
        else:
            # Update the existing web app
            print(f"Updating Web App '{app_name}'...")
            
            # Convert app settings to list of NameValuePair objects
            name_value_pairs = []
            for setting in app_settings:
                name_value_pairs.append(NameValuePair(name=setting["name"], value=setting["value"]))
            
            site_config = SiteConfig(
                app_settings=name_value_pairs,
                linux_fx_version=f"DOCKER|{docker_image}",
                always_on=True
            )
            
            poller = web_client.web_apps.begin_update(
                resource_group,
                app_name,
                {
                    "site_config": site_config
                }
            )
            
            web_app = poller.result()
            print_success(f"Web App '{app_name}' updated successfully.")
        
        return web_app
    except Exception as e:
        print_error(f"Failed to deploy Web App: {e}")
        sys.exit(1)

def bind_custom_domain(credential, subscription_id, resource_group, app_name, domain):
    """Bind a custom domain to the web app."""
    print_header(f"\nBinding custom domain '{domain}' to Web App...")
    
    try:
        web_client = WebSiteManagementClient(credential, subscription_id)
        
        # Check if the domain is already bound
        host_name_bindings = list(web_client.web_apps.list_host_name_bindings(resource_group, app_name))
        for binding in host_name_bindings:
            if binding.name.lower() == domain.lower():
                print_success(f"Custom domain '{domain}' is already bound to the Web App.")
                return True
        
        # Bind the custom domain
        print(f"Binding custom domain '{domain}' to Web App '{app_name}'...")
        
        web_client.web_apps.create_or_update_host_name_binding(
            resource_group,
            app_name,
            domain,
            {
                "host_name_type": "Verified",
                "site_name": app_name
            }
        )
        
        print_success(f"Custom domain '{domain}' bound successfully.")
        
        # Add SSL binding
        print(f"Configuring SSL for '{domain}'...")
        
        web_client.web_apps.create_or_update_host_name_binding(
            resource_group,
            app_name,
            domain,
            {
                "ssl_state": "SniEnabled",
                "host_name_type": "Verified",
                "site_name": app_name
            }
        )
        
        print_success(f"SSL configured for '{domain}'.")
        return True
    except Exception as e:
        print_error(f"Failed to bind custom domain: {e}")
        return False

def main():
    """Main function to deploy the application to Azure App Services."""
    # Configuration
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group = "growth-accelerator-rg"
    location = "westeurope"
    app_name = "growth-accelerator"
    plan_name = f"{app_name}-plan"
    domain = "app.growthaccelerator.nl"
    docker_image = "ghcr.io/bart-wetselaar/growth-accelerator-deployment:latest"
    
    print_header("==== DEPLOYING GROWTH ACCELERATOR STAFFING PLATFORM TO AZURE ====")
    print(f"Subscription ID: {subscription_id}")
    print(f"Resource Group: {resource_group}")
    print(f"Location: {location}")
    print(f"App Name: {app_name}")
    print(f"Domain: {domain}")
    print(f"Docker Image: {docker_image}")
    
    # Get Azure credential
    credential = get_credential()
    
    # Ensure the resource group exists
    ensure_resource_group(
        credential,
        subscription_id,
        resource_group,
        location
    )
    
    # App Service Plan
    app_service_plan = create_app_service_plan(
        credential,
        subscription_id,
        resource_group,
        location,
        plan_name
    )
    
    # Web App deployment
    web_app = deploy_web_app(
        credential,
        subscription_id,
        resource_group,
        location,
        app_name,
        app_service_plan.id,
        docker_image
    )
    
    # Custom domain binding
    bind_custom_domain(
        credential,
        subscription_id,
        resource_group,
        app_name,
        domain
    )
    
    # Print deployment summary
    print_header("\n==== DEPLOYMENT SUMMARY ====")
    print(f"Application Name: {app_name}")
    print(f"Resource Group: {resource_group}")
    print(f"Application URL: https://{domain}")
    
    print_success("\nGrowth Accelerator Staffing Platform deployed successfully!")
    print(f"Azure Portal URL: https://portal.azure.com/#@/resource/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Web/sites/{app_name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())