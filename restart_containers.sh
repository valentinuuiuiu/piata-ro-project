#!/bin/bash

echo "🔄 Restarting Piața.ro containers to apply authentication changes..."

# Change to project directory
cd /home/shiva/Desktop/piata-ro-project

# Stop all containers
echo "🛑 Stopping containers..."
docker-compose down

# Remove the web container image to force rebuild with new changes
echo "🗑️ Removing web container image to force rebuild..."
docker rmi piata-ro-project_web 2>/dev/null || echo "Web image not found (that's okay)"

# Rebuild and start containers
echo "🚀 Building and starting containers with new changes..."
docker-compose up -d --build

# Wait a moment for containers to start
echo "⏳ Waiting for containers to start..."
sleep 10

# Show container status
echo "📊 Container status:"
docker-compose ps

# Show logs from web container
echo "📝 Recent web container logs:"
docker-compose logs --tail=20 web

echo "✅ Container restart complete!"
echo "🌐 You can now test the admin login at: http://localhost:8000/admin/login/"
echo "🔐 Regular login is available at: http://localhost:8000/accounts/login/"
