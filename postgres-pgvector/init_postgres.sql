-- PostgreSQL initialization script for piata.ro
-- Creates pgvector extension and optimizes for AI/ML workloads

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create extension for full-text search (used by Django)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Optimize PostgreSQL for vector operations
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Vector-specific optimizations
ALTER SYSTEM SET hnsw.ef_search = 40;

-- Grant permissions to the main database user
GRANT ALL PRIVILEGES ON DATABASE piata_ro TO piata_ro;

-- Log completion
SELECT 'PostgreSQL with pgvector initialized successfully!' as status;
