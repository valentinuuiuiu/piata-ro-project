#!/bin/bash
# Production deployment script for Piața.ro

set -e

echo "🚀 Starting Piața.ro deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env.prod ]; then
    echo "📝 Creating production environment file..."
    cat > .env.prod << EOF
# Production Environment Variables
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEEPSEEK_API_KEY=sk-a476a9683f274f449f081e9cb3a64fb8
DATABASE_URL=postgresql://piata_user:piata_password@db:5432/piata_ro
REDIS_URL=redis://redis:6379/0

# Azure Storage (optional)
# AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
# AZURE_STORAGE_ACCOUNT_KEY=your_storage_key
# AZURE_STORAGE_CONTAINER=media

# Email settings
# EMAIL_HOST_USER=your_email
# EMAIL_HOST_PASSWORD=your_password
EOF
    echo "✅ Created .env.prod file. Please update with your actual values."
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.yml build

echo "🗄️ Starting database and Redis..."
docker-compose -f docker-compose.yml up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

echo "📊 Running database migrations..."
docker-compose -f docker-compose.yml run --rm web python manage.py migrate

echo "📦 Collecting static files..."
docker-compose -f docker-compose.yml run --rm web python manage.py collectstatic --noinput

echo "👤 Creating superuser (if needed)..."
docker-compose -f docker-compose.yml run --rm web python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@piata.ro', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

echo "📝 Populating sample data..."
docker-compose -f docker-compose.yml run --rm web python manage.py populate_sample_data

echo "🚀 Starting all services..."
docker-compose -f docker-compose.yml up -d

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Your marketplace is now running at:"
echo "   - Main site: http://localhost"
echo "   - Admin panel: http://localhost/admin"
echo "   - API: http://localhost/api"
echo "   - AI Assistant: http://localhost/ai"
echo ""
echo "📊 Service status:"
docker-compose -f docker-compose.yml ps

echo ""
echo "📋 Next steps:"
echo "1. Update .env.prod with your actual API keys and settings"
echo "2. Configure your domain name in settings"
echo "3. Set up SSL certificates for production"
echo "4. Configure Azure storage for media files"
echo "5. Set up monitoring and logging"