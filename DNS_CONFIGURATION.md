# Growth Accelerator Staffing Platform - DNS Configuration Guide

This guide provides detailed instructions for configuring DNS settings for the Growth Accelerator Staffing Platform's custom domain (app.growthaccelerator.nl).

## Prerequisites

- Azure App Service deployment completed
- Access to your domain registrar or DNS provider for growthaccelerator.nl
- Domain verification ID (provided by Azure after deployment)

## DNS Records Overview

You'll need to configure two DNS records:

1. **TXT Record** - For domain ownership verification
2. **CNAME Record** - For routing traffic to Azure App Service

## Step 1: Add TXT Record for Domain Verification

The TXT record proves that you own the domain and allows Azure to use it with your web app.

| Record Type | Name/Host | Value/Target | TTL |
|-------------|-----------|--------------|-----|
| TXT | asuid.app.growthaccelerator.nl | [verification-id] | 3600 (or default) |

Replace `[verification-id]` with the actual verification ID provided by Azure after deployment.

## Step 2: Add CNAME Record for Traffic Routing

The CNAME record routes traffic from your custom domain to your Azure App Service.

| Record Type | Name/Host | Value/Target | TTL |
|-------------|-----------|--------------|-----|
| CNAME | app.growthaccelerator.nl | growth-accelerator-staffing.azurewebsites.net | 3600 (or default) |

Replace `growth-accelerator-staffing` with your actual App Service name if different.

## Step 3: Verify DNS Propagation

DNS changes can take time to propagate (typically 15 minutes to 48 hours). You can check if your DNS records have propagated using:

```bash
dig TXT asuid.app.growthaccelerator.nl
dig CNAME app.growthaccelerator.nl
```

Or use online tools like [DNSChecker](https://dnschecker.org/) or [MxToolbox](https://mxtoolbox.com/).

## Step 4: Verify Domain in Azure Portal

Once DNS records have propagated:

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Navigate to **App Services** > your app (e.g., growth-accelerator-staffing)
3. Select **Custom domains** from the left menu
4. Click **Add custom domain**
5. Enter your domain name (app.growthaccelerator.nl)
6. Azure will verify the TXT record
7. Once verified, add the domain

## Step 5: Configure SSL/TLS Certificate

For secure HTTPS access:

1. In the Azure Portal, go to your app service
2. Select **TLS/SSL settings** from the left menu
3. Click **Private Key Certificates** tab
4. Click **Create App Service Managed Certificate**
5. Select your verified custom domain
6. Click **Create**
7. Once created, go to **TLS/SSL bindings**
8. Click **Add TLS/SSL binding**
9. Select your custom domain, the managed certificate, and TLS 1.2
10. Click **Add Binding**

## Troubleshooting DNS Issues

### TXT Record Verification Fails

- Verify you added the TXT record to the correct domain zone
- Check that the name is exactly `asuid.app.growthaccelerator.nl`
- Ensure the verification ID value is correct with no extra spaces
- Wait longer for DNS propagation (up to 48 hours in rare cases)

### CNAME Issues

- Ensure there are no conflicting records (like A records) for the same hostname
- Verify the target is exactly your `.azurewebsites.net` address
- Check that your domain registrar allows CNAME records at the apex/root level

### Testing Connectivity

After DNS propagation and Azure verification:

```bash
# Check if your domain resolves to the correct Azure address
nslookup app.growthaccelerator.nl

# Test HTTPS connectivity
curl -I https://app.growthaccelerator.nl
```

## Monitoring Tool

You can use the included DNS monitoring script to check DNS propagation status:

```bash
python check_dns_configuration.py --domain app.growthaccelerator.nl --verification-id [your-verification-id]
```

For continuous monitoring during propagation:

```bash
python check_dns_configuration.py --domain app.growthaccelerator.nl --verification-id [your-verification-id] --monitor
```