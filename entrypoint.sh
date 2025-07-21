#!/bin/bash

set -e  # Exit on any error

# Default values if environment variables are not set
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

echo "🚀 Starting Piata.ro application..."

# Wait for PostgreSQL to be ready with timeout
echo "⏳ Waiting for PostgreSQL..."
timeout=60
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
  timeout=$((timeout-1))
  if [ $timeout -eq 0 ]; then
    echo "❌ PostgreSQL connection timeout!"
    exit 1
  fi
done
echo "✅ PostgreSQL started"

# Wait for Redis to be ready with timeout
echo "⏳ Waiting for Redis..."
timeout=60
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 1
  timeout=$((timeout-1))
  if [ $timeout -eq 0 ]; then
    echo "❌ Redis connection timeout!"
    exit 1
  fi
done
echo "✅ Redis started"

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import os
import django
import psycopg2
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1;')
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Create pgvector extension
echo "🔮 Creating pgvector extension..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')
        print('✅ pgvector extension created/verified')
except Exception as e:
    print(f'⚠️  pgvector extension warning: {e}')
"

# Apply database migrations
echo "🔄 Applying database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@piata.ro', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('✅ Superuser already exists')
"

# Seed categories if database is empty
echo "🏷️ Seeding categories..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()
from marketplace.models import Category
if Category.objects.count() == 0:
    print('📦 Database empty, will seed categories after static files...')
    exit(42)  # Special exit code to indicate seeding needed
else:
    print(f'✅ Categories already exist: {Category.objects.count()} found')
"
SEED_NEEDED=$?

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Seed data if needed
if [ $SEED_NEEDED -eq 42 ]; then
    echo "🌱 Seeding initial data..."
    if [ -f "/app/seed_data.py" ]; then
        python seed_data.py
    else
        echo "⚠️  No seed_data.py found, skipping data seeding"
    fi
fi

# Start the application
echo "🎉 Starting server..."
if [ "$1" = "gunicorn" ]; then
    exec gunicorn piata_ro.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
else
    exec "$@"
fi