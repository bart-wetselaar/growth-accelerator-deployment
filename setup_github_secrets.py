#!/usr/bin/env python3
"""
Script to set up GitHub repository secrets for GitHub Actions deployment workflow
to Azure App Service.

This script sets up the necessary secrets in a GitHub repository for the
Growth Accelerator Staffing Platform to be deployed using GitHub Actions.

Prerequisites:
- GitHub Personal Access Token with repo permissions
- Azure Service Principal with Contributor permissions
"""

import os
import sys
import json
import getpass
import argparse
import subprocess
from base64 import b64encode
from nacl import encoding, public

try:
    import github
    from github.GithubException import GithubException
except ImportError:
    print("PyGithub package not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyGithub", "PyNaCl"])
    import github
    from github.GithubException import GithubException

def encrypt_secret(public_key, secret_value):
    """Encrypt a secret using the repository's public key."""
    public_key_decoded = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_decoded)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def get_azure_credentials():
    """Get Azure Service Principal credentials."""
    print("\nCreating Azure Service Principal for GitHub Actions...")
    print("This will create a service principal with Contributor role on your subscription.\n")
    
    subscription_id = input("Azure Subscription ID: ")
    sp_name = input("Service Principal Name [github-actions-growth-accelerator]: ") or "github-actions-growth-accelerator"
    
    print("\nCreating service principal...")
    result = subprocess.run(
        ["az", "ad", "sp", "create-for-rbac", 
         "--name", sp_name,
         "--role", "Contributor",
         "--scopes", f"/subscriptions/{subscription_id}",
         "--sdk-auth"],
        check=True,
        capture_output=True,
        text=True
    )
    
    return result.stdout.strip()

def main():
    """Main function to set up GitHub repository secrets."""
    parser = argparse.ArgumentParser(description="Set up GitHub repository secrets for Azure deployment.")
    parser.add_argument("--repo", required=True, help="GitHub repository name (format: owner/repo)")
    parser.add_argument("--token", help="GitHub Personal Access Token (if not provided, will prompt)")
    args = parser.parse_args()
    
    # Get GitHub token
    github_token = args.token
    if not github_token:
        github_token = getpass.getpass("GitHub Personal Access Token: ")
        
    if not github_token:
        print("Error: GitHub token is required")
        sys.exit(1)
    
    # Connect to GitHub
    g = github.Github(github_token)
    try:
        repo = g.get_repo(args.repo)
        print(f"Connected to repository: {repo.full_name}")
    except GithubException as e:
        print(f"Error: Unable to access repository {args.repo}. {e}")
        sys.exit(1)
    
    # Get repository public key for encrypting secrets
    try:
        public_key = repo.get_public_key()
    except GithubException as e:
        print(f"Error: Unable to get repository public key. {e}")
        sys.exit(1)
    
    # Get Azure credentials
    try:
        azure_credentials = get_azure_credentials()
    except subprocess.CalledProcessError as e:
        print(f"Error creating Azure Service Principal: {e.stderr}")
        print("Make sure you're logged in to Azure CLI with 'az login'")
        sys.exit(1)
    
    # Parse Azure credentials
    try:
        azure_creds_json = json.loads(azure_credentials)
    except json.JSONDecodeError:
        print("Error: Unable to parse Azure credentials")
        sys.exit(1)
    
    # Get App Service info
    print("\nPlease provide Azure App Service information:")
    azure_resource_group = input("Azure Resource Group Name: ")
    azure_app_name = input("Azure App Service Name: ")
    
    # Get API keys and database URL
    print("\nPlease provide API keys and database connection string:")
    workable_api_key = getpass.getpass("Workable API Key: ")
    linkedin_client_id = getpass.getpass("LinkedIn Client ID: ")
    linkedin_client_secret = getpass.getpass("LinkedIn Client Secret: ")
    squarespace_api_key = getpass.getpass("Squarespace API Key: ")
    database_url = getpass.getpass("Database URL: ")
    session_secret = getpass.getpass("Session Secret (leave empty to generate a new one): ") or os.urandom(24).hex()
    
    # Create secrets
    secrets = {
        "AZURE_CREDENTIALS": azure_credentials,
        "AZURE_RESOURCE_GROUP": azure_resource_group,
        "AZURE_APP_NAME": azure_app_name,
        "WORKABLE_API_KEY": workable_api_key,
        "LINKEDIN_CLIENT_ID": linkedin_client_id,
        "LINKEDIN_CLIENT_SECRET": linkedin_client_secret,
        "SQUARESPACE_API_KEY": squarespace_api_key,
        "DATABASE_URL": database_url,
        "SESSION_SECRET": session_secret
    }
    
    # Set secrets in repository
    print("\nSetting up GitHub repository secrets...")
    for name, value in secrets.items():
        if not value:
            print(f"Skipping empty secret: {name}")
            continue
            
        try:
            encrypted_value = encrypt_secret(public_key.key, value)
            repo.create_secret(name, encrypted_value)
            print(f"✓ Secret {name} created successfully")
        except GithubException as e:
            print(f"Error setting secret {name}: {e}")
    
    print("\nSecrets setup complete. Your GitHub Actions workflow is now ready to deploy to Azure.")
    print("Push your code to the repository to trigger the deployment action.")

if __name__ == "__main__":
    main()