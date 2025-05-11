# Setting Up GitHub Container Registry for Docker Images

This guide walks you through setting up GitHub Container Registry (GHCR) to store Docker images for the Growth Accelerator Staffing Platform.

## What is GitHub Container Registry?

GitHub Container Registry is a package registry integrated with GitHub that allows you to host and manage Docker container images within your GitHub organization or personal account.

## Prerequisites

- A GitHub account
- Git installed on your local machine
- Docker installed on your local machine
- Docker image of the Growth Accelerator Staffing Platform

## Step 1: Create a Personal Access Token (PAT)

1. Log in to your GitHub account
2. Click on your profile picture in the top-right corner
3. Select **Settings**
4. In the left sidebar, click on **Developer settings**
5. Click on **Personal access tokens** → **Tokens (classic)**
6. Click **Generate new token** → **Generate new token (classic)**
7. Give your token a descriptive name, e.g., "Growth Accelerator Container Registry"
8. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `write:packages` (Upload packages to GitHub Package Registry)
   - `read:packages` (Download packages from GitHub Package Registry)
   - `delete:packages` (Delete packages from GitHub Package Registry)
9. Click **Generate token**
10. **IMPORTANT**: Copy the token immediately and store it securely, as GitHub will only show it once

## Step 2: Log in to GitHub Container Registry

Use your GitHub username and the PAT to log in to the GitHub Container Registry:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u your-github-username --password-stdin
```

Replace `$GITHUB_TOKEN` with your PAT and `your-github-username` with your GitHub username.

## Step 3: Prepare Your Docker Image

Tag your Docker image with the GitHub Container Registry format:

```bash
docker build -t ghcr.io/your-github-username/growth-accelerator-staffing:latest .
```

Replace `your-github-username` with your GitHub username.

## Step 4: Push the Docker Image

Push the image to GitHub Container Registry:

```bash
docker push ghcr.io/your-github-username/growth-accelerator-staffing:latest
```

## Step 5: Configure Package Visibility (Optional)

By default, packages published to GitHub Container Registry are private. To change visibility:

1. Go to your GitHub profile
2. Click on **Packages**
3. Click on your container package
4. Click on **Package settings**
5. Under **Danger Zone**, you can change the visibility to public if needed

## Step 6: Using the Container Image in Deployment

Now you can use this container image in your Azure deployment:

```bash
python deploy_to_azure_simplified.py \
  # ...other parameters
  --github-username "your-github-username" \
  --github-token "your-github-token" \
  --container-image "ghcr.io/your-github-username/growth-accelerator-staffing:latest" \
  # ...other parameters
```

## GitHub Actions for Automated Builds (Optional)

You can automate the building and pushing of your Docker image using GitHub Actions.

Create a file at `.github/workflows/docker-build.yml` with the following content:

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v1
        with:
          registry: ghcr.io
          username: ${{ github.repository_owner }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for Docker
        id: meta
        uses: docker/metadata-action@v3
        with:
          images: ghcr.io/${{ github.repository_owner }}/growth-accelerator-staffing
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
            latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v2
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

With this workflow, every push to the main branch and any tagged release will automatically build and push a new version of your Docker image to GitHub Container Registry.

## Troubleshooting

### Authentication Issues

If you encounter authentication issues when pushing to GHCR:

1. Ensure your PAT has the correct scopes
2. Try logging in again with the correct credentials
3. Check that your token hasn't expired

### Image Push Failures

If your image push fails:

1. Ensure you have the right permissions in your GitHub account
2. Check that your image is properly tagged
3. Verify that Docker is correctly installed and running

### Rate Limiting

GitHub Container Registry has rate limits. If you hit them:

1. Wait and try again later
2. Consider implementing caching in your CI/CD pipeline
3. Optimize your Docker builds to reduce the number of pushes