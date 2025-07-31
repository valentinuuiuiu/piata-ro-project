
# Use a multi-stage build for better caching and smaller image size
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Dependencies stage
FROM base AS dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM dependencies AS release
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "piata_ro.wsgi:application", "--bind", "0.0.0.0:8000"]
