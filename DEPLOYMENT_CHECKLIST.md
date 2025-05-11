# Growth Accelerator Staffing Platform Deployment Checklist

Use this checklist to ensure a smooth deployment of the Growth Accelerator Staffing Platform to Azure App Service.

## Pre-Deployment Preparation

### Local Environment Setup
- [ ] Install Azure CLI
- [ ] Install Git
- [ ] Install Python 3.10+
- [ ] Install Docker and Docker Compose
- [ ] Clone the repository

### Azure Account Preparation
- [ ] Ensure Azure subscription is active
- [ ] Verify appropriate permissions (Contributor role)
- [ ] Check subscription spending limits and quotas

### Gather Required Information
- [ ] Azure Subscription ID
- [ ] Resource Group name to use
- [ ] Azure region to deploy to (e.g., West Europe)
- [ ] App Service name
- [ ] Custom domain (e.g., app.growthaccelerator.nl)
- [ ] Docker registry username and password
- [ ] API keys (Workable, LinkedIn, Squarespace)
- [ ] Database credentials

## GitHub Repository Setup

### Repository Configuration
- [ ] Create GitHub repository
- [ ] Push code to repository
- [ ] Set up branch protection for main branch
- [ ] Configure repository settings

### GitHub Actions Setup
- [ ] Create Service Principal in Azure for GitHub Actions
      ```
      az ad sp create-for-rbac --name "github-actions-growth-accelerator" \
                              --role contributor \
                              --scopes /subscriptions/<subscription-id> \
                              --sdk-auth
      ```
- [ ] Store Azure credentials in GitHub Secrets
- [ ] Configure additional GitHub Secrets:
  - [ ] AZURE_CREDENTIALS
  - [ ] AZURE_RESOURCE_GROUP
  - [ ] AZURE_APP_NAME
  - [ ] WORKABLE_API_KEY
  - [ ] LINKEDIN_CLIENT_ID
  - [ ] LINKEDIN_CLIENT_SECRET
  - [ ] SQUARESPACE_API_KEY
  - [ ] DATABASE_URL
  - [ ] SESSION_SECRET

## Azure Infrastructure Deployment

### ARM Template Deployment
- [ ] Update ARM template parameters if needed
- [ ] Deploy infrastructure using ARM template:
      ```
      az deployment group create --resource-group <resource-group> \
                                --template-file azure/azuredeploy.json \
                                --parameters appName=<app-name> customDomainName=<domain>
      ```
- [ ] Verify all resources are created successfully

### Database Setup
- [ ] Ensure PostgreSQL server is created
- [ ] Configure firewall rules
- [ ] Create database and users
- [ ] Verify database connection

### App Service Configuration
- [ ] Verify App Service is created
- [ ] Configure deployment settings
- [ ] Set up application settings
- [ ] Configure diagnostic settings
- [ ] Set up continuous deployment

## DNS and SSL Setup

### DNS Records
- [ ] Get domain verification ID from Azure
- [ ] Create TXT record for domain verification:
      ```
      asuid.<custom-domain>  TXT  <verification-id>
      ```
- [ ] Create CNAME record for custom domain:
      ```
      <subdomain>  CNAME  <app-name>.azurewebsites.net
      ```
- [ ] (Optional) Create CNAME for CDN endpoint:
      ```
      cdn  CNAME  <app-name>-endpoint.azureedge.net
      ```
- [ ] Verify DNS propagation

### SSL/TLS Configuration
- [ ] Add custom domain in Azure portal
- [ ] Generate App Service Managed Certificate
- [ ] Add TLS/SSL binding
- [ ] Enforce HTTPS
- [ ] Verify SSL configuration

## Application Deployment

### Docker Image
- [ ] Build Docker image
- [ ] Tag image
- [ ] Push image to container registry
- [ ] Verify image in registry

### App Service Deployment
- [ ] Deploy application to App Service
- [ ] Verify deployment success
- [ ] Check application logs

## Post-Deployment Tasks

### Application Verification
- [ ] Access application using custom domain
- [ ] Verify HTTPS is working
- [ ] Test authentication flow
- [ ] Test API functionality
- [ ] Test data retrieval from Workable
- [ ] Test integration with LinkedIn
- [ ] Test integration with Squarespace

### Monitoring and Alerts
- [ ] Set up Application Insights
- [ ] Configure alerts for errors
- [ ] Configure performance alerts
- [ ] Set up health check monitoring
- [ ] Configure email notifications

### Documentation
- [ ] Update README.md with deployment information
- [ ] Document environment variables
- [ ] Document custom domain setup
- [ ] Document maintenance procedures
- [ ] Document rollback procedures

### Backup and Disaster Recovery
- [ ] Configure database backups
- [ ] Verify backup functionality
- [ ] Document restore procedures
- [ ] Set up geo-redundancy (if needed)

## Optimization and Performance

### CDN Setup (Optional)
- [ ] Set up Azure CDN
- [ ] Configure CDN endpoint
- [ ] Set up CDN rules
- [ ] Verify CDN caching
- [ ] Configure cache-control headers

### Performance Testing
- [ ] Conduct load testing
- [ ] Analyze performance metrics
- [ ] Optimize database queries
- [ ] Implement performance improvements
- [ ] Verify improvements

## Security

### Security Scan
- [ ] Run security scan on application
- [ ] Verify secure headers
- [ ] Check for exposed endpoints
- [ ] Test authentication security
- [ ] Verify API security

### Compliance
- [ ] Ensure GDPR compliance
- [ ] Check data protection measures
- [ ] Verify privacy policy
- [ ] Document compliance measures

## Final Review

### Go-Live Checklist
- [ ] Conduct final application testing
- [ ] Verify all integrations are working
- [ ] Confirm monitoring is active
- [ ] Validate security measures
- [ ] Obtain stakeholder approval

### Announcement
- [ ] Prepare go-live announcement
- [ ] Update documentation
- [ ] Communicate with stakeholders
- [ ] Schedule post-deployment review

## Useful Commands

### Azure CLI
```bash
# Login to Azure
az login

# List subscriptions
az account list --output table

# Set active subscription
az account set --subscription <subscription-id>

# Create resource group
az group create --name <resource-group> --location <location>

# Deploy ARM template
az deployment group create --resource-group <resource-group> --template-file <template-file> --parameters <parameters>

# List App Services
az webapp list --resource-group <resource-group> --output table

# Get App Service details
az webapp show --resource-group <resource-group> --name <app-name>

# Restart App Service
az webapp restart --resource-group <resource-group> --name <app-name>

# Get deployment logs
az webapp log deployment show --resource-group <resource-group> --name <app-name>

# Stream logs
az webapp log tail --resource-group <resource-group> --name <app-name>
```

### Docker
```bash
# Build Docker image
docker build -t <image-name> .

# Tag Docker image
docker tag <image-name> <registry>/<image-name>:<tag>

# Push Docker image
docker push <registry>/<image-name>:<tag>

# Run Docker image locally
docker run -p 8000:8000 <image-name>
```

### GitHub Actions
```yaml
# Manually trigger GitHub Actions workflow
gh workflow run "Deploy to Azure App Service"
```