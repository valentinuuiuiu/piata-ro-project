#!/bin/bash
#
# This script runs the Django test suite inside the Docker container.
# It ensures tests are run against the same PostgreSQL/pgvector database
# as the production environment.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Bringing up the database service..."
docker-compose up -d db

# Wait for the database to be ready
echo "Waiting for PostgreSQL to be ready..."
# Loop until pg_isready returns 0
until docker-compose exec db pg_isready -U piata_user -d piata_ro -q; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - running tests..."

# Run the tests inside the web container.
# The container will be created, the command run, and then the container removed.
docker-compose run --rm web python manage.py test "$@"

echo "Tests finished. Bringing down the database service..."
docker-compose down

echo "Done."
