#!/usr/bin/env python
"""
Comprehensive data seeding script for Piata.ro
Seeds categories, users, and sample listings into PostgreSQL
"""

import os
import json
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from django.contrib.auth.models import User
from marketplace.models import Category, Listing, Location
from django.db import transaction
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_categories():
    """Seed all categories from the original SQLite data"""
    print("🏷️ Seeding categories...")
    
    # Main categories data
    main_categories = [
        {'name': 'Agro și Industrie', 'slug': 'agro-si-industrie', 'icon': '🏭', 'color': '#8B4513'},
        {'name': 'Animale', 'slug': 'animale', 'icon': '🐾', 'color': '#FF69B4'},
        {'name': 'Auto, Moto și Ambarcațiuni', 'slug': 'auto-moto-si-ambarcatiuni', 'icon': '🚗', 'color': '#FF4500'},
        {'name': 'Casă și Grădină', 'slug': 'casa-si-gradina', 'icon': '🏠', 'color': '#32CD32'},
        {'name': 'Educație', 'slug': 'educatie', 'icon': '📚', 'color': '#4169E1'},
        {'name': 'Electronice și Electrocasnice', 'slug': 'electronice-si-electrocasnice', 'icon': '📱', 'color': '#000080'},
        {'name': 'Imobiliare', 'slug': 'imobiliare', 'icon': '🏢', 'color': '#8A2BE2'},
        {'name': 'Locuri de muncă', 'slug': 'locuri-de-munca', 'icon': '💼', 'color': '#2F4F4F'},
        {'name': 'Mama și Copilul', 'slug': 'mama-si-copilul', 'icon': '👶', 'color': '#FFB6C1'},
        {'name': 'Matrimoniale', 'slug': 'matrimoniale', 'icon': '💕', 'color': '#DC143C'},
        {'name': 'Modă și Frumusețe', 'slug': 'moda-si-frumusete', 'icon': '👗', 'color': '#FF1493'},
        {'name': 'Servicii, Afaceri, Echipamente Firme', 'slug': 'servicii-afaceri-echipamente-firme', 'icon': '🏢', 'color': '#708090'},
        {'name': 'Sport, Timp Liber, Artă', 'slug': 'sport-timp-liber-arta', 'icon': '⚽', 'color': '#00CED1'},
        {'name': 'Sănătate', 'slug': 'sanatate', 'icon': '⚕️', 'color': '#228B22'},
    ]
    
    # Create main categories
    created_main = 0
    for cat_data in main_categories:
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
            logger.info(f"✅ Created main category: {cat_data['name']}")
    
    # Sample subcategories for each main category
    subcategories_data = {
        'agro-si-industrie': [
            'Echipamente Agricole', 'Utilaje Industriale', 'Materiale de Construcție'
        ],
        'animale': [
            'Câini', 'Pisici', 'Animale de Fermă', 'Animale Exotice', 'Accesorii Animale'
        ],
        'auto-moto-si-ambarcatiuni': [
            'Autoturisme', 'Motociclete', 'Camioane', 'Ambarcațiuni', 'Accesorii Auto', 'Anvelope și Jante'
        ],
        'casa-si-gradina': [
            'Mobilier', 'Decorațiuni', 'Grădină', 'Electronice Casă', 'Materiale DIY'
        ],
        'educatie': [
            'Cursuri', 'Cărți', 'Meditații', 'Limbi Străine', 'IT & Programming'
        ],
        'electronice-si-electrocasnice': [
            'Telefoane Mobile', 'Laptopuri', 'TV & Audio', 'Electrocasnice Mari', 'Electrocasnice Mici', 'Gaming'
        ],
        'imobiliare': [
            'Apartamente de vânzare', 'Case de vânzare', 'Apartamente de închiriat', 'Case de închiriat', 'Terenuri'
        ],
        'locuri-de-munca': [
            'IT & Software', 'Vânzări', 'Marketing', 'Administrație', 'Construcții', 'HoReCa'
        ],
        'mama-si-copilul': [
            'Îmbrăcăminte Copii', 'Jucării', 'Cărți Copii', 'Echipamente Bebeluși', 'Sănătate Copii'
        ],
        'matrimoniale': [
            'Bărbați caută Femei', 'Femei caută Bărbați', 'Prietenii', 'Matrimoniale Serioase'
        ],
        'moda-si-frumusete': [
            'Haine Femei', 'Haine Bărbați', 'Încălțăminte', 'Accesorii', 'Cosmetice', 'Parfumuri'
        ],
        'servicii-afaceri-echipamente-firme': [
            'Servicii IT', 'Consultanță', 'Contabilitate', 'Marketing', 'Design', 'Echipamente Birou'
        ],
        'sport-timp-liber-arta': [
            'Echipamente Sportive', 'Fitness', 'Călătorii', 'Muzică', 'Artă', 'Colecții'
        ],
        'sanatate': [
            'Aparatură Medicală', 'Medicamente', 'Suplimente', 'Servicii Medicale', 'Wellness'
        ]
    }
    
    # Create subcategories
    created_sub = 0
    for parent_slug, subcats in subcategories_data.items():
        try:
            parent = Category.objects.get(slug=parent_slug)
            for subcat_name in subcats:
                subcat_slug = subcat_name.lower().replace(' ', '-').replace('&', 'si').replace(',', '')
                subcat_slug = ''.join(c for c in subcat_slug if c.isalnum() or c == '-')
                
                subcategory, created = Category.objects.get_or_create(
                    slug=subcat_slug,
                    defaults={
                        'name': subcat_name,
                        'parent': parent,
                        'icon': '',
                        'color': parent.color
                    }
                )
                if created:
                    created_sub += 1
        except Category.DoesNotExist:
            logger.warning(f"Parent category not found: {parent_slug}")
    
    logger.info(f"✅ Created {created_main} main categories and {created_sub} subcategories")
    return created_main + created_sub

def seed_locations():
    """Seed sample locations"""
    print("📍 Seeding locations...")
    
    major_cities = [
        {'name': 'București', 'latitude': 44.4268, 'longitude': 26.1025},
        {'name': 'Cluj-Napoca', 'latitude': 46.7712, 'longitude': 23.6236},
        {'name': 'Timișoara', 'latitude': 45.7489, 'longitude': 21.2087},
        {'name': 'Iași', 'latitude': 47.1585, 'longitude': 27.6014},
        {'name': 'Constanța', 'latitude': 44.1598, 'longitude': 28.6348},
        {'name': 'Craiova', 'latitude': 44.3302, 'longitude': 23.7949},
        {'name': 'Brașov', 'latitude': 45.6427, 'longitude': 25.5887},
        {'name': 'Galați', 'latitude': 45.4353, 'longitude': 28.0080},
    ]
    
    created = 0
    for city_data in major_cities:
        location, is_created = Location.objects.get_or_create(
            name=city_data['name'],
            defaults={
                'latitude': city_data['latitude'],
                'longitude': city_data['longitude'],
                'location_type': 'city'
            }
        )
        if is_created:
            created += 1
            logger.info(f"✅ Created location: {city_data['name']}")
    
    return created

def seed_sample_users():
    """Create sample users"""
    print("👥 Seeding sample users...")
    
    sample_users = [
        {'username': 'ion_popescu', 'email': 'ion@example.com', 'first_name': 'Ion', 'last_name': 'Popescu'},
        {'username': 'maria_ionescu', 'email': 'maria@example.com', 'first_name': 'Maria', 'last_name': 'Ionescu'},
        {'username': 'alex_dumitrescu', 'email': 'alex@example.com', 'first_name': 'Alexandru', 'last_name': 'Dumitrescu'},
    ]
    
    created = 0
    for user_data in sample_users:
        user, is_created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_active': True
            }
        )
        if is_created:
            user.set_password('password123')
            user.save()
            created += 1
            logger.info(f"✅ Created user: {user_data['username']}")
    
    return created

def seed_sample_listings():
    """Create sample listings"""
    print("📦 Seeding sample listings...")
    
    # Get some data for listings
    categories = list(Category.objects.filter(parent__isnull=False)[:10])
    users = list(User.objects.all()[:3])
    locations = list(Location.objects.all()[:5])
    
    if not categories or not users:
        logger.warning("⚠️  No categories or users found, skipping listings")
        return 0
    
    sample_listings = [
        {
            'title': 'Apartament 2 camere în București',
            'description': 'Apartament frumos, renovat recent, în zona centrală.',
            'price': 75000,
            'category': 'apartamente-de-vanzare'
        },
        {
            'title': 'BMW Seria 3, 2015',
            'description': 'Mașină în stare foarte bună, service la zi.',
            'price': 18000,
            'category': 'autoturisme'
        },
        {
            'title': 'iPhone 13 Pro',
            'description': 'Telefon folosit doar 6 luni, garantie inclusă.',
            'price': 3500,
            'category': 'telefoane-mobile'
        },
        {
            'title': 'Set mobilier living',
            'description': 'Mobilier modern pentru living, 3 piese.',
            'price': 2500,
            'category': 'mobilier'
        },
        {
            'title': 'Curs programare Python',
            'description': 'Curs intensiv de Python pentru începători.',
            'price': 500,
            'category': 'cursuri'
        }
    ]
    
    created = 0
    for listing_data in sample_listings:
        try:
            category = Category.objects.filter(slug=listing_data['category']).first()
            if not category:
                category = categories[0]  # Fallback to first available category
            
            user = users[created % len(users)]
            location = locations[created % len(locations)] if locations else None
            
            listing, is_created = Listing.objects.get_or_create(
                title=listing_data['title'],
                defaults={
                    'description': listing_data['description'],
                    'price': listing_data['price'],
                    'currency': 'RON',
                    'category': category,
                    'user': user,
                    'location': location.name if location else 'București',
                    'status': 'active'
                }
            )
            if is_created:
                created += 1
                logger.info(f"✅ Created listing: {listing_data['title']}")
        except Exception as e:
            logger.error(f"❌ Error creating listing {listing_data['title']}: {e}")
    
    return created

def main():
    """Main seeding function"""
    try:
        with transaction.atomic():
            print("🌱 Starting data seeding process...")
            
            # Seed all data
            categories_count = seed_categories()
            locations_count = seed_locations()
            users_count = seed_sample_users()
            listings_count = seed_sample_listings()
            
            print(f"""
🎉 Data seeding completed successfully!
📊 Summary:
   - Categories: {categories_count}
   - Locations: {locations_count}
   - Users: {users_count}
   - Listings: {listings_count}
   
🔗 You can now:
   - Access admin: http://localhost:8000/admin (admin/admin123)
   - Browse marketplace: http://localhost:8000
   - Test API: http://localhost:8000/api/
            """)
            
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise

if __name__ == '__main__':
    main()
