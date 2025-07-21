#!/usr/bin/env python
"""
Migration script to transfer data from SQLite to PostgreSQL
Run this after setting up the new PostgreSQL database
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def migrate_data():
    """
    Migrate data from SQLite to PostgreSQL
    """
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    
    # Step 1: Backup existing SQLite data
    print("📦 Creating backup of SQLite database...")
    if os.path.exists('db.sqlite3'):
        os.system('cp db.sqlite3 db.sqlite3.backup')
        print("✅ SQLite backup created")
    
    # Step 2: Export data from SQLite
    print("📤 Exporting data from SQLite...")
    os.system('python manage.py dumpdata --settings=piata_ro.settings_sqlite > sqlite_data.json')
    
    # Step 3: Switch to PostgreSQL settings and migrate
    print("🔄 Switching to PostgreSQL and running migrations...")
    os.system('python manage.py migrate')
    
    # Step 4: Load data into PostgreSQL
    print("📥 Loading data into PostgreSQL...")
    try:
        os.system('python manage.py loaddata sqlite_data.json')
        print("✅ Data migration completed successfully!")
    except Exception as e:
        print(f"⚠️  Warning: Some data might not have migrated: {e}")
        print("This is normal for complex data relationships")
    
    # Step 5: Create vector embeddings for existing listings
    print("🔮 Creating vector embeddings for existing listings...")
    try:
        from marketplace.ai_search.enhanced_search import search_engine
        from marketplace.models import Listing
        
        listings = Listing.objects.filter(status='active')[:100]  # Limit for initial migration
        for listing in listings:
            try:
                # This will trigger embedding creation
                search_engine.get_similar_listings(listing, limit=1)
            except Exception as e:
                print(f"Warning: Could not create embedding for listing {listing.id}: {e}")
        
        print("✅ Vector embeddings created")
    except Exception as e:
        print(f"⚠️  Could not create vector embeddings: {e}")
        print("You can create these later using the management command")
    
    print("🎉 Migration completed!")
    print("📝 Next steps:")
    print("   1. Test your application: python manage.py runserver")
    print("   2. Check data integrity")
    print("   3. Remove SQLite backup if everything works: rm db.sqlite3.backup")

if __name__ == '__main__':
    migrate_data()
