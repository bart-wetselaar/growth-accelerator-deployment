# DNS Configuration Guide for Growth Accelerator Staffing Platform

This guide explains how to configure your DNS settings to point your custom domain to the Growth Accelerator Staffing Platform deployed on Azure App Service.

## Prerequisites

- Ownership of the domain (e.g., `growthaccelerator.nl`)
- Access to your domain's DNS settings (typically through your domain registrar)
- Azure App Service deployment complete
- Domain verification ID from Azure

## Overview of Required DNS Records

To properly configure your domain to work with Azure App Service, you need to set up the following DNS records:

1. **TXT Record** - For domain ownership verification
2. **CNAME Record** - To point your subdomain to Azure App Service
3. **Optional CDN CNAME Record** - If using Azure CDN for better performance

## Step 1: Domain Ownership Verification

Azure requires you to verify domain ownership before binding a custom domain to your App Service.

### Create a TXT Record

1. Log in to your domain registrar (e.g., GoDaddy, Namecheap, TransIP)
2. Go to DNS Management or DNS Records section
3. Add a new TXT record with the following values:
   - **Name/Host**: `asuid.app` (for app.growthaccelerator.nl)
   - **Value/Content**: `[Your Azure Domain Verification ID]`
   - **TTL**: 3600 (or 1 hour)

Example:
```
asuid.app.growthaccelerator.nl  TXT  MS12345678901234567890ABCDEFGH
```

## Step 2: Configure Custom Domain CNAME

Create a CNAME record that maps your subdomain to the Azure App Service.

1. Log in to your domain registrar
2. Go to DNS Management or DNS Records section
3. Add a new CNAME record with the following values:
   - **Name/Host**: `app` (for app.growthaccelerator.nl)
   - **Value/Target**: `growth-accelerator-staffing.azurewebsites.net` (your App Service URL)
   - **TTL**: 3600 (or 1 hour)

Example:
```
app.growthaccelerator.nl  CNAME  growth-accelerator-staffing.azurewebsites.net
```

## Step 3: (Optional) Configure CDN CNAME

If you're using Azure CDN to improve performance and reduce load on your App Service, you can set up an additional CNAME.

1. Log in to your domain registrar
2. Go to DNS Management or DNS Records section
3. Add a new CNAME record with the following values:
   - **Name/Host**: `cdn` (for cdn.growthaccelerator.nl)
   - **Value/Target**: `growth-accelerator-staffing-endpoint.azureedge.net` (your CDN endpoint)
   - **TTL**: 3600 (or 1 hour)

Example:
```
cdn.growthaccelerator.nl  CNAME  growth-accelerator-staffing-endpoint.azureedge.net
```

## Step 4: Verify DNS Propagation

DNS changes can take time to propagate (typically 15 minutes to 48 hours). You can verify propagation using:

1. **Command line** (Linux/macOS/Windows with WSL):
   ```bash
   dig TXT asuid.app.growthaccelerator.nl
   dig CNAME app.growthaccelerator.nl
   ```

2. **Online tools**:
   - [DNS Checker](https://dnschecker.org)
   - [MxToolbox](https://mxtoolbox.com/DNSLookup.aspx)
   - [WhatsMyDNS](https://whatsmydns.net)

## Step 5: Add Custom Domain in Azure Portal

After DNS propagation is complete, you need to configure the custom domain in Azure:

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Navigate to your App Service
3. Under **Settings**, select **Custom domains**
4. Click **+ Add custom domain**
5. Enter your custom domain (e.g., `app.growthaccelerator.nl`)
6. Azure will validate the domain ownership using the TXT record
7. Select **Add custom domain**

## Step 6: Configure HTTPS/SSL

For security, you should enable HTTPS for your custom domain:

1. In the Azure Portal, navigate to your App Service
2. Under **Settings**, select **TLS/SSL settings**
3. Select **Private Key Certificates**
4. Click **Create App Service Managed Certificate**
5. Select your custom domain and click **Create**
6. Once the certificate is created, go to **Custom domains**
7. Next to your custom domain, click **Add Binding**
8. Select the certificate and click **Add Binding**

## Troubleshooting

### Domain Verification Issues

- Ensure the TXT record is correctly configured with the exact verification ID provided by Azure
- Wait for DNS propagation (may take up to 48 hours)
- Check that the TXT record is at the correct host/name

### CNAME Issues

- Ensure your CNAME points to the correct App Service URL
- Check for conflicting DNS records (e.g., A records for the same host)
- Some domain registrars don't allow CNAME records at the root domain (e.g., growthaccelerator.nl)

### SSL/HTTPS Issues

- If the managed certificate fails to generate, you may need to use your own certificate
- Ensure your domain is correctly validated before requesting a certificate

## Using the DNS Checker Script

We've provided a DNS checker script that can help verify your DNS configuration:

```bash
python check_dns_configuration.py --domain app.growthaccelerator.nl --verification-id YOUR_VERIFICATION_ID
```

The script will check for proper TXT and CNAME record configuration and continuously monitor DNS propagation.

## Additional Resources

- [Azure App Service Domain Configuration Documentation](https://docs.microsoft.com/en-us/azure/app-service/app-service-web-tutorial-custom-domain)
- [Azure App Service HTTPS Configuration](https://docs.microsoft.com/en-us/azure/app-service/configure-ssl-bindings)
- [DNS Concepts and Best Practices](https://docs.microsoft.com/en-us/azure/dns/dns-operations-recordsets-portal)