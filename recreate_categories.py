#!/usr/bin/env python
"""
Script to recreate categories in PostgreSQL from the exported structure
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from marketplace.models import Category

def recreate_categories():
    """Recreate all categories in PostgreSQL"""
    print("🏷️ Recreating categories in PostgreSQL...")
    
    # Load category data
    with open('categories_structure.json', 'r', encoding='utf-8') as f:
        categories_data = json.load(f)
    
    print(f"📊 Found {len(categories_data)} categories to create")
    
    # First, create all main categories (no parent)
    main_categories = [cat for cat in categories_data if cat['parent_slug'] is None]
    subcategories = [cat for cat in categories_data if cat['parent_slug'] is not None]
    
    print(f"📋 Creating {len(main_categories)} main categories...")
    
    created_main = 0
    for cat_data in main_categories:
        try:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'parent': None
                }
            )
            if created:
                created_main += 1
                print(f"  ✅ Created: {cat_data['name']}")
            else:
                print(f"  ⚠️  Already exists: {cat_data['name']}")
        except Exception as e:
            print(f"  ❌ Error creating {cat_data['name']}: {e}")
    
    print(f"✅ Created {created_main} main categories")
    print(f"📋 Creating {len(subcategories)} subcategories...")
    
    created_sub = 0
    errors = 0
    
    for cat_data in subcategories:
        try:
            # Find parent category
            try:
                parent = Category.objects.get(slug=cat_data['parent_slug'])
            except Category.DoesNotExist:
                print(f"  ❌ Parent not found for {cat_data['name']}: {cat_data['parent_slug']}")
                errors += 1
                continue
            
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'parent': parent
                }
            )
            if created:
                created_sub += 1
                if created_sub % 10 == 0:
                    print(f"  📈 Created {created_sub} subcategories so far...")
            else:
                print(f"  ⚠️  Already exists: {cat_data['name']}")
                
        except Exception as e:
            print(f"  ❌ Error creating {cat_data['name']}: {e}")
            errors += 1
    
    print(f"✅ Created {created_sub} subcategories with {errors} errors")
    
    # Verify the creation
    total_created = Category.objects.count()
    main_count = Category.objects.filter(parent__isnull=True).count()
    sub_count = Category.objects.filter(parent__isnull=False).count()
    
    print("")
    print("📊 Final Statistics:")
    print(f"   Total categories: {total_created}")
    print(f"   Main categories: {main_count}")
    print(f"   Subcategories: {sub_count}")
    
    # Show some examples
    print("")
    print("🏷️ Sample categories created:")
    for cat in Category.objects.filter(parent__isnull=True)[:5]:
        sub_count = cat.children.count()
        print(f"  - {cat.name} ({sub_count} subcategories)")
        for sub in cat.children.all()[:3]:
            print(f"    └─ {sub.name}")
        if sub_count > 3:
            print(f"    └─ ... and {sub_count - 3} more")
    
    return total_created

if __name__ == '__main__':
    try:
        total = recreate_categories()
        print(f"🎉 Successfully recreated {total} categories in PostgreSQL!")
    except Exception as e:
        print(f"💥 Error during category recreation: {e}")
        import traceback
        traceback.print_exc()
