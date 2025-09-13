#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Install required packages
print_status "Installing required packages..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Create SSL directory if it doesn't exist
mkdir -p /etc/ssl/certs /etc/ssl/private

# Set proper permissions
chmod 700 /etc/ssl/private

# Copy the nginx configuration to the proper location
print_status "Copying Nginx configuration..."
cp /home/shiva/piata-ro-project/nginx.conf /etc/nginx/nginx.conf

# Test Nginx configuration
print_status "Testing Nginx configuration..."
nginx -t

# If domain is not resolving yet, we'll create temporary self-signed certificates
print_status "Checking if domain is resolving..."
if ! nslookup piata-ai.ro &> /dev/null; then
    print_warning "Domain piata-ai.ro is not resolving yet. Creating temporary self-signed certificate."
    
    # Generate private key
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/piata-ai.ro.key \
        -out /etc/ssl/certs/piata-ai.ro.crt \
        -subj "/C=RO/ST=Bucharest/L=Bucharest/O=Piata AI/OU=IT/CN=piata-ai.ro"
    
    print_status "Temporary self-signed certificate created"
else
    print_status "Domain is resolving. Let's get SSL certificate from Let's Encrypt..."
    
    # Get SSL certificate from Let's Encrypt
    certbot --nginx -d piata-ai.ro -d www.piata-ai.ro --non-interactive --agree-tos --email ionutbaltag3@gmail.com
    
    print_status "SSL certificate obtained successfully"
fi

# Restart Nginx
print_status "Restarting Nginx..."
systemctl restart nginx

# Enable Nginx to start on boot
systemctl enable nginx

# Check Nginx status
print_status "Checking Nginx status..."
systemctl status nginx --no-pager -l

print_status "Setup completed successfully!"
print_warning "Please make sure your DNS is pointing to this server (142.132.234.22)"
print_status "After DNS propagation, run this script again to get a real SSL certificate"
