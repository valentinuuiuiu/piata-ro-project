#!/bin/bash
# Production deployment script for Piața.ro

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warning "Running as root is not recommended. Consider using a non-root user."
fi

log_info "🚀 Starting Piața.ro production deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    log_error "Docker Compose (V2) is not installed. Please install Docker Compose V2 first."
    exit 1
fi

# Check Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    log_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

# Create environment file template if it doesn't exist
if [ ! -f .env.prod ]; then
    log_info "📝 Creating production environment file template..."
    cat > .env.prod << 'EOF'
# Production Environment Variables
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this-in-production
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DATABASE_URL=postgresql://piata_user:piata_password@db:5432/piata_ro
REDIS_URL=redis://redis:6379/0

# Security
ALLOWED_HOSTS=piata.ro,www.piata.ro,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://piata.ro,https://www.piata.ro

# Azure Storage (required for production)
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-name
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key
AZURE_STORAGE_CONTAINER=media

# Email settings (Resend.com)
RESEND_API_KEY=your-resend-api-key
DEFAULT_FROM_EMAIL=noreply@piata.ro

# Monitoring
SENTRY_DSN=your-sentry-dsn-if-using

# Stripe Payments
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_SECRET_KEY=your-stripe-secret-key
EOF
    
    # Generate a secure secret key
    secret_key=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || \
                 openssl rand -base64 48 | tr -d '/+=' | cut -c1-50)
    
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env.prod
    rm -f .env.prod.bak
    
    log_warning "⚠️  Created .env.prod template. Please update with your actual values before deployment!"
    log_warning "⚠️  Required: DEEPSEEK_API_KEY, AZURE_STORAGE_*, RESEND_API_KEY, STRIPE_*"
    exit 1
fi

# Validate environment file
if grep -q "your-" .env.prod; then
    log_error "Please update .env.prod with your actual values before deployment."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env.prod | xargs)

# Build services
log_info "🔨 Building Docker images..."
docker compose -f docker-compose.yml build

# Start database and Redis
log_info "🗄️ Starting database and Redis..."
docker compose -f docker-compose.yml up -d db redis

# Wait for database to be ready
log_info "⏳ Waiting for database to be ready..."
for i in {1..30}; do
    if docker compose -f docker-compose.yml exec db pg_isready -U piata_user -d piata_ro; then
        log_success "Database is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "Database failed to start within 60 seconds"
        docker compose -f docker-compose.yml logs db
        exit 1
    fi
    sleep 2
done

# Wait for Redis to be ready
log_info "⏳ Waiting for Redis to be ready..."
for i in {1..15}; do
    if docker compose -f docker-compose.yml exec redis redis-cli ping | grep -q PONG; then
        log_success "Redis is ready!"
        break
    fi
    if [ $i -eq 15 ]; then
        log_error "Redis failed to start within 30 seconds"
        docker compose -f docker-compose.yml logs redis
        exit 1
    fi
    sleep 2
done

# Create directories
log_info "📁 Creating necessary directories..."
docker compose -f docker-compose.yml run --rm web mkdir -p /app/logs /app/staticfiles /app/media

# Run database migrations
log_info "📊 Running database migrations..."
if ! docker compose -f docker-compose.yml run --rm web python manage.py migrate --settings=settings_prod --noinput; then
    log_error "Database migrations failed"
    docker compose -f docker-compose.yml logs web
    exit 1
fi

# Collect static files
log_info "📦 Collecting static files..."
if ! docker compose -f docker-compose.yml run --rm web python manage.py collectstatic --noinput --settings=settings_prod; then
    log_error "Static file collection failed"
    exit 1
fi

# Create superuser if needed
log_info "👤 Checking superuser..."
docker compose -f docker-compose.yml run --rm web python manage.py shell --settings=settings_prod -c "
from django.contrib.auth.models import User
import os
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@piata.ro', os.getenv('ADMIN_PASSWORD', 'admin123'))
    print('Superuser created: admin')
else:
    print('Superuser already exists')
"

# Start all services
log_info "🚀 Starting all services..."
docker compose -f docker-compose.yml up -d --wait

# Wait for services to be healthy
log_info "⏳ Waiting for services to become healthy..."
for i in {1..30}; do
    if docker compose -f docker-compose.yml ps --format json | grep -q '"healthy"'; then
        log_success "All services are healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        log_warning "Some services may not be fully healthy"
        break
    fi
    sleep 2
done

# Run health check
log_info "🏥 Running health check..."
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    log_success "Health check passed!"
else
    log_warning "Health check failed or service not ready yet"
fi

log_success "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Your marketplace is now running at:"
echo "   - Main site: https://localhost"
echo "   - Admin panel: https://localhost/admin"
echo "   - API: https://localhost/api"
echo "   - AI Assistant: https://localhost/ai"
echo "   - Health check: https://localhost/health"
echo ""

# Show service status
echo "📊 Service status:"
docker compose -f docker-compose.yml ps

echo ""
echo "📋 Next steps:"
echo "1. Configure SSL certificates in ./ssl/ directory"
echo "2. Set up domain name and update ALLOWED_HOSTS"
echo "3. Configure Azure storage for production media files"
echo "4. Set up monitoring and alerting"
echo "5. Configure backup procedures"
echo "6. Set up CI/CD pipeline"
echo ""
echo "📝 Logs can be found in:"
echo "   - Application logs: ./logs/"
echo "   - Docker logs: docker compose logs [service]"
echo ""
echo "🛡️  Security reminder:"
echo "   - Change default passwords"
echo "   - Rotate SECRET_KEY in production"
echo "   - Set up proper firewall rules"
echo "   - Enable monitoring and alerts"