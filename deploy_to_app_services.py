#!/usr/bin/env python3
"""
Direct deployment script to Azure App Services for Growth Accelerator Staffing Platform.
This script deploys the application to Azure App Services using the Azure SDK.
It assumes the domain app.growthaccelerator.nl is already configured.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

# Azure SDK imports
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import Site, SiteConfig, NameValuePair, AppServicePlan
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
from azure.mgmt.rdbms.postgresql.models import ServerForCreate, ServerPropertiesForDefaultCreate, ServerVersion, Sku

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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Deploy Growth Accelerator Staffing Platform to Azure App Services')
    
    # Azure authentication parameters
    parser.add_argument('--tenant-id', required=True, help='Azure Tenant ID')
    parser.add_argument('--subscription-id', required=True, help='Azure Subscription ID')
    parser.add_argument('--client-id', required=True, help='Azure Service Principal Client ID')
    parser.add_argument('--client-secret', required=True, help='Azure Service Principal Client Secret')
    
    # Deployment parameters
    parser.add_argument('--resource-group', required=True, help='Azure Resource Group name')
    parser.add_argument('--location', default='westeurope', help='Azure Region (default: westeurope)')
    parser.add_argument('--app-name', default='growth-accelerator', help='Azure Web App name')
    parser.add_argument('--domain', default='app.growthaccelerator.nl', help='Custom domain name')
    parser.add_argument('--db-server-name', help='Azure PostgreSQL server name (default: <app-name>-db)')
    parser.add_argument('--db-username', default='gadmin', help='PostgreSQL admin username')
    parser.add_argument('--db-password', help='PostgreSQL admin password')
    parser.add_argument('--db-name', default='growth_accelerator_db', help='PostgreSQL database name')
    parser.add_argument('--plan-name', help='App Service Plan name (default: <app-name>-plan)')
    parser.add_argument('--plan-tier', default='P1v2', help='App Service Plan tier (default: P1v2)')
    parser.add_argument('--docker-image', default='ghcr.io/bart-wetselaar/growth-accelerator-deployment:latest', 
                        help='Docker image URL')
    parser.add_argument('--skip-db', action='store_true', help='Skip database creation')
    parser.add_argument('--skip-domain', action='store_true', help='Skip custom domain binding')
    
    # Environment variables
    parser.add_argument('--env-vars', nargs='+', help='Additional environment variables in KEY=VALUE format')
    
    return parser.parse_args()

def get_credential(tenant_id, client_id, client_secret):
    """Get Azure credential object."""
    try:
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        return credential
    except Exception as e:
        print_error(f"Failed to create Azure credential: {str(e)}")
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
        print_error(f"Failed to ensure resource group: {str(e)}")
        sys.exit(1)

def create_postgresql_server(credential, subscription_id, resource_group, location, 
                             server_name, admin_user, admin_password):
    """Create an Azure PostgreSQL server."""
    print_header("\nCreating PostgreSQL server...")
    
    try:
        postgresql_client = PostgreSQLManagementClient(credential, subscription_id)
        
        # Check if the server already exists
        servers = list(postgresql_client.servers.list_by_resource_group(resource_group))
        for server in servers:
            if server.name.lower() == server_name.lower():
                print_success(f"PostgreSQL server '{server_name}' already exists.")
                return server
        
        # Define the server properties
        sku = Sku(name="GP_Gen5_2", tier="GeneralPurpose", capacity=2)
        properties = ServerPropertiesForDefaultCreate(
            administrator_login=admin_user,
            administrator_login_password=admin_password,
            version=ServerVersion.ELEVEN,
            ssl_enforcement="Enabled",
            storage_profile={"storageMB": 51200, "backup_retention_days": 7, "geo_redundant_backup": "Disabled"}
        )
        
        # Create the server
        print(f"Creating PostgreSQL server '{server_name}' in location '{location}'...")
        server_creation = postgresql_client.servers.begin_create(
            resource_group,
            server_name,
            ServerForCreate(
                location=location,
                properties=properties,
                sku=sku
            )
        )
        
        # Wait for the server to be created
        print("Waiting for PostgreSQL server to be created (this may take a few minutes)...")
        server = server_creation.result()
        print_success(f"PostgreSQL server '{server_name}' created successfully.")
        
        # Configure firewall to allow Azure services
        print("Configuring PostgreSQL server firewall to allow Azure services...")
        postgresql_client.firewall_rules.create_or_update(
            resource_group,
            server_name,
            "AllowAllAzureIPs",
            "0.0.0.0",  # Start IP address
            "0.0.0.0"   # End IP address
        )
        print_success("PostgreSQL server firewall configured to allow Azure services.")
        
        # Create the database
        return server
    except Exception as e:
        print_error(f"Failed to create PostgreSQL server: {str(e)}")
        return None

def create_postgresql_database(credential, subscription_id, resource_group, server_name, database_name):
    """Create a PostgreSQL database."""
    print_header("\nCreating PostgreSQL database...")
    
    try:
        postgresql_client = PostgreSQLManagementClient(credential, subscription_id)
        
        # Check if the database already exists
        databases = list(postgresql_client.databases.list_by_server(resource_group, server_name))
        for db in databases:
            if db.name.lower() == database_name.lower():
                print_success(f"PostgreSQL database '{database_name}' already exists.")
                return
        
        # Create the database
        print(f"Creating PostgreSQL database '{database_name}'...")
        postgresql_client.databases.create_or_update(
            resource_group,
            server_name,
            database_name,
            {}
        )
        print_success(f"PostgreSQL database '{database_name}' created successfully.")
    except Exception as e:
        print_error(f"Failed to create PostgreSQL database: {str(e)}")

def create_app_service_plan(credential, subscription_id, resource_group, location, plan_name, tier="P1v2"):
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
        
        # Create the App Service Plan
        print(f"Creating App Service Plan '{plan_name}' in location '{location}'...")
        app_service_plan = web_client.app_service_plans.begin_create_or_update(
            resource_group,
            plan_name,
            AppServicePlan(
                location=location,
                sku={
                    "name": tier,
                    "tier": "PremiumV2" if tier.startswith("P") else "Standard"
                },
                reserved=True  # For Linux
            )
        ).result()
        
        print_success(f"App Service Plan '{plan_name}' created successfully.")
        return app_service_plan
    except Exception as e:
        print_error(f"Failed to create App Service Plan: {str(e)}")
        return None

def deploy_web_app(credential, subscription_id, resource_group, location, app_name, plan_id, 
                   docker_image, database_url, env_vars=None):
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
        
        # Prepare app settings including database connection
        app_settings = [
            NameValuePair(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"),
            NameValuePair(name="DOCKER_REGISTRY_SERVER_URL", value="https://ghcr.io"),
            NameValuePair(name="DOCKER_ENABLE_CI", value="true"),
            NameValuePair(name="DATABASE_URL", value=database_url),
            NameValuePair(name="SESSION_SECRET", value=os.urandom(24).hex()),
            NameValuePair(name="WORKABLE_API_KEY", value=os.environ.get("WORKABLE_API_KEY", "")),
            NameValuePair(name="LINKEDIN_CLIENT_ID", value=os.environ.get("LINKEDIN_CLIENT_ID", "")),
            NameValuePair(name="LINKEDIN_CLIENT_SECRET", value=os.environ.get("LINKEDIN_CLIENT_SECRET", "")),
            NameValuePair(name="SQUARESPACE_API_KEY", value=os.environ.get("SQUARESPACE_API_KEY", ""))
        ]
        
        # Add any additional environment variables
        if env_vars:
            for env_var in env_vars:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    app_settings.append(NameValuePair(name=key, value=value))
        
        if not web_app:
            # Create the web app
            print(f"Creating Web App '{app_name}' in location '{location}'...")
            web_app = web_client.web_apps.begin_create_or_update(
                resource_group,
                app_name,
                Site(
                    location=location,
                    server_farm_id=plan_id,
                    site_config=SiteConfig(
                        app_settings=app_settings,
                        linux_fx_version=f"DOCKER|{docker_image}",
                        always_on=True,
                        health_check_path="/health"
                    )
                )
            ).result()
            print_success(f"Web App '{app_name}' created and configured successfully.")
        else:
            # Update the existing web app
            print(f"Updating Web App '{app_name}'...")
            web_app = web_client.web_apps.begin_update(
                resource_group,
                app_name,
                Site(
                    server_farm_id=plan_id,
                    site_config=SiteConfig(
                        app_settings=app_settings,
                        linux_fx_version=f"DOCKER|{docker_image}",
                        always_on=True,
                        health_check_path="/health"
                    )
                )
            ).result()
            print_success(f"Web App '{app_name}' updated successfully.")
        
        return web_app
    except Exception as e:
        print_error(f"Failed to deploy Web App: {str(e)}")
        return None

def bind_custom_domain(credential, subscription_id, resource_group, app_name, domain):
    """Bind a custom domain to the web app."""
    print_header(f"\nBinding custom domain '{domain}' to Web App...")
    
    try:
        web_client = WebSiteManagementClient(credential, subscription_id)
        
        # Check for domain verification ID
        verification_id = None
        try:
            site_info = web_client.web_apps.get(resource_group, app_name)
            if hasattr(site_info, 'custom_domain_verification_id'):
                verification_id = site_info.custom_domain_verification_id
        except Exception as e:
            print_warning(f"Could not retrieve domain verification ID: {str(e)}")
        
        if verification_id:
            print(f"Domain verification ID: {verification_id}")
            print("Please ensure this verification ID is present in a TXT record for your domain.")
        
        # Check if the domain is already bound
        host_names = web_client.web_apps.get(resource_group, app_name).host_names
        if domain in host_names:
            print_success(f"Custom domain '{domain}' is already bound to the Web App.")
            return True
        
        # Bind the custom domain
        print(f"Binding custom domain '{domain}' to Web App '{app_name}'...")
        web_client.web_apps.create_or_update_host_name_binding(
            resource_group,
            app_name,
            domain,
            {
                "site_name": app_name,
                "host_name_type": "Verified",
                "custom_host_name_dns_record_type": "A"
            }
        )
        print_success(f"Custom domain '{domain}' bound successfully.")
        
        return True
    except Exception as e:
        print_error(f"Failed to bind custom domain: {str(e)}")
        return False

def add_ssl_certificate(credential, subscription_id, resource_group, app_name, domain):
    """Add a free managed SSL certificate to the web app domain."""
    print_header(f"\nConfiguring SSL for custom domain '{domain}'...")
    
    try:
        web_client = WebSiteManagementClient(credential, subscription_id)
        
        # Check if SSL is already enabled
        certificates = list(web_client.certificates.list_by_resource_group(resource_group))
        for cert in certificates:
            subject_name = cert.subject_name
            if subject_name and subject_name.lower() == domain.lower():
                print_success(f"SSL certificate for '{domain}' already exists.")
                return
        
        # Create a free managed certificate
        print(f"Creating managed SSL certificate for '{domain}'...")
        operation = web_client.web_apps.create_or_update_managed_host_name_certificate(
            resource_group,
            app_name,
            domain,
            {
                "host_name": domain,
                "site_name": app_name,
                "server_farm_id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Web/serverfarms/{app_name}-plan"
            }
        )
        
        print_success(f"Managed SSL certificate for '{domain}' requested successfully.")
        print_warning("Note: SSL certificate provisioning may take up to 24 hours to complete.")
    except Exception as e:
        print_error(f"Failed to add SSL certificate: {str(e)}")

def main():
    """Main function to deploy the application to Azure App Services."""
    args = parse_arguments()
    
    # Generate default names if not provided
    if not args.db_server_name:
        args.db_server_name = f"{args.app_name}-db"
    if not args.plan_name:
        args.plan_name = f"{args.app_name}-plan"
    if not args.db_password:
        args.db_password = f"P@ssw0rd{os.urandom(4).hex()}"  # Generate a random password
    
    print_header("==== DEPLOYING GROWTH ACCELERATOR STAFFING PLATFORM TO AZURE ====")
    print(f"Subscription ID: {args.subscription_id}")
    print(f"Resource Group: {args.resource_group}")
    print(f"Location: {args.location}")
    print(f"App Name: {args.app_name}")
    print(f"Domain: {args.domain}")
    print(f"Database Server: {args.db_server_name}")
    print(f"Database Name: {args.db_name}")
    print(f"Docker Image: {args.docker_image}")
    
    # Get Azure credential
    credential = get_credential(
        args.tenant_id,
        args.client_id,
        args.client_secret
    )
    
    # Ensure the resource group exists
    ensure_resource_group(
        credential,
        args.subscription_id,
        args.resource_group,
        args.location
    )
    
    # PostgreSQL server and database
    if not args.skip_db:
        server = create_postgresql_server(
            credential,
            args.subscription_id,
            args.resource_group,
            args.location,
            args.db_server_name,
            args.db_username,
            args.db_password
        )
        
        if server:
            create_postgresql_database(
                credential,
                args.subscription_id,
                args.resource_group,
                args.db_server_name,
                args.db_name
            )
            
            # Construct the database connection string
            # Format: postgresql://username:password@host:port/dbname
            database_url = f"postgresql://{args.db_username}:{args.db_password}@{args.db_server_name}.postgres.database.azure.com:5432/{args.db_name}"
        else:
            print_error("Failed to create or access PostgreSQL server. Deployment cannot continue.")
            return 1
    else:
        print_warning("Skipping database creation as requested.")
        database_url = os.environ.get("DATABASE_URL", "sqlite:///growth_accelerator_staffing.db")
    
    # App Service Plan
    app_service_plan = create_app_service_plan(
        credential,
        args.subscription_id,
        args.resource_group,
        args.location,
        args.plan_name,
        args.plan_tier
    )
    
    if not app_service_plan:
        print_error("Failed to create or access App Service Plan. Deployment cannot continue.")
        return 1
    
    # Web App deployment
    web_app = deploy_web_app(
        credential,
        args.subscription_id,
        args.resource_group,
        args.location,
        args.app_name,
        app_service_plan.id,
        args.docker_image,
        database_url,
        args.env_vars
    )
    
    if not web_app:
        print_error("Failed to deploy Web App. Deployment cannot continue.")
        return 1
    
    # Custom domain binding
    if not args.skip_domain:
        domain_bound = bind_custom_domain(
            credential,
            args.subscription_id,
            args.resource_group,
            args.app_name,
            args.domain
        )
        
        if domain_bound:
            # Add SSL certificate
            add_ssl_certificate(
                credential,
                args.subscription_id,
                args.resource_group,
                args.app_name,
                args.domain
            )
    else:
        print_warning("Skipping custom domain binding as requested.")
    
    # Print deployment summary
    print_header("\n==== DEPLOYMENT SUMMARY ====")
    print(f"Application Name: {args.app_name}")
    print(f"Resource Group: {args.resource_group}")
    print(f"Database Server: {args.db_server_name}")
    print(f"Database Name: {args.db_name}")
    
    app_url = f"https://{args.domain}" if not args.skip_domain else f"https://{args.app_name}.azurewebsites.net"
    print(f"Application URL: {app_url}")
    
    print_success("\nGrowth Accelerator Staffing Platform deployed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())