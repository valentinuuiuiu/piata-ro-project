# Piata AI Domain Setup Guide

## Overview
This guide provides step-by-step instructions for setting up the domain piata-ai.ro with your Hetzner server and Coolify.

## Server Information
- **Server IP**: 142.132.234.22
- **IPv6 Address**: 2a01:4f8:c014:cd29::/64

## Prerequisites
1. Domain registered with Hostgate (✓ Completed - Domain registered on 05/09/2025)
2. Root SSH access to the Hetzner server

## Step 1: Configure DNS on Hostgate

### Create A Records
Log in to your Hostgate account and add the following DNS records for piata-ai.ro:

1. **A Record**:
   - Host: `@`
   - Type: `A`
   - Value: `142.132.234.22`
   - TTL: `Default`

2. **WWW A Record**:
   - Host: `www`
   - Type: `A`
   - Value: `142.132.234.22`
   - TTL: `Default`

3. **AAAA Record** (Optional for IPv6):
   - Host: `@`
   - Type: `AAAA`
   - Value: `2a01:4f8:c014:cd29::1` (Use the appropriate IPv6 address)
   - TTL: `Default`

4. **AAAA Record for WWW** (Optional):
   - Host: `www`
   - Type: `AAAA`
   - Value: `2a01:4f8:c014:cd29::1` (Use the appropriate IPv6 address)
   - TTL: `Default`

### Verify DNS Propagation
After updating the DNS records:
```bash
# On the server or locally
nslookup piata-ai.ro
nslookup www.piata-ai.ro
```

## Step 2: Deploy the Setup Script

### Connect to Hetzner Server
```bash
ssh root@142.132.234.22
```

### Copy Files to Server
Copy the following files to your server:
- `nginx.conf`
- `setup_ssl_and_deploy.sh`

```bash
# Example using scp
scp nginx.conf root@142.132.234.22:~
scp setup_ssl_and_deploy.sh root@142.132.234.22:~
```

### Run SSL and Nginx Setup
```bash
# Make script executable
chmod +x setup_ssl_and_deploy.sh

# Run the setup script
./setup_ssl_and_deploy.sh
```

This script will:
1. Install nginx and certbot (Let's Encrypt SSL client)
2. Configure Nginx with SSL support
3. Generate temporary self-signed certificate (domain not resolved yet)
4. Set up automatic HTTP to HTTPS redirects
5. Prepare for Let's Encrypt SSL certificate once DNS propagates

## Step 3: Configure Coolify with Domain

### Access Coolify
Once DNS propagates (usually takes a few minutes to 24 hours), access Coolify using the domain:
```
https://piata-ai.ro
```

### Configure Coolify Domain
1. Log in to Coolify
2. Navigate to Settings > General
3. Update the application URL to:
   - `https://piata-ai.ro`
4. Save the settings

### Configure SSL in Coolify
1. In Coolify, navigate to the "SSL" section
2. Let Coolify automatically provision SSL certificates through Let's Encrypt
3. Or manually upload SSL certificates obtained from certbot

## Step 4: Test and Verify

### Test Domain Access
1. Visit `https://piata-ai.ro` in your browser
2. Verify that you're redirected to HTTPS
3. Check that SSL certificate is valid

### Test SSL Certificate
```bash
# On the server
curl -I https://piata-ai.ro
```

### Verify Nginx Configuration
```bash
nginx -t
systemctl status nginx
```

## Troubleshooting

### DNS Not Resolving
- Wait for DNS propagation (use `dig piata-ai.ro` to check)
- Contact Hostgate support if needed

### SSL Certificate Issues
- If using Let's Encrypt, ensure port 80 and 443 are open
- Check Nginx configuration for SSL settings
- Verify domain ownership

### Coolify Configuration
- Ensure Coolify can bind to the correct port
- Check Coolify logs for any configuration errors
- Verify that Coolify can communicate with the database

## Next Steps
1. Complete DNS configuration on Hostgate
2. Run the setup script on the server
3. Wait for DNS propagation
4. Configure domain in Coolify
5. Test the application

## Additional Notes
- The setup script creates temporary self-signed certificates initially
- Once DNS propagates, the script can be run again to obtain real Let's Encrypt certificates
- Consider setting up automatic SSL renewal with certbot renew cron job
