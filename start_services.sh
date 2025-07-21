#!/bin/bash

# Piata.ro - Start PostgreSQL and Redis services with migration
echo "🚀 Starting Piata.ro with PostgreSQL and Redis..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Remove old SQLite-based volumes if they exist
echo "🧹 Cleaning up old volumes..."
docker volume prune -f

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d db redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if PostgreSQL is responding
until docker-compose exec db pg_isready -U ${DB_USER:-piata_ro} -d ${DB_NAME:-piata_ro}; do
  echo "⏳ PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is up and running!"

# Check if Redis is responding
echo "⏳ Checking Redis connection..."
until docker-compose exec redis redis-cli -a ${REDIS_PASSWORD:-piata_ro_redis_password_2024} ping; do
  echo "⏳ Redis is unavailable - sleeping"
  sleep 2
done

echo "✅ Redis is up and running!"

# Run Django migrations
echo "🔄 Running Django migrations..."
docker-compose run --rm web python manage.py migrate

# Create vector embeddings for existing data
echo "🔮 Creating vector embeddings..."
docker-compose run --rm web python manage.py create_embeddings --batch-size 50

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo "🎉 All services are running!"
echo "📝 Services available at:"
echo "   - Web application: http://localhost:8000"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo "   - Nginx: http://localhost"

echo ""
echo "📊 Check service status:"
echo "   docker-compose ps"
echo ""
echo "📋 View logs:"
echo "   docker-compose logs -f web"
