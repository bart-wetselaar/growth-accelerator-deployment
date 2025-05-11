# Growth Accelerator Staffing Platform - Deployment Checklist

This checklist helps ensure a successful deployment of the Growth Accelerator Staffing Platform to Azure. Follow these steps in order to deploy the application.

## Pre-Deployment Checklist

### 1. Azure Account and Service Principal

- [ ] Active Azure subscription
- [ ] Azure Service Principal created with Contributor permissions
- [ ] Tenant ID, Client ID, and Client Secret recorded
- [ ] Subscription ID recorded

### 2. Container Registry and Docker Image

- [ ] GitHub repository created
- [ ] GitHub Personal Access Token created with appropriate permissions
- [ ] Docker image built and pushed to GitHub Container Registry (ghcr.io)
- [ ] Container image URL recorded

### 3. API Keys and Credentials

- [ ] Workable API Key obtained
- [ ] LinkedIn Client ID and Secret obtained
- [ ] Squarespace API Key obtained
- [ ] Session Secret created (or leave empty to auto-generate)

### 4. Domain and DNS

- [ ] Custom domain registered and available (e.g., app.growthaccelerator.nl)
- [ ] DNS access to add TXT and CNAME records

## Deployment Steps

### 1. Get Deployment Scripts

- [ ] Clone the deployment repository:
  ```
  git clone https://github.com/bart-wetselaar/growth-accelerator-deployment.git
  ```
  
  Or download individual files:
  ```
  curl -O https://raw.githubusercontent.com/bart-wetselaar/growth-accelerator-deployment/main/quick_deploy.sh
  chmod +x quick_deploy.sh
  ```

### 2. Run Deployment

- [ ] Run the Quick Deploy script:
  ```
  ./quick_deploy.sh
  ```
  
  Or run the deployment script directly:
  ```
  python deploy_to_azure_simplified.py --tenant-id "..." --client-id "..." ...
  ```

### 3. Configure DNS

- [ ] Add TXT record for domain verification:
  - Name: `asuid.app.growthaccelerator.nl`
  - Value: `<verification-id>` (provided by deployment output)
  
- [ ] Add CNAME record for the custom domain:
  - Name: `app.growthaccelerator.nl`
  - Value: `<app-name>.azurewebsites.net` (e.g., `growth-accelerator-staffing.azurewebsites.net`)

### 4. Add Custom Domain in Azure Portal

- [ ] Navigate to App Service in Azure Portal
- [ ] Select the deployed app
- [ ] Go to "Custom domains"
- [ ] Click "Add custom domain"
- [ ] Enter the custom domain name (e.g., app.growthaccelerator.nl)
- [ ] Verify domain ownership
- [ ] Add TLS/SSL binding

## Post-Deployment Checklist

### 1. Verify Deployment

- [ ] Access the Azure Web App URL: `https://<app-name>.azurewebsites.net`
- [ ] Verify the application loads correctly
- [ ] Check that all services are working (Workable, LinkedIn, Squarespace)
- [ ] Access the custom domain after DNS propagation: `https://app.growthaccelerator.nl`

### 2. Monitor Application

- [ ] Check Application Insights for any errors
- [ ] Verify database connectivity
- [ ] Test all major application features

### 3. Security and Maintenance

- [ ] Enable auto-scaling if needed
- [ ] Set up monitoring and alerts
- [ ] Schedule regular database backups
- [ ] Document the deployment for future reference

## Troubleshooting

If you encounter issues during deployment:

1. Check the deployment script output for specific error messages
2. Verify that all API keys and credentials are correct
3. Ensure the DNS records are properly configured
4. Check Azure Portal for resource-specific errors
5. Verify network connectivity and firewall settings

## Rollback Procedure

If needed, you can roll back the deployment:

1. Restore from a previous database backup
2. Redeploy an earlier container image version
3. Revert DNS changes if needed

For assistance, contact the deployment team.