#!/bin/bash
# Start Nginx proxy for MCP server

# Check if docker-compose file exists
if [ ! -f "docker-compose-nginx.yml" ]; then
    echo "Error: docker-compose-nginx.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if nginx config exists
if [ ! -f "nginx-mcp-proxy.conf" ]; then
    echo "Error: nginx-mcp-proxy.conf not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Create logs directory
mkdir -p nginx-logs

# Check if container is already running
if docker-compose -f docker-compose-nginx.yml ps | grep -q "nginx-mcp-proxy"; then
    echo "Nginx MCP proxy is already running."
    echo "Use 'docker-compose -f docker-compose-nginx.yml down' to stop it first."
    exit 1
fi

# Start nginx proxy
echo "Starting Nginx proxy for MCP server..."
echo "Proxy will be available at http://localhost:80"
echo "MCP server should be running on http://localhost:8005"

# Start in background
docker-compose -f docker-compose-nginx.yml up -d

if [ $? -eq 0 ]; then
    echo "Nginx proxy started successfully!"
    echo "Check logs with: docker-compose -f docker-compose-nginx.yml logs"
else
    echo "Failed to start Nginx proxy!"
    exit 1
fi

# Wait a moment for startup
sleep 3

# Show status
docker-compose -f docker-compose-nginx.yml ps
