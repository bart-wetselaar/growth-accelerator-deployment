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
    
    az_version = run_command("az --version")
    if not az_version:
        print("Azure CLI is not installed or not in PATH.")
        choice = input("Do you want to install Azure CLI? [y/N]: ").strip().lower()
        if choice in ["y", "yes"]:
            print("Installing Azure CLI...")
            run_command("curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        else:
            print("Azure CLI is required to continue. Please install it and try again.")
            return False
    
    # Check if user is logged in
    account_info = run_command("az account show")
    if not account_info:
        print("You are not logged in to Azure CLI.")
        print("Running 'az login'...")
        login_result = run_command("az login")
        if not login_result:
            print("Failed to login to Azure CLI.")
            return False
        print("Successfully logged in to Azure CLI.")
    else:
        account_data = json.loads(account_info)
        print(f"You are logged in as {account_data.get('user', {}).get('name')} in tenant {account_data.get('tenantId')}")
    
    return True

def select_subscription():
    """Select the subscription to use."""
    print("\nSelecting Azure subscription...")
    
    # List available subscriptions
    subscriptions = run_command("az account list --output json")
    if not subscriptions:
        print("Failed to list Azure subscriptions.")
        return None
    
    subscriptions_data = json.loads(subscriptions)
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
    
    # Let user select a subscription
    while True:
        try:
            choice = int(input(f"Enter the number of the subscription to use [1-{len(subscriptions_data)}]: "))
            if 1 <= choice <= len(subscriptions_data):
                subscription_id = subscriptions_data[choice-1].get("id")
                print(f"Selected subscription: {subscription_id}")
                return subscription_id
            else:
                print(f"Please enter a number between 1 and {len(subscriptions_data)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return None

def create_service_principal(subscription_id):
    """Create a service principal with Contributor role."""
    sp_name = "growth-accelerator-sp"
    
    print(f"\nCreating service principal '{sp_name}' with Contributor role...")
    
    # Create the service principal
    command = f"az ad sp create-for-rbac --name {sp_name} --role Contributor --scopes /subscriptions/{subscription_id} --output json"
    result = run_command(command)
    
    if not result:
        print("Failed to create service principal.")
        return None
    
    try:
        sp_data = json.loads(result)
        print("Service Principal created successfully.")
        
        # Map the returned data to expected format
        credentials = {
            "tenantId": sp_data.get("tenant"),
            "clientId": sp_data.get("appId"),
            "clientSecret": sp_data.get("password"),
            "subscriptionId": subscription_id
        }
        
        return credentials
    except json.JSONDecodeError:
        print("Failed to parse service principal data.")
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