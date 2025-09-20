#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime
import random

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from django.contrib.auth.models import User
from marketplace.models import Category, Listing, UserProfile

def create_sample_data():
    print("Creating sample data...")

    # Create a test user if it doesn't exist
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
    print(f"User: {'Created' if created else 'Exists'} - {user.username}")

    # Get or create category
    category, created = Category.objects.get_or_create(
        name='Imobiliare',
        defaults={
            'slug': 'imobiliare',
            'icon': 'fa-home',
            'color': '#FF6B6B'
        }
    )
    print(f"Category: {'Created' if created else 'Exists'} - {category.name}")

    # Create some sample listings
    sample_listings = [
        {
            'title': 'Apartament 3 camere, sector 2, Bucharest',
            'description': 'Apartament modern în sectorul 2 din București. 3 camere, baie nouă, balcon, parcare.',
            'price': 2800.00,
            'location': 'Sector 2, București',
            'city': 'București',
            'county': 'Ilfov'
        },
        {
            'title': 'Vilă în Herastrau, București',
            'description': 'Vilă frumoasă în zona Herastrau cu grădină mare și piscină. 5 camere, 3 băi.',
            'price': 15000.00,
            'location': 'Herastrau, București',
            'city': 'București',
            'county': 'Ilfov'
        },
        {
            'title': 'Garsonieră mobilată, Timișoara',
            'description': 'Garsonieră complet mobilată în centrul Timișoarei. Utilități incluse.',
            'price': 1200.00,
            'location': 'Centru, Timișoara',
            'city': 'Timișoara',
            'county': 'Timiș'
        },
        {
            'title': 'Birouri 200 m² în Cluj-Napoca',
            'description': 'Birouri moderne într-un complex prestigios din Cluj-Napoca. 200 m² la preț excelent.',
            'price': 8000.00,
            'location': 'Cluj-Napoca',
            'city': 'Cluj-Napoca',
            'county': 'Cluj'
        },
        {
            'title': 'Casă cu curte în Brașov',
            'description': 'Casă tradițională cu curte mare în frumoasa oraș Brașov. Poziție excelentă.',
            'price': 4500.00,
            'location': 'Brașov',
            'city': 'Brașov',
            'county': 'Brașov'
        }
    ]

    created_count = 0
    for listing_data in sample_listings:
        listing, created = Listing.objects.get_or_create(
            title=listing_data['title'],
            defaults={
                'description': listing_data['description'],
                'price': listing_data['price'],
                'currency': 'EUR',
                'location': listing_data['location'],
                'city': listing_data['city'],
                'county': listing_data['county'],
                'country': 'România',
                'user': user,
                'category': category,
                'status': 'active'
            }
        )
        if created:
            created_count += 1
            print(f"Created listing: {listing.title}")

    print(f"Total listings created: {created_count}")

    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'location': 'București',
            'bio': 'Test user for demonstration purposes.',
            'phone': '+40700000000'
        }
    )
    print(f"User Profile: {'Created' if created else 'Exists'} - {profile.user.username}")

if __name__ == '__main__':
    create_sample_data()
    print("Sample data creation completed!")
