import sqlite3
from django.core.management.base import BaseCommand
from marketplace.models import Category
from django.db import transaction

class Command(BaseCommand):
    help = 'Migrate categories from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('--sqlite-path', type=str, default='db.sqlite3', help='Path to SQLite DB')

    def handle(self, *args, **options):
        sqlite_path = options['sqlite_path']
        conn = None
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, slug, icon, color, parent_id FROM marketplace_category')
            rows = cursor.fetchall()
            
            self.stdout.write(f'Found {len(rows)} categories in SQLite.')

            # Map old id to new Category objects
            id_map = {}
            created_count = 0
            error_count = 0
            
            with transaction.atomic():
                # First pass: create categories without parent
                for idx, row in enumerate(rows):
                    id, name, slug, icon, color, parent_id = row
                    if parent_id is None:
                        try:
                            cat, created = Category.objects.get_or_create(
                                name=name,
                                defaults={
                                    'slug': slug,
                                    'icon': icon or '',
                                    'color': color or '#007bff',
                                    'parent': None
                                }
                            )
                            if created:
                                id_map[id] = cat
                                created_count += 1
                                if created_count % 20 == 0:
                                    self.stdout.write(f'Created {created_count} root categories...')
                        except Exception as e:
                            error_count += 1
                            self.stderr.write(self.style.ERROR(f'Error creating category {name}: {e}'))
                
                # Second pass: create categories with parent
                for idx, row in enumerate(rows):
                    id, name, slug, icon, color, parent_id = row
                    if parent_id is not None:
                        parent = id_map.get(parent_id)
                        try:
                            cat, created = Category.objects.get_or_create(
                                name=name,
                                defaults={
                                    'slug': slug,
                                    'icon': icon or '',
                                    'color': color or '#007bff',
                                    'parent': parent
                                }
                            )
                            if created:
                                id_map[id] = cat
                                created_count += 1
                                if created_count % 20 == 0:
                                    self.stdout.write(f'Created {created_count} categories (with parent)...')
                        except Exception as e:
                            error_count += 1
                            self.stderr.write(self.style.ERROR(f'Error creating category {name}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Categories migrated successfully! Created: {created_count}, Errors: {error_count}'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error during migration: {e}'))
        finally:
            if conn:
                conn.close()
