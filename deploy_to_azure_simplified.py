#!/usr/bin/env python3
"""
Simplified Azure Deployment Script using Azure SDK for Python
This script deploys the Growth Accelerator Staffing Platform to Azure App Service.
"""

import os
import sys
import json
import time
import uuid
import getpass
from datetime import datetime

try:
    from azure.identity import ClientSecretCredential
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.web import WebSiteManagementClient
    from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
    from azure.core.exceptions import HttpResponseError
except ImportError:
    print("Azure SDK packages not found. Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "azure-identity", "azure-mgmt-resource", "azure-mgmt-web",
                          "azure-mgmt-rdbms"])
    print("Packages installed. Please run the script again.")
    sys.exit(0)

# Color output for terminal
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}==== {message} ===={Colors.ENDC}\n")

def print_success(message):
    print(f"{Colors.GREEN}{Colors.BOLD}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def deploy_to_azure():
    """Deploy Growth Accelerator Staffing Platform to Azure"""
    print_header("GROWTH ACCELERATOR STAFFING PLATFORM DEPLOYMENT")
    print("This script will deploy the application to Azure App Service.")
    
    # Get Azure credentials
    print_header("AZURE AUTHENTICATION")
    print("Please enter your Azure service principal credentials.")
    
    tenant_id = input("Azure Tenant ID: ")
    client_id = input("Azure Client ID: ")
    client_secret = getpass.getpass("Azure Client Secret: ")
    subscription_id = input("Azure Subscription ID: ")
    
    try:
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        print_success("Authentication successful")
    except Exception as e:
        print_error(f"Authentication failed: {str(e)}")
        sys.exit(1)
    
    # Initialize Azure clients
    resource_client = ResourceManagementClient(credential, subscription_id)
    web_client = WebSiteManagementClient(credential, subscription_id)
    postgresql_client = PostgreSQLManagementClient(credential, subscription_id)
    
    # Get deployment details
    print_header("DEPLOYMENT CONFIGURATION")
    resource_group_name = input("Resource Group Name [growth-accelerator-rg]: ") or "growth-accelerator-rg"
    location = input("Location [westeurope]: ") or "westeurope"
    app_name = input("App Name [growth-accelerator-staffing]: ") or "growth-accelerator-staffing"
    custom_domain = input("Custom Domain [app.growthaccelerator.nl]: ") or "app.growthaccelerator.nl"
    
    # Get API keys and secrets
    print_header("API KEYS AND SECRETS")
    print("These keys will be securely stored in Azure App Settings.")
    workable_api_key = getpass.getpass("Workable API Key: ")
    linkedin_client_id = getpass.getpass("LinkedIn Client ID: ")
    linkedin_client_secret = getpass.getpass("LinkedIn Client Secret: ")
    squarespace_api_key = getpass.getpass("Squarespace API Key: ")
    
    # Generate a session secret if not provided
    session_secret = getpass.getpass("Session Secret (leave empty to generate): ") or str(uuid.uuid4())
    
    # Get container registry details
    print_header("CONTAINER REGISTRY")
    print("GitHub Container Registry (ghcr.io) credentials")
    github_username = input("GitHub Username: ")
    github_token = getpass.getpass("GitHub Personal Access Token: ")
    container_image = input(f"Container Image [ghcr.io/{github_username}/{app_name}:latest]: ") or f"ghcr.io/{github_username}/{app_name}:latest"
    
    # Get database configuration
    print_header("DATABASE CONFIGURATION")
    db_server_name = input(f"Database Server Name [{app_name}-db]: ") or f"{app_name}-db"
    db_name = input("Database Name [growth_accelerator]: ") or "growth_accelerator"
    db_admin_user = input("Database Admin Username [dbadmin]: ") or "dbadmin"
    db_admin_password = getpass.getpass("Database Admin Password: ")
    
    try:
        # Create or update resource group
        print_header("CREATING/UPDATING RESOURCE GROUP")
        resource_client.resource_groups.create_or_update(
            resource_group_name,
            {"location": location}
        )
        print_success(f"Resource group '{resource_group_name}' is ready")
        
        # Create PostgreSQL server
        print_header("CREATING POSTGRESQL SERVER")
        print(f"Creating PostgreSQL server '{db_server_name}'...")
        
        # Define PostgreSQL server parameters
        postgres_parameters = {
            "location": location,
            "properties": {
                "administrator_login": db_admin_user,
                "administrator_login_password": db_admin_password,
                "version": "12",
                "ssl_enforcement": "Enabled",
                "minimal_tls_version": "TLS1_2",
                "storage_profile": {
                    "storage_mb": 51200,
                    "backup_retention_days": 7,
                    "geo_redundant_backup": "Disabled",
                    "storage_autogrow": "Enabled"
                }
            },
            "sku": {
                "name": "GP_Gen5_2",
                "tier": "GeneralPurpose",
                "capacity": 2,
                "family": "Gen5"
            }
        }
        
        try:
            # Check if server exists first
            try:
                postgresql_client.servers.get(resource_group_name, db_server_name)
                print_warning(f"PostgreSQL server '{db_server_name}' already exists")
                server_exists = True
            except:
                server_exists = False
            
            if not server_exists:
                postgresql_poller = postgresql_client.servers.begin_create(
                    resource_group_name,
                    db_server_name,
                    postgres_parameters
                )
                server = postgresql_poller.result()
                print_success(f"PostgreSQL server '{db_server_name}' created")
            
            # Configure firewall to allow Azure services
            postgresql_client.firewall_rules.create_or_update(
                resource_group_name,
                db_server_name,
                "AllowAllAzureIPs",
                {
                    "start_ip_address": "0.0.0.0",
                    "end_ip_address": "0.0.0.0"
                }
            )
            print_success("Firewall rule created")
            
            # Create database
            postgresql_client.databases.create_or_update(
                resource_group_name,
                db_server_name,
                db_name,
                {
                    "charset": "utf8",
                    "collation": "en_US.utf8"
                }
            )
            print_success(f"Database '{db_name}' created")
            
        except Exception as e:
            print_error(f"Error with PostgreSQL setup: {str(e)}")
            sys.exit(1)
        
        # Create App Service Plan
        print_header("CREATING APP SERVICE PLAN")
        app_service_plan_name = f"{app_name}-plan"
        print(f"Creating App Service Plan '{app_service_plan_name}'...")
        
        app_service_plan_parameters = {
            "location": location,
            "sku": {"name": "P1v2", "tier": "PremiumV2"},
            "reserved": True,  # For Linux
            "kind": "linux"
        }
        
        try:
            # Check if App Service Plan exists
            try:
                web_client.app_service_plans.get(resource_group_name, app_service_plan_name)
                print_warning(f"App Service Plan '{app_service_plan_name}' already exists")
                app_service_plan_exists = True
            except:
                app_service_plan_exists = False
                
            if not app_service_plan_exists:
                app_service_plan_poller = web_client.app_service_plans.begin_create_or_update(
                    resource_group_name,
                    app_service_plan_name,
                    app_service_plan_parameters
                )
                app_service_plan = app_service_plan_poller.result()
                print_success(f"App Service Plan '{app_service_plan_name}' created")
            else:
                app_service_plan = web_client.app_service_plans.get(
                    resource_group_name, 
                    app_service_plan_name
                )
                
        except Exception as e:
            print_error(f"Error creating App Service Plan: {str(e)}")
            sys.exit(1)
        
        # Create Web App
        print_header("CREATING WEB APP")
        print(f"Creating Web App '{app_name}'...")
        
        # Database connection string
        db_connection_string = f"postgresql://{db_admin_user}:{db_admin_password}@{db_server_name}.postgres.database.azure.com:5432/{db_name}?sslmode=require"
        
        # Web app configuration
        web_app_parameters = {
            "location": location,
            "server_farm_id": app_service_plan.id,
            "site_config": {
                "linux_fx_version": f"DOCKER|{container_image}",
                "http20_enabled": True,
                "min_tls_version": "1.2",
                "ftps_state": "Disabled",
                "health_check_path": "/health",
                "app_settings": [
                    {"name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE", "value": "false"},
                    {"name": "WEBSITE_HOSTNAME", "value": custom_domain},
                    {"name": "DOCKER_REGISTRY_SERVER_URL", "value": "https://ghcr.io"},
                    {"name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": github_username},
                    {"name": "DOCKER_REGISTRY_SERVER_PASSWORD", "value": github_token},
                    {"name": "DATABASE_URL", "value": db_connection_string},
                    {"name": "WORKABLE_API_KEY", "value": workable_api_key},
                    {"name": "LINKEDIN_CLIENT_ID", "value": linkedin_client_id},
                    {"name": "LINKEDIN_CLIENT_SECRET", "value": linkedin_client_secret},
                    {"name": "SQUARESPACE_API_KEY", "value": squarespace_api_key},
                    {"name": "SESSION_SECRET", "value": session_secret},
                    {"name": "PORT", "value": "8000"},
                    {"name": "WEBSITES_PORT", "value": "8000"},
                    {"name": "WORKERS", "value": "4"},
                    {"name": "TIMEOUT", "value": "120"}
                ]
            },
            "https_only": True
        }
        
        try:
            # Check if Web App exists
            try:
                web_client.web_apps.get(resource_group_name, app_name)
                print_warning(f"Web App '{app_name}' already exists")
                web_app_exists = True
            except:
                web_app_exists = False
                
            if not web_app_exists:
                web_app_poller = web_client.web_apps.begin_create_or_update(
                    resource_group_name,
                    app_name,
                    web_app_parameters
                )
                web_app = web_app_poller.result()
                print_success(f"Web App '{app_name}' created")
            else:
                # Update the existing web app
                web_app_poller = web_client.web_apps.begin_update(
                    resource_group_name,
                    app_name,
                    {
                        "site_config": web_app_parameters["site_config"]
                    }
                )
                web_app = web_app_poller.result()
                print_success(f"Web App '{app_name}' updated")
                
            # Get domain verification ID
            web_app_details = web_client.web_apps.get(resource_group_name, app_name)
            verification_id = web_app_details.custom_domain_verification_id
            
        except Exception as e:
            print_error(f"Error with Web App setup: {str(e)}")
            sys.exit(1)
            
        # Print deployment summary
        print_header("DEPLOYMENT SUMMARY")
        print(f"Resource Group: {resource_group_name}")
        print(f"Database Server: {db_server_name}.postgres.database.azure.com")
        print(f"Database Name: {db_name}")
        print(f"Web App URL: https://{app_name}.azurewebsites.net")
        print(f"Custom Domain: https://{custom_domain}")
        print(f"Domain Verification ID: {verification_id}")
        
        print("\nDNS Configuration Required:")
        print(f"1. TXT Record: asuid.{custom_domain} -> {verification_id}")
        print(f"2. CNAME Record: {custom_domain} -> {app_name}.azurewebsites.net")
        
        print("\nNext Steps:")
        print("1. Configure DNS records as shown above")
        print("2. Add custom domain in Azure Portal (App Service > Custom domains)")
        print("3. Set up SSL/TLS binding")
        print("4. Verify the application is working")
        
    except Exception as e:
        print_error(f"Deployment error: {str(e)}")
        sys.exit(1)
        
    return 0

def deploy_with_args(args):
    """Deploy with command-line arguments"""
    print_header("GROWTH ACCELERATOR STAFFING PLATFORM DEPLOYMENT")
    print("Deploying with provided command-line arguments...")
    
    try:
        # Authentication
        credential = ClientSecretCredential(
            tenant_id=args.tenant_id,
            client_id=args.client_id,
            client_secret=args.client_secret
        )
        print_success("Authentication successful")
    except Exception as e:
        print_error(f"Authentication failed: {str(e)}")
        return 1
    
    # Initialize Azure clients
    resource_client = ResourceManagementClient(credential, args.subscription_id)
    web_client = WebSiteManagementClient(credential, args.subscription_id)
    postgresql_client = PostgreSQLManagementClient(credential, args.subscription_id)
    
    try:
        # Create or update resource group
        print_header("CREATING/UPDATING RESOURCE GROUP")
        resource_client.resource_groups.create_or_update(
            args.resource_group,
            {"location": args.location}
        )
        print_success(f"Resource group '{args.resource_group}' is ready")
        
        # Create PostgreSQL server
        print_header("CREATING POSTGRESQL SERVER")
        print(f"Creating PostgreSQL server '{args.db_server}'...")
        
        # Define PostgreSQL server parameters
        postgres_parameters = {
            "location": args.location,
            "properties": {
                "administrator_login": args.db_admin,
                "administrator_login_password": args.db_password,
                "version": "12",
                "ssl_enforcement": "Enabled",
                "minimal_tls_version": "TLS1_2",
                "storage_profile": {
                    "storage_mb": 51200,
                    "backup_retention_days": 7,
                    "geo_redundant_backup": "Disabled",
                    "storage_autogrow": "Enabled"
                }
            },
            "sku": {
                "name": "GP_Gen5_2",
                "tier": "GeneralPurpose",
                "capacity": 2,
                "family": "Gen5"
            }
        }
        
        try:
            # Check if server exists first
            try:
                postgresql_client.servers.get(args.resource_group, args.db_server)
                print_warning(f"PostgreSQL server '{args.db_server}' already exists")
                server_exists = True
            except:
                server_exists = False
            
            if not server_exists:
                postgresql_poller = postgresql_client.servers.begin_create(
                    args.resource_group,
                    args.db_server,
                    postgres_parameters
                )
                server = postgresql_poller.result()
                print_success(f"PostgreSQL server '{args.db_server}' created")
            
            # Configure firewall to allow Azure services
            postgresql_client.firewall_rules.create_or_update(
                args.resource_group,
                args.db_server,
                "AllowAllAzureIPs",
                {
                    "start_ip_address": "0.0.0.0",
                    "end_ip_address": "0.0.0.0"
                }
            )
            print_success("Firewall rule created")
            
            # Create database
            postgresql_client.databases.create_or_update(
                args.resource_group,
                args.db_server,
                args.db_name,
                {
                    "charset": "utf8",
                    "collation": "en_US.utf8"
                }
            )
            print_success(f"Database '{args.db_name}' created")
            
        except Exception as e:
            print_error(f"Error with PostgreSQL setup: {str(e)}")
            return 1
        
        # Create App Service Plan
        print_header("CREATING APP SERVICE PLAN")
        app_service_plan_name = f"{args.app_name}-plan"
        print(f"Creating App Service Plan '{app_service_plan_name}'...")
        
        app_service_plan_parameters = {
            "location": args.location,
            "sku": {"name": "P1v2", "tier": "PremiumV2"},
            "reserved": True,  # For Linux
            "kind": "linux"
        }
        
        try:
            # Check if App Service Plan exists
            try:
                web_client.app_service_plans.get(args.resource_group, app_service_plan_name)
                print_warning(f"App Service Plan '{app_service_plan_name}' already exists")
                app_service_plan_exists = True
            except:
                app_service_plan_exists = False
                
            if not app_service_plan_exists:
                app_service_plan_poller = web_client.app_service_plans.begin_create_or_update(
                    args.resource_group,
                    app_service_plan_name,
                    app_service_plan_parameters
                )
                app_service_plan = app_service_plan_poller.result()
                print_success(f"App Service Plan '{app_service_plan_name}' created")
            else:
                app_service_plan = web_client.app_service_plans.get(
                    args.resource_group, 
                    app_service_plan_name
                )
                
        except Exception as e:
            print_error(f"Error creating App Service Plan: {str(e)}")
            return 1
        
        # Create Web App
        print_header("CREATING WEB APP")
        print(f"Creating Web App '{args.app_name}'...")
        
        # Database connection string
        db_connection_string = f"postgresql://{args.db_admin}:{args.db_password}@{args.db_server}.postgres.database.azure.com:5432/{args.db_name}?sslmode=require"
        
        # Session secret
        session_secret = args.session_secret or str(uuid.uuid4())
        
        # Web app configuration
        web_app_parameters = {
            "location": args.location,
            "server_farm_id": app_service_plan.id,
            "site_config": {
                "linux_fx_version": f"DOCKER|{args.container_image}",
                "http20_enabled": True,
                "min_tls_version": "1.2",
                "ftps_state": "Disabled",
                "health_check_path": "/health",
                "app_settings": [
                    {"name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE", "value": "false"},
                    {"name": "WEBSITE_HOSTNAME", "value": args.custom_domain},
                    {"name": "DOCKER_REGISTRY_SERVER_URL", "value": "https://ghcr.io"},
                    {"name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": args.github_username},
                    {"name": "DOCKER_REGISTRY_SERVER_PASSWORD", "value": args.github_token},
                    {"name": "DATABASE_URL", "value": db_connection_string},
                    {"name": "WORKABLE_API_KEY", "value": args.workable_api_key},
                    {"name": "LINKEDIN_CLIENT_ID", "value": args.linkedin_client_id},
                    {"name": "LINKEDIN_CLIENT_SECRET", "value": args.linkedin_client_secret},
                    {"name": "SQUARESPACE_API_KEY", "value": args.squarespace_api_key},
                    {"name": "SESSION_SECRET", "value": session_secret},
                    {"name": "PORT", "value": "8000"},
                    {"name": "WEBSITES_PORT", "value": "8000"},
                    {"name": "WORKERS", "value": "4"},
                    {"name": "TIMEOUT", "value": "120"}
                ]
            },
            "https_only": True
        }
        
        try:
            # Check if Web App exists
            try:
                web_client.web_apps.get(args.resource_group, args.app_name)
                print_warning(f"Web App '{args.app_name}' already exists")
                web_app_exists = True
            except:
                web_app_exists = False
                
            if not web_app_exists:
                web_app_poller = web_client.web_apps.begin_create_or_update(
                    args.resource_group,
                    args.app_name,
                    web_app_parameters
                )
                web_app = web_app_poller.result()
                print_success(f"Web App '{args.app_name}' created")
            else:
                # Update the existing web app
                web_app_poller = web_client.web_apps.begin_update(
                    args.resource_group,
                    args.app_name,
                    {
                        "site_config": web_app_parameters["site_config"]
                    }
                )
                web_app = web_app_poller.result()
                print_success(f"Web App '{args.app_name}' updated")
                
            # Get domain verification ID
            web_app_details = web_client.web_apps.get(args.resource_group, args.app_name)
            verification_id = web_app_details.custom_domain_verification_id
            
        except Exception as e:
            print_error(f"Error with Web App setup: {str(e)}")
            return 1
            
        # Print deployment summary
        print_header("DEPLOYMENT SUMMARY")
        print(f"Resource Group: {args.resource_group}")
        print(f"Database Server: {args.db_server}.postgres.database.azure.com")
        print(f"Database Name: {args.db_name}")
        print(f"Web App URL: https://{args.app_name}.azurewebsites.net")
        print(f"Custom Domain: https://{args.custom_domain}")
        print(f"Domain Verification ID: {verification_id}")
        
        print("\nDNS Configuration Required:")
        print(f"1. TXT Record: asuid.{args.custom_domain} -> {verification_id}")
        print(f"2. CNAME Record: {args.custom_domain} -> {args.app_name}.azurewebsites.net")
        
        print("\nNext Steps:")
        print("1. Configure DNS records as shown above")
        print("2. Add custom domain in Azure Portal (App Service > Custom domains)")
        print("3. Set up SSL/TLS binding")
        print("4. Verify the application is working")
        
    except Exception as e:
        print_error(f"Deployment error: {str(e)}")
        return 1
        
    return 0
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy Growth Accelerator Staffing Platform to Azure")
    
    # Azure authentication
    parser.add_argument("--tenant-id", required=True, help="Azure Tenant ID")
    parser.add_argument("--client-id", required=True, help="Azure Client ID")
    parser.add_argument("--client-secret", required=True, help="Azure Client Secret")
    parser.add_argument("--subscription-id", required=True, help="Azure Subscription ID")
    
    # Resource configuration
    parser.add_argument("--resource-group", default="growth-accelerator-rg", help="Resource Group Name")
    parser.add_argument("--location", default="westeurope", help="Azure Region (e.g., westeurope)")
    parser.add_argument("--app-name", default="growth-accelerator-staffing", help="App Service Name")
    parser.add_argument("--custom-domain", default="app.growthaccelerator.nl", help="Custom Domain")
    
    # Database configuration
    parser.add_argument("--db-server", help="Database Server Name (default: {app-name}-db)")
    parser.add_argument("--db-name", default="growth_accelerator", help="Database Name")
    parser.add_argument("--db-admin", default="dbadmin", help="Database Admin Username")
    parser.add_argument("--db-password", required=True, help="Database Admin Password")
    
    # Container configuration
    parser.add_argument("--github-username", required=True, help="GitHub Username")
    parser.add_argument("--github-token", required=True, help="GitHub Personal Access Token")
    parser.add_argument("--container-image", help="Container Image (default: ghcr.io/{github-username}/{app-name}:latest)")
    
    # API keys and secrets
    parser.add_argument("--workable-api-key", required=True, help="Workable API Key")
    parser.add_argument("--linkedin-client-id", required=True, help="LinkedIn Client ID")
    parser.add_argument("--linkedin-client-secret", required=True, help="LinkedIn Client Secret")
    parser.add_argument("--squarespace-api-key", required=True, help="Squarespace API Key")
    parser.add_argument("--session-secret", help="Session Secret (generated if not provided)")
    
    args = parser.parse_args()
    
    # Set default values that depend on other arguments
    if not args.db_server:
        args.db_server = f"{args.app_name}-db"
    if not args.container_image:
        args.container_image = f"ghcr.io/{args.github_username}/{args.app_name}:latest"
    
    # Check for interactive mode
    if len(sys.argv) == 1:
        # If no args provided, use the interactive mode
        sys.exit(deploy_to_azure())
    else:
        # Otherwise use the command-line arguments
        sys.exit(deploy_with_args(args))