#!/usr/bin/env python3
"""
Setup GitHub Container Registry and Push Docker Image

This script:
1. Authenticates with GitHub
2. Creates a Personal Access Token with package permissions if needed
3. Builds and pushes the Docker image to GitHub Container Registry
"""

import argparse
import base64
import getpass
import json
import os
import subprocess
import sys
import requests
from typing import Dict, List, Optional, Tuple

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

def run_command(command: str) -> Optional[str]:
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

def get_github_username() -> str:
    """Get GitHub username from user input"""
    return input("GitHub Username: ").strip()

def get_github_token() -> str:
    """Get GitHub token with default from environment or user input"""
    default_token = os.environ.get("GITHUB_TOKEN", "")
    if default_token:
        use_default = input(f"Use token from environment variable GITHUB_TOKEN? [Y/n]: ").strip().lower()
        if use_default in ["", "y", "yes"]:
            return default_token
    
    return getpass.getpass("GitHub Personal Access Token: ").strip()

def verify_github_token(username: str, token: str) -> bool:
    """Verify GitHub token by making a simple API request"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(f"https://api.github.com/users/{username}", headers=headers)
        if response.status_code == 200:
            print_success("GitHub token verified successfully")
            return True
        else:
            print_error(f"Failed to verify GitHub token: {response.status_code} {response.reason}")
            return False
    except Exception as e:
        print_error(f"Error verifying GitHub token: {e}")
        return False

def check_token_permissions(token: str) -> Dict[str, bool]:
    """Check if the token has the required permissions for package operations"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    permissions = {
        "repo": False,
        "write:packages": False,
        "read:packages": False,
        "delete:packages": False
    }
    
    try:
        # Get rate limit info to check authentication and scopes
        response = requests.get("https://api.github.com/rate_limit", headers=headers)
        
        if response.status_code != 200:
            print_error(f"Failed to check token permissions: {response.status_code} {response.reason}")
            return permissions
        
        # Parse X-OAuth-Scopes header to check permissions
        scopes = response.headers.get("X-OAuth-Scopes", "").split(", ")
        
        for scope in scopes:
            if scope == "repo":
                permissions["repo"] = True
            elif scope == "write:packages":
                permissions["write:packages"] = True
            elif scope == "read:packages":
                permissions["read:packages"] = True
            elif scope == "delete:packages":
                permissions["delete:packages"] = True
            elif scope == "packages":  # Full packages scope (includes all package permissions)
                permissions["write:packages"] = True
                permissions["read:packages"] = True
                permissions["delete:packages"] = True
        
        return permissions
    except Exception as e:
        print_error(f"Error checking token permissions: {e}")
        return permissions

def docker_login(username: str, token: str) -> bool:
    """Login to GitHub Container Registry with Docker"""
    print_header("LOGGING IN TO GITHUB CONTAINER REGISTRY")
    
    # Check if Docker is installed
    if not run_command("docker --version"):
        print_error("Docker is not installed or not in the PATH")
        return False
    
    # Login to GitHub Container Registry
    print(f"Logging in to GitHub Container Registry as {username}...")
    
    # Write token to file to avoid showing it in process list
    token_file = ".ghcr_token"
    try:
        with open(token_file, "w") as f:
            f.write(token)
        
        command = f"cat {token_file} | docker login ghcr.io -u {username} --password-stdin"
        result = run_command(command)
        
        # Remove token file
        os.remove(token_file)
        
        if result and "Login Succeeded" in result:
            print_success("Login to GitHub Container Registry successful")
            return True
        else:
            print_error("Failed to login to GitHub Container Registry")
            return False
    except Exception as e:
        print_error(f"Error during GitHub Container Registry login: {e}")
        if os.path.exists(token_file):
            os.remove(token_file)
        return False

def build_docker_image(username: str, image_name: str, tag: str = "latest") -> bool:
    """Build Docker image with the correct tag for GitHub Container Registry"""
    print_header("BUILDING DOCKER IMAGE")
    
    full_image_name = f"ghcr.io/{username}/{image_name}:{tag}"
    print(f"Building Docker image: {full_image_name}")
    
    # Check if Dockerfile exists
    if not os.path.exists("Dockerfile"):
        print_error("Dockerfile not found in the current directory")
        return False
    
    # Build the Docker image
    command = f"docker build -t {full_image_name} ."
    result = run_command(command)
    
    if result is not None:
        print_success(f"Docker image built successfully: {full_image_name}")
        return True
    else:
        print_error("Failed to build Docker image")
        return False

def push_docker_image(username: str, image_name: str, tag: str = "latest") -> bool:
    """Push Docker image to GitHub Container Registry"""
    print_header("PUSHING DOCKER IMAGE TO GITHUB CONTAINER REGISTRY")
    
    full_image_name = f"ghcr.io/{username}/{image_name}:{tag}"
    print(f"Pushing Docker image: {full_image_name}")
    
    # Push the Docker image
    command = f"docker push {full_image_name}"
    result = run_command(command)
    
    if result is not None:
        print_success(f"Docker image pushed successfully: {full_image_name}")
        return True
    else:
        print_error("Failed to push Docker image")
        return False

def setup_github_workflow(username: str, image_name: str) -> bool:
    """Set up GitHub Actions workflow for automatic Docker builds"""
    print_header("SETTING UP GITHUB ACTIONS WORKFLOW")
    
    workflows_dir = ".github/workflows"
    os.makedirs(workflows_dir, exist_ok=True)
    
    workflow_file = f"{workflows_dir}/docker-build.yml"
    
    if os.path.exists(workflow_file):
        overwrite = input(f"GitHub Actions workflow file already exists at {workflow_file}. Overwrite? [y/N]: ").strip().lower()
        if overwrite not in ["y", "yes"]:
            print_warning("Skipping GitHub Actions workflow setup")
            return False
    
    print(f"Creating GitHub Actions workflow file: {workflow_file}")
    
    workflow_content = f"""name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{{{ github.repository_owner }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ghcr.io/${{{{ github.repository_owner }}}}/{image_name}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{{{version}}}}
            type=semver,pattern={{{{major}}}}.{{{{minor}}}}
            type=sha
            latest

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
    
    try:
        with open(workflow_file, "w") as f:
            f.write(workflow_content)
        print_success(f"GitHub Actions workflow file created: {workflow_file}")
        return True
    except Exception as e:
        print_error(f"Failed to create GitHub Actions workflow file: {e}")
        return False

def save_credentials(username: str, token: str, filename="github_credentials.json") -> bool:
    """Save GitHub credentials to a file"""
    print_header("SAVING GITHUB CREDENTIALS")
    
    credentials = {
        "username": username,
        "token": token
    }
    
    try:
        with open(filename, "w") as f:
            json.dump(credentials, f, indent=2)
        print_success(f"GitHub credentials saved to {filename}")
        return True
    except Exception as e:
        print_error(f"Failed to save GitHub credentials: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Setup GitHub Container Registry and push Docker image"
    )
    parser.add_argument(
        "--username",
        help="GitHub username"
    )
    parser.add_argument(
        "--token",
        help="GitHub Personal Access Token with package permissions"
    )
    parser.add_argument(
        "--image-name",
        default="growth-accelerator-staffing",
        help="Docker image name (default: growth-accelerator-staffing)"
    )
    parser.add_argument(
        "--tag",
        default="latest",
        help="Docker image tag (default: latest)"
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building the Docker image"
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Skip pushing the Docker image"
    )
    parser.add_argument(
        "--setup-workflow",
        action="store_true",
        help="Set up GitHub Actions workflow for automatic builds"
    )
    parser.add_argument(
        "--save-credentials",
        action="store_true",
        help="Save GitHub credentials to a file"
    )
    parser.add_argument(
        "--credentials-file",
        default="github_credentials.json",
        help="File to save GitHub credentials (default: github_credentials.json)"
    )
    
    args = parser.parse_args()
    
    print_header("GITHUB CONTAINER REGISTRY SETUP")
    
    # Get GitHub username
    username = args.username
    if not username:
        username = get_github_username()
    
    # Get GitHub token
    token = args.token
    if not token:
        token = get_github_token()
    
    # Verify GitHub token
    if not verify_github_token(username, token):
        return 1
    
    # Check token permissions
    permissions = check_token_permissions(token)
    required_permissions = ["write:packages", "read:packages"]
    missing_permissions = [p for p in required_permissions if not permissions.get(p)]
    
    if missing_permissions:
        print_warning(f"Token is missing required permissions: {', '.join(missing_permissions)}")
        print("Please create a new token with the following permissions:")
        print("  - write:packages")
        print("  - read:packages")
        continue_anyway = input("Continue anyway? [y/N]: ").strip().lower()
        if continue_anyway not in ["y", "yes"]:
            return 1
    
    # Login to GitHub Container Registry
    if not docker_login(username, token):
        return 1
    
    # Build Docker image
    if not args.skip_build:
        if not build_docker_image(username, args.image_name, args.tag):
            return 1
    
    # Push Docker image
    if not args.skip_push:
        if not push_docker_image(username, args.image_name, args.tag):
            return 1
    
    # Set up GitHub Actions workflow
    if args.setup_workflow:
        setup_github_workflow(username, args.image_name)
    
    # Save credentials
    if args.save_credentials:
        save_credentials(username, token, args.credentials_file)
    
    # Print deployment information
    print_header("DEPLOYMENT INFORMATION")
    print(f"Docker Image: ghcr.io/{username}/{args.image_name}:{args.tag}")
    print("\nYou can use this image in your Azure deployment:")
    print(f"python deploy_to_azure_simplified.py \\")
    print(f"  # ...other parameters \\")
    print(f"  --github-username \"{username}\" \\")
    print(f"  --github-token \"{token}\" \\")
    print(f"  --container-image \"ghcr.io/{username}/{args.image_name}:{args.tag}\" \\")
    print(f"  # ...other parameters")
    
    print_success("GitHub Container Registry setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())