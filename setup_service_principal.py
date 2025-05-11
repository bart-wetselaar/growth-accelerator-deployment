#!/usr/bin/env python3
"""
Automatic setup of Azure Service Principal for Growth Accelerator Staffing Platform.
This script uses the Azure CLI to create a service principal with the necessary permissions.
"""

import json
import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(e.stderr)
        return None

def check_azure_cli():
    """Check if Azure CLI is installed and user is logged in."""
    # Try to get current account information
    print("Checking Azure CLI installation and login status...")
    
    try:
        from azure.cli.core import get_default_cli
        print("Azure CLI Python package is installed.")
    except ImportError:
        print("Azure CLI Python package is not installed.")
        print("Please run: pip install azure-cli")
        return False
    
    # Check if user is logged in through API
    try:
        from azure.identity import AzureCliCredential
        credential = AzureCliCredential()
        # Try to get a token to check if logged in
        token = credential.get_token("https://management.azure.com/.default")
        print("You are already logged in to Azure CLI.")
        return True
    except Exception as e:
        print(f"Not logged in to Azure CLI: {str(e)}")
        
        # Try to login
        print("Attempting to login...")
        print("NOTE: A browser window should open. If it doesn't, please visit the URL shown in the output.")
        print("If running in a remote environment without a browser, use 'az login --use-device-code' manually.")
        
        try:
            from azure.cli.core import get_default_cli
            exit_code = get_default_cli().invoke(['login'])
            if exit_code == 0:
                print("Successfully logged in to Azure CLI.")
                return True
            else:
                print("Failed to login to Azure CLI.")
                print("Please run 'az login' manually and then run this script again.")
                return False
        except Exception as login_error:
            print(f"Error during login: {login_error}")
            print("Please run 'az login' manually and then run this script again.")
            return False

def select_subscription():
    """Select the subscription to use."""
    print("\nSelecting Azure subscription...")
    
    try:
        from azure.cli.core import get_default_cli
        # Get subscriptions using Azure CLI Python SDK
        import io
        import contextlib
        
        # Capture output of CLI command
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            get_default_cli().invoke(['account', 'list'])
            output = buf.getvalue()
        
        # Extract JSON part from output
        import re
        json_match = re.search(r'(\[.*\])', output, re.DOTALL)
        if not json_match:
            print("Failed to parse subscription list.")
            return None
            
        subscriptions_json = json_match.group(1)
        subscriptions_data = json.loads(subscriptions_json)
        
        if not subscriptions_data:
            print("No subscriptions found. Make sure you have access to an Azure subscription.")
            return None
        
        # Display available subscriptions
        print("Available subscriptions:")
        for idx, sub in enumerate(subscriptions_data, 1):
            state = "ACTIVE" if sub.get("state") == "Enabled" else "DISABLED"
            is_default = " (Default)" if sub.get("isDefault") else ""
            print(f"{idx}. {sub.get('name')} - {sub.get('id')} [{state}]{is_default}")
        
        # If only one subscription, use it automatically
        if len(subscriptions_data) == 1:
            subscription_id = subscriptions_data[0].get("id")
            print(f"Using the only available subscription: {subscription_id}")
            return subscription_id
        
        # Find the default subscription
        default_sub = next((sub for sub in subscriptions_data if sub.get("isDefault")), None)
        if default_sub:
            subscription_id = default_sub.get("id")
            print(f"Using default subscription: {subscription_id}")
            return subscription_id
            
        # If we get here, we need to select a subscription
        # In non-interactive mode, just use the first one
        subscription_id = subscriptions_data[0].get("id")
        print(f"Automatically selecting first subscription: {subscription_id}")
        return subscription_id
        
    except Exception as e:
        print(f"Error selecting subscription: {str(e)}")
        return None

def create_service_principal(subscription_id):
    """Create a service principal with Contributor role."""
    sp_name = "growth-accelerator-sp"
    
    print(f"\nCreating service principal '{sp_name}' with Contributor role...")
    
    try:
        # Create using SDK directly
        from azure.cli.core import get_default_cli
        import io
        import contextlib
        
        # Capture output of CLI command
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            result = get_default_cli().invoke(['ad', 'sp', 'create-for-rbac', 
                                      '--name', sp_name, 
                                      '--role', 'Contributor', 
                                      '--scopes', f'/subscriptions/{subscription_id}'])
            output = buf.getvalue()
        
        if result != 0:
            print(f"Failed to create service principal. Exit code: {result}")
            print(f"Output: {output}")
            return None
        
        # Extract JSON data from output
        import re
        json_match = re.search(r'({.*})', output, re.DOTALL)
        if not json_match:
            print("Failed to parse service principal data.")
            return None
            
        sp_json = json_match.group(1)
        sp_data = json.loads(sp_json)
        
        print("Service Principal created successfully.")
        
        # Map the returned data to expected format
        credentials = {
            "tenantId": sp_data.get("tenant"),
            "clientId": sp_data.get("appId"),
            "clientSecret": sp_data.get("password"),
            "subscriptionId": subscription_id
        }
        
        return credentials
    except Exception as e:
        print(f"Error creating service principal: {str(e)}")
        return None

def save_credentials(credentials, filename="azure_credentials.json"):
    """Save the credentials to a file."""
    print(f"\nSaving credentials to {filename}...")
    
    try:
        with open(filename, "w") as f:
            json.dump(credentials, f, indent=2)
        
        print(f"Credentials saved to {filename}")
        
        # Make the file readable only by the current user
        os.chmod(filename, 0o600)
        
        print("\nAzure Service Principal Credentials:")
        print(f"Tenant ID:       {credentials['tenantId']}")
        print(f"Client ID:       {credentials['clientId']}")
        print(f"Client Secret:   {credentials['clientSecret']}")
        print(f"Subscription ID: {credentials['subscriptionId']}")
        
        print("\nYou can use these credentials with the Azure deployment script:")
        print(f"python deploy_to_azure_simplified.py \\")
        print(f"  --tenant-id \"{credentials['tenantId']}\" \\")
        print(f"  --client-id \"{credentials['clientId']}\" \\")
        print(f"  --client-secret \"{credentials['clientSecret']}\" \\")
        print(f"  --subscription-id \"{credentials['subscriptionId']}\" \\")
        print(f"  # ... other parameters")
        
        return True
    except Exception as e:
        print(f"Failed to save credentials: {e}")
        return False

def main():
    print("==== AZURE SERVICE PRINCIPAL CREATION ====\n")
    
    # Check Azure CLI installation and login
    if not check_azure_cli():
        return 1
    
    # Select subscription
    subscription_id = select_subscription()
    if not subscription_id:
        return 1
    
    # Set active subscription
    print(f"Setting active subscription to: {subscription_id}")
    result = run_command(f"az account set --subscription {subscription_id}")
    if result is None:
        print("Failed to set subscription.")
        return 1
    
    # Create service principal
    credentials = create_service_principal(subscription_id)
    if not credentials:
        return 1
    
    # Save credentials
    if not save_credentials(credentials):
        return 1
    
    print("\n==== AZURE SERVICE PRINCIPAL SETUP COMPLETED SUCCESSFULLY ====")
    return 0

if __name__ == "__main__":
    sys.exit(main())