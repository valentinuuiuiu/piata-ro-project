# SQLite to PostgreSQL Migration Guide

## Overview
This guide explains how to migrate your existing SQLite database to PostgreSQL for the Piata-RO marketplace application.

## Prerequisites
1. PostgreSQL server running
2. Python environment with required packages:
   - psycopg2-binary
   - Pillow (for image handling)
   - Django

## Migration Steps

### 1. Configure PostgreSQL Connection
Update your `.env` file with PostgreSQL credentials:
```bash
DATABASE_URL=postgres://username:password@localhost:5432/piata_ro
```

### 2. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Migrate Categories (Optional)
If you have categories in SQLite:
```bash
python manage.py migrate_categories_from_sqlite --sqlite-path db.sqlite3
```

### 4. Migrate All Data
```bash
python manage.py migrate_sqlite_data --sqlite-path db.sqlite3
```

## Migration Commands

### migrate_sqlite_data
Migrates all data including:
- Users and User Profiles
- Listings
- Listing Images (with placeholder images if PIL is available)

**Options:**
- `--sqlite-path`: Path to SQLite database file (default: db.sqlite3)

### migrate_categories_from_sqlite
Migrates categories from SQLite to PostgreSQL.

**Options:**
- `--sqlite-path`: Path to SQLite database file (default: db.sqlite3)

## Troubleshooting

### Common Issues

1. **PIL/Pillow not installed**
   - Images will be created without actual image data
   - Install with: `pip install Pillow`

2. **Database connection errors**
   - Check PostgreSQL credentials in `.env`
   - Ensure PostgreSQL is running

3. **Duplicate key errors**
   - The script uses `get_or_create` to handle duplicates
   - Existing data will be preserved

4. **Missing dependencies**
   - Install required packages: `pip install -r requirements.txt`

### Verification
After migration, verify data integrity:
```bash
python manage.py shell
>>> from marketplace.models import *
>>> User.objects.count()
>>> Listing.objects.count()
>>> Category.objects.count()
```

## Rollback
The migration is additive - it won't overwrite existing data. To rollback:
1. Drop PostgreSQL database
2. Recreate database
3. Run migrations again
