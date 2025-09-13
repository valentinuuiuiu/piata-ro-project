#!/bin/bash
# Server setup script for piata-ai.ro

# Server IP
SERVER_IP="142.132.234.22"

# Create SSL directories
echo "Creating SSL directories..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "mkdir -p /etc/ssl/certs /etc/ssl/private"

# Copy nginx.conf
echo "Copying nginx configuration..."
scp -o StrictHostKeyChecking=no nginx.conf root@$SERVER_IP:/etc/nginx/nginx.conf

# Create temporary SSL certificates
echo "Creating temporary SSL certificates..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/piata-ai.ro.key \
  -out /etc/ssl/certs/piata-ai.ro.pem \
  -subj '/C=RO/ST=Romania/L=Bucharest/O=PiataAI/CN=piata-ai.ro'
"

# Test nginx configuration
echo "Testing nginx configuration..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "nginx -t"

# Restart nginx
echo "Restarting nginx..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP "systemctl restart nginx"

echo "Setup completed successfully!"
