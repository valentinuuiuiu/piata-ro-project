
# Use a multi-stage build for better caching and smaller image size
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Dependencies stage
FROM base AS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    postgresql-client \
    binutils \
    gcc \
    && rm -rf /var/lib/apt/lists/*
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM dependencies AS release
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "piata_ro.wsgi:application", "--bind", "0.0.0.0:8000"]
