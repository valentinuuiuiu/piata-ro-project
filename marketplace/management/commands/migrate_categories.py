from django.core.management.base import BaseCommand
from django.core.files import File
import re
import os
from marketplace.models import Category
from sentence_transformers import SentenceTransformer
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate categories from sample-data.sql to PostgreSQL with embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql-file',
            default='sample-data.sql',
            help='Path to SQL file with category data'
        )
        parser.add_argument(
            '--model-name',
            default='all-MiniLM-L6-v2',
            help='Sentence transformer model for embeddings'
        )

    def handle(self, *args, **options):
        sql_file = options['sql_file']
        model_name = options['model_name']

        if not os.path.exists(sql_file):
            self.stdout.write(self.style.ERROR(f'SQL file {sql_file} not found'))
            return

        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse INSERT INTO categories statements
        category_data = self.parse_categories(content)
        if not category_data:
            self.stdout.write(self.style.ERROR('No category data found in SQL file'))
            return

        # Create main categories first (parent_id NULL)
        main_categories = {}
        for name, data in category_data.items():
            if data['parent_id'] is None:
                category, created = Category.objects.get_or_create(
                    name=name,
                    defaults={
                        'slug': data['slug'],
                        'icon': data['icon'],
                        'color': data['color'],
                        'parent': None
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created main category: {name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Main category exists: {name}'))
                main_categories[name] = category

        # Create subcategories
        sub_categories_created = 0
        for name, data in category_data.items():
            if data['parent_id'] is not None:
                parent_name = data['parent_name']  # We'll store parent name in data
                if parent_name in main_categories:
                    parent = main_categories[parent_name]
                    category, created = Category.objects.get_or_create(
                        name=name,
                        parent=parent,
                        defaults={
                            'slug': data['slug'],
                            'icon': data['icon'],
                            'color': data['color']
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created subcategory: {name} under {parent_name}'))
                        sub_categories_created += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'Subcategory exists: {name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'Parent not found for {name}: {parent_name}'))

        self.stdout.write(self.style.SUCCESS(f'Migrated {len(main_categories)} main and {sub_categories_created} sub categories'))

        # Generate embeddings
        self.generate_embeddings(model_name)

    def parse_categories(self, content):
        # Regex to match INSERT INTO categories (name, slug, icon, color, parent_id) VALUES (...)
        # Handle multiple VALUES
        pattern = r"INSERT INTO categories\s*\([^)]*\)\s*VALUES\s*\(([^)]+)\),\s*\(([^)]+)\)(?:,\s*\([^)]+\))*\s*--.*?(?=\n--|\Z)"
        matches = re.findall(r"INSERT INTO categories\s*\([^)]*\)\s*VALUES\s*\((.*?)\)", content, re.DOTALL | re.MULTILINE)

        category_data = {}
        main_categories = {}

        # First, find all main categories (parent_id NULL)
        main_pattern = r"INSERT INTO categories\s*\([^)]*\)\s*VALUES\s*\(('[^']+?)',\s*'([^']+?)',\s*'([^']+?)',\s*'([^']+?)',\s*NULL\)"
        main_matches = re.findall(main_pattern, content)

        for match in main_matches:
            name, slug, icon, color = match
            category_data[name] = {
                'slug': slug,
                'icon': icon,
                'color': color,
                'parent_id': None,
                'parent_name': None
            }
            main_categories[name] = True

        # Then subcategories
        sub_pattern = r"INSERT INTO categories\s*\([^)]*\)\s*VALUES\s*\(('[^']+?)',\s*'([^']+?)',\s*'([^']+?)',\s*'([^']+?)',\s*(\d+)\)"
        sub_matches = re.findall(sub_pattern, content)

        for match in sub_matches:
            name, slug, icon, color, parent_id_str = match
            parent_id = int(parent_id_str)
            # Map parent_id to parent name - this is tricky, assume order or use comments
            # For simplicity, use the comment lines to map
            # Look for -- Subcategories for 'Name' (Parent ID: X)
            comment_pattern = r"-- Subcategories for '([^']+?)'\s*\(Parent ID:\s*(\d+)\)"
            comment_matches = re.findall(comment_pattern, content)
            parent_map = {int(pid): pname for pname, pid in comment_matches}

            parent_name = parent_map.get(parent_id, f'Unknown_{parent_id}')
            category_data[name] = {
                'slug': slug,
                'icon': icon,
                'color': color,
                'parent_id': parent_id,
                'parent_name': parent_name
            }

        return category_data

    def generate_embeddings(self, model_name):
        self.stdout.write('Generating embeddings for categories...')
        model = SentenceTransformer(model_name)
        categories = Category.objects.all()
        updated = 0

        for category in categories:
            if category.embedding is None:
                embedding = model.encode(category.name)
                category.embedding = embedding.tolist()
                category.save()
                updated += 1
                logger.info(f'Generated embedding for category: {category.name}')

        self.stdout.write(self.style.SUCCESS(f'Generated embeddings for {updated} categories'))
