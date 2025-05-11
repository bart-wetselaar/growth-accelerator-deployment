#!/usr/bin/env python3
"""
Setup GitHub Container Registry for Growth Accelerator Staffing Platform.
This script configures GitHub Container Registry to store and manage Docker images.
"""

import argparse
import json
import os
import re
import requests
import sys
from base64 import b64encode
from getpass import getpass
from datetime import datetime

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

def get_github_token(args):
    """Get GitHub personal access token from args or prompt."""
    token = args.token
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        try:
            token = getpass("Enter your GitHub Personal Access Token: ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit(1)
    
    if not token:
        print_error("GitHub token is required.")
        sys.exit(1)
    
    return token

def get_github_username(token):
    """Get GitHub username from token."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get("https://api.github.com/user", headers=headers)
    
    if response.status_code == 200:
        return response.json()["login"]
    else:
        print_error(f"Failed to get GitHub username: {response.status_code} {response.text}")
        sys.exit(1)

def create_or_update_docker_workflow(token, owner, repo, image_name=None):
    """Create or update GitHub Actions workflow for Docker build and push."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Default image name is the repo name if not provided
    if not image_name:
        image_name = repo.lower()
    
    workflow_path = ".github/workflows/docker-build.yml"
    
    # Check if workflow already exists
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{workflow_path}"
    response = requests.get(url, headers=headers)
    
    workflow_content = f"""name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    paths:
      - 'Dockerfile'
      - '.github/workflows/docker-build.yml'
      - 'docker-entrypoint.sh'
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to the Container registry
        uses: docker/login-action@v2
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
          tags: |
            type=sha,format=long
            type=ref,event=branch
            type=raw,value=latest,enable=${{{{ github.ref == format('refs/heads/{{0}}', 'main') }}}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""
    
    if response.status_code == 200:
        # Update existing workflow
        sha = response.json()["sha"]
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{workflow_path}"
        payload = {
            "message": "Update Docker build workflow",
            "content": b64encode(workflow_content.encode()).decode(),
            "sha": sha
        }
        
        response = requests.put(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print_success(f"Updated GitHub Actions workflow at {workflow_path}")
        else:
            print_error(f"Failed to update workflow: {response.status_code} {response.text}")
            return False
    elif response.status_code == 404:
        # Create new workflow
        
        # First ensure the .github/workflows directory exists
        directory_parts = workflow_path.split('/')
        current_path = ""
        
        for i in range(len(directory_parts) - 1):
            current_path = '/'.join(directory_parts[:i+1])
            check_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{current_path}"
            check_response = requests.get(check_url, headers=headers)
            
            if check_response.status_code == 404:
                # Create directory by creating a .gitkeep file
                create_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{current_path}/.gitkeep"
                create_payload = {
                    "message": f"Create {current_path} directory",
                    "content": b64encode(b"").decode()
                }
                
                create_response = requests.put(create_url, headers=headers, json=create_payload)
                
                if create_response.status_code != 201:
                    print_error(f"Failed to create directory {current_path}: {create_response.status_code} {create_response.text}")
                    return False
                else:
                    print_success(f"Created {current_path} directory")
        
        # Now create the workflow file
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{workflow_path}"
        payload = {
            "message": "Add Docker build workflow",
            "content": b64encode(workflow_content.encode()).decode()
        }
        
        response = requests.put(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            print_success(f"Created GitHub Actions workflow at {workflow_path}")
        else:
            print_error(f"Failed to create workflow: {response.status_code} {response.text}")
            return False
    else:
        print_error(f"Failed to check workflow existence: {response.status_code} {response.text}")
        return False
    
    return True

def enable_github_packages(token, owner, repo):
    """Enable GitHub Packages for the repository."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check repository visibility
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print_error(f"Failed to get repository information: {response.status_code} {response.text}")
        return False
    
    repo_info = response.json()
    is_private = repo_info.get("private", False)
    
    if is_private:
        print_warning("Repository is private. You'll need to use a personal access token with packages:read scope to pull images.")
        
        # Update package visibility to make it accessible
        # Note: This API is still in preview
        headers["Accept"] = "application/vnd.github.package-deletes-preview+json"
        package_url = f"https://api.github.com/orgs/{owner}/packages/container/{repo}/visibility"
        package_payload = {"visibility": "private"}
        
        package_response = requests.patch(package_url, headers=headers, json=package_payload)
        
        if package_response.status_code in (200, 204):
            print_success("Updated package visibility settings")
        else:
            print_warning(f"Could not update package visibility: {package_response.status_code} {package_response.text}")
            print_warning("You may need to manually configure package settings on GitHub")
    else:
        print_success("Repository is public. Docker images will be publicly available.")
    
    return True

def print_usage_instructions(owner, repo_name):
    """Print usage instructions for GitHub Container Registry."""
    print_header("\n==== USAGE INSTRUCTIONS ====")
    
    print(f"\nTo pull the Docker image from the GitHub Container Registry:")
    print(f"docker pull ghcr.io/{owner.lower()}/{repo_name.lower()}:latest")
    
    print(f"\nTo run the Docker container:")
    print(f"docker run -p 5000:5000 ghcr.io/{owner.lower()}/{repo_name.lower()}:latest")
    
    print(f"\nTo use with docker-compose:")
    print("```yaml")
    print("version: '3.8'")
    print("services:")
    print("  app:")
    print(f"    image: ghcr.io/{owner.lower()}/{repo_name.lower()}:latest")
    print("    ports:")
    print("      - '5000:5000'")
    print("    environment:")
    print("      - DATABASE_URL=postgresql://user:password@db:5432/appdb")
    print("    depends_on:")
    print("      - db")
    print("  db:")
    print("    image: postgres:14")
    print("    environment:")
    print("      - POSTGRES_USER=user")
    print("      - POSTGRES_PASSWORD=password")
    print("      - POSTGRES_DB=appdb")
    print("    volumes:")
    print("      - postgres_data:/var/lib/postgresql/data")
    print("volumes:")
    print("  postgres_data:")
    print("```")
    
    print("\nTo use with Azure App Service (container setting):")
    print(f"Container Registry: ghcr.io")
    print(f"Image: {owner.lower()}/{repo_name.lower()}")
    print(f"Tag: latest")
    print(f"Full image URL: ghcr.io/{owner.lower()}/{repo_name.lower()}:latest")

def main():
    parser = argparse.ArgumentParser(description="Setup GitHub Container Registry for Growth Accelerator Staffing Platform")
    parser.add_argument("--token", help="GitHub Personal Access Token with repo and packages scope")
    parser.add_argument("--repo", default="growth-accelerator-deployment", help="GitHub repository name")
    parser.add_argument("--image-name", help="Docker image name (defaults to repo name)")
    args = parser.parse_args()
    
    print_header("==== GITHUB CONTAINER REGISTRY SETUP ====\n")
    
    # Get GitHub token
    token = get_github_token(args)
    
    # Get GitHub username
    username = get_github_username(token)
    print_success(f"Authenticated as GitHub user: {username}")
    
    # Create or update Docker workflow
    success = create_or_update_docker_workflow(token, username, args.repo, args.image_name)
    
    if success:
        # Enable GitHub Packages
        success = enable_github_packages(token, username, args.repo)
    
    if success:
        print_success("GitHub Container Registry setup complete!")
        print_usage_instructions(username, args.repo)
    else:
        print_error("GitHub Container Registry setup failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())