#!/usr/bin/env python
"""
Test script to verify PostgreSQL and Redis connectivity
Run this before starting the migration
"""

import os
import sys
import psycopg2
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres():
    """Test PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'piata_ro'),
            user=os.getenv('DB_USER', 'piata_ro'),
            password=os.getenv('DB_PASSWORD', 'piata_ro_secure_password_2024'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"✅ PostgreSQL connection successful: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    try:
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            password=os.getenv('REDIS_PASSWORD', 'piata_ro_redis_password_2024'),
            db=int(os.getenv('REDIS_DB', '0'))
        )
        r.ping()
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        r.delete('test_key')
        print(f"✅ Redis connection successful: {value.decode()}")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_pgvector():
    """Test pgvector extension"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'piata_ro'),
            user=os.getenv('DB_USER', 'piata_ro'),
            password=os.getenv('DB_PASSWORD', 'piata_ro_secure_password_2024'),
            port=os.getenv('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if result:
            print(f"✅ pgvector extension available: {result}")
            return True
        else:
            print("❌ pgvector extension not found")
            return False
    except Exception as e:
        print(f"❌ pgvector test failed: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing database connections...")
    print(f"📍 Using environment:")
    print(f"   DB_HOST: {os.getenv('DB_HOST', 'localhost')}")
    print(f"   DB_PORT: {os.getenv('DB_PORT', '5432')}")
    print(f"   REDIS_HOST: {os.getenv('REDIS_HOST', 'localhost')}")
    print(f"   REDIS_PORT: {os.getenv('REDIS_PORT', '6379')}")
    print("")
    
    postgres_ok = test_postgres()
    redis_ok = test_redis()
    pgvector_ok = test_pgvector()
    
    print("")
    if postgres_ok and redis_ok and pgvector_ok:
        print("🎉 All systems ready for migration!")
        sys.exit(0)
    else:
        print("💥 Some systems are not ready. Please check Docker services.")
        print("Run: docker-compose up -d db redis")
        sys.exit(1)
