#!/bin/bash

# Script to migrate data from SQLite to PostgreSQL
# This script assumes you have both databases configured and Docker running

echo "Starting migration from SQLite to PostgreSQL with pgvector..."

# Step 1: Start the PostgreSQL container if not already running
echo "Starting PostgreSQL container..."
docker-compose up -d db

# Step 2: Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Step 3: Dump SQLite data to JSON
echo "Dumping data from SQLite to JSON..."
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin.logentry --indent 2 > data_dump.json

# Step 4: Create PostgreSQL database schema
echo "Creating PostgreSQL database schema..."
python manage.py migrate

# Step 5: Load data into PostgreSQL
echo "Loading data into PostgreSQL..."
python manage.py loaddata data_dump.json

echo "Migration completed successfully!"
echo "You can now start the full Docker environment with: docker-compose up -d"