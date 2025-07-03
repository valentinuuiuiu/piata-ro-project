# Production-ready Dockerfile for Piața.ro
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=piata_ro.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn playwright httpx fastapi uvicorn
RUN playwright install chromium

# Copy project
COPY . .

# Create directories and collect static files
RUN mkdir -p media/listings staticfiles
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "piata_ro.wsgi:application"]