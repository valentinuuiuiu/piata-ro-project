-- Initialize PostgreSQL database with pgvector extension
-- This script is automatically executed when the PostgreSQL container starts

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database and user (if not exists)
-- Note: These are handled by environment variables in Docker

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE piata_ro TO piata_ro;

-- Verify pgvector installation
SELECT * FROM pg_extension WHERE extname = 'vector';
