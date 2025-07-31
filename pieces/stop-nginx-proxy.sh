#!/bin/bash
# Stop Nginx proxy for MCP server

# Check if docker-compose file exists
if [ ! -f "docker-compose-nginx.yml" ]; then
    echo "Error: docker-compose-nginx.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if container is running
if ! docker-compose -f docker-compose-nginx.yml ps | grep -q "nginx-mcp-proxy"; then
    echo "Nginx MCP proxy is not running."
    exit 0
fi

# Stop nginx proxy
echo "Stopping Nginx proxy for MCP server..."

docker-compose -f docker-compose-nginx.yml down

if [ $? -eq 0 ]; then
    echo "Nginx proxy stopped successfully!"
else
    echo "Failed to stop Nginx proxy!"
    exit 1
fi
