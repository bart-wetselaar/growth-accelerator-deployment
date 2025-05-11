#!/usr/bin/env python3
"""
Create Azure Service Principal for Growth Accelerator Staffing Platform

This script creates an Azure Service Principal with Contributor role for deploying
the Growth Accelerator Staffing Platform to Azure.
"""

import json
import os
import subprocess
import sys

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
    print(f"{Colors.BLUE}{Colors.BOLD}==== {message} ===={Colors.ENDC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.RED}Error: {message}{Colors.ENDC}")

def run_command(command):
    """Run a shell command and return the output"""
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
        print_error(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr)
        return None

def az_login():
    """Login to Azure"""
    print_header("LOGGING IN TO AZURE")
    print("You'll be prompted to authenticate with Azure...")
    
    # Try to get current account info to check if already logged in
    account_info = run_command("az account show")
    if account_info:
        account_data = json.loads(account_info)
        print_success(f"Already logged in as {account_data.get('user', {}).get('name')} in tenant {account_data.get('tenantId')}")
        return True
    
    # If not logged in, initiate login
    result = run_command("az login")
    if result:
        print_success("Login successful")
        return True
    else:
        print_error("Failed to login to Azure")
        return False

def get_subscription():
    """Get the subscription ID to use"""
    print_header("SELECTING AZURE SUBSCRIPTION")
    
    # List available subscriptions
    subscriptions = run_command("az account list --output json")
    if not subscriptions:
        print_error("Failed to list Azure subscriptions")
        return None
    
    subscriptions_data = json.loads(subscriptions)
    if not subscriptions_data:
        print_error("No subscriptions found. Make sure you have access to an Azure subscription")
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
        print_success(f"Using the only available subscription: {subscription_id}")
        return subscription_id
    
    # Find the default subscription
    default_sub = next((sub for sub in subscriptions_data if sub.get("isDefault")), None)
    if default_sub:
        while True:
            use_default = input(f"Use default subscription '{default_sub.get('name')}' ({default_sub.get('id')})? [Y/n]: ").strip().lower()
            if use_default in ["", "y", "yes"]:
                return default_sub.get("id")
            elif use_default in ["n", "no"]:
                break
            else:
                print("Please answer Y or N")
    
    # Let user select a subscription
    while True:
        try:
            choice = int(input(f"Enter the number of the subscription to use [1-{len(subscriptions_data)}]: "))
            if 1 <= choice <= len(subscriptions_data):
                subscription_id = subscriptions_data[choice-1].get("id")
                print_success(f"Selected subscription: {subscription_id}")
                return subscription_id
            else:
                print(f"Please enter a number between 1 and {len(subscriptions_data)}")
        except ValueError:
            print("Please enter a valid number")

def set_subscription(subscription_id):
    """Set the active subscription"""
    print(f"Setting active subscription to: {subscription_id}")
    result = run_command(f"az account set --subscription {subscription_id}")
    if result is not None:
        print_success("Subscription set successfully")
        return True
    else:
        print_error("Failed to set subscription")
        return False

def create_service_principal(name, subscription_id):
    """Create a service principal with Contributor role"""
    print_header("CREATING SERVICE PRINCIPAL")
    print(f"Creating service principal '{name}' with Contributor role...")
    
    scope = f"/subscriptions/{subscription_id}"
    command = f"az ad sp create-for-rbac --name {name} --role Contributor --scopes {scope} --output json"
    result = run_command(command)
    
    if result:
        try:
            sp_data = json.loads(result)
            print_success("Service Principal created successfully")
            return sp_data
        except json.JSONDecodeError:
            print_error("Failed to parse service principal data")
            return None
    else:
        print_error("Failed to create service principal")
        return None

def save_credentials(sp_data, subscription_id, filename="azure_credentials.json"):
    """Save the credentials to a file"""
    print_header("SAVING CREDENTIALS")
    
    if not sp_data:
        print_error("No service principal data to save")
        return False
    
    # Map the returned data to our expected format
    credentials = {
        "clientId": sp_data.get("appId"),
        "clientSecret": sp_data.get("password"),
        "tenantId": sp_data.get("tenant"),
        "subscriptionId": subscription_id
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    
    try:
        with open(filename, "w") as f:
            json.dump(credentials, f, indent=2)
        print_success(f"Credentials saved to {filename}")
        
        # Print the credentials
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
        print_error(f"Failed to save credentials: {e}")
        return False

def main():
    print_header("AZURE SERVICE PRINCIPAL CREATION")
    
    # Login to Azure
    if not az_login():
        return 1
    
    # Get subscription ID
    subscription_id = get_subscription()
    if not subscription_id:
        return 1
    
    # Set active subscription
    if not set_subscription(subscription_id):
        return 1
    
    # Create service principal
    sp_name = input("Enter a name for the service principal [growth-accelerator-sp]: ").strip() or "growth-accelerator-sp"
    sp_data = create_service_principal(sp_name, subscription_id)
    if not sp_data:
        return 1
    
    # Save credentials
    credentials_file = input("Enter filename to save credentials [azure_credentials.json]: ").strip() or "azure_credentials.json"
    if not save_credentials(sp_data, subscription_id, credentials_file):
        return 1
    
    print_success("Azure Service Principal setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())