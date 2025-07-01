"""
Management command to populate database with sample data and real images
"""
import os
import requests
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from marketplace.models import Category, Listing, ListingImage, UserProfile
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate database with sample listings and real images'

    def handle(self, *args, **options):
        self.stdout.write('Populating sample data...')
        
        # Create sample users
        users = self.create_sample_users()
        
        # Create categories if they don't exist
        categories = self.create_categories()
        
        # Create sample listings with real images
        self.create_sample_listings(users, categories)
        
        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))

    def create_sample_users(self):
        users = []
        sample_users = [
            {'username': 'ion_popescu', 'email': 'ion@example.com', 'first_name': 'Ion', 'last_name': 'Popescu'},
            {'username': 'maria_ionescu', 'email': 'maria@example.com', 'first_name': 'Maria', 'last_name': 'Ionescu'},
            {'username': 'alex_dumitrescu', 'email': 'alex@example.com', 'first_name': 'Alexandru', 'last_name': 'Dumitrescu'},
        ]
        
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                # Create user profile
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': '+40712345678',
                        'location': 'București',
                        'credits_balance': Decimal('10.00')
                    }
                )
            users.append(user)
        
        return users

    def create_categories(self):
        categories_data = [
            {'name': 'Auto, Moto și Ambarcațiuni', 'slug': 'auto-moto'},
            {'name': 'Electronice și Electrocasnice', 'slug': 'electronice'},
            {'name': 'Imobiliare', 'slug': 'imobiliare'},
            {'name': 'Modă și Frumusețe', 'slug': 'moda'},
            {'name': 'Casă și Grădină', 'slug': 'casa-gradina'},
            {'name': 'Sport, Timp Liber, Artă', 'slug': 'sport-timp-liber'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name']}
            )
            categories.append(category)
        
        return categories

    def create_sample_listings(self, users, categories):
        sample_listings = [
            {
                'title': 'BMW 320d 2018, stare excelentă',
                'description': 'BMW Seria 3 320d, an fabricație 2018, motor diesel 2.0L, 190 CP. Mașina este în stare excelentă, service-uri la zi, fără accidente. Interior piele, navigație, senzori parcare.',
                'price': Decimal('22500.00'),
                'location': 'Cluj-Napoca',
                'category': 'auto-moto',
                'image_url': 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=800&h=600&fit=crop'
            },
            {
                'title': 'iPhone 13 Pro, 256GB, ca nou',
                'description': 'iPhone 13 Pro în stare impecabilă, 256GB stocare, culoare Pacific Blue. Folosit cu grijă, fără zgârieturi, bateria la 98%. Include încărcător original și husă.',
                'price': Decimal('3500.00'),
                'location': 'Timișoara',
                'category': 'electronice',
                'image_url': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=800&h=600&fit=crop'
            },
            {
                'title': 'Apartament modern 2 camere în centrul Bucureștiului',
                'description': 'Apartament cu 2 camere, 65mp, complet renovat, mobilat și utilat modern. Situat în centrul Bucureștiului, aproape de metrou. Ideal pentru tineri profesioniști.',
                'price': Decimal('120000.00'),
                'location': 'București, Sector 1',
                'category': 'imobiliare',
                'image_url': 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&h=600&fit=crop'
            },
            {
                'title': 'Jachetă din piele designer, mărimea M',
                'description': 'Jachetă din piele naturală, brand de designer, mărimea M. Purtată foarte puțin, în stare perfectă. Culoare neagră, stil clasic, perfectă pentru sezonul rece.',
                'price': Decimal('1200.00'),
                'location': 'Constanța',
                'category': 'moda',
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&h=600&fit=crop'
            },
            {
                'title': 'Set mobilier grădină',
                'description': 'Set complet mobilier pentru grădină: masă și 6 scaune din ratan sintetic, rezistent la intemperii. Stare foarte bună, folosit o singură vară.',
                'price': Decimal('800.00'),
                'location': 'București, Sector 3',
                'category': 'casa-gradina',
                'image_url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&h=600&fit=crop'
            },
            {
                'title': 'Bicicletă montană - Trek Marlin 7',
                'description': 'Bicicletă montană Trek Marlin 7, cadru aluminiu mărimea M, 21 viteze Shimano. Foarte bine întreținută, perfectă pentru trasee montane și urbane.',
                'price': Decimal('2500.00'),
                'location': 'Cluj-Napoca',
                'category': 'sport-timp-liber',
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&h=600&fit=crop'
            }
        ]

        for i, listing_data in enumerate(sample_listings):
            # Find category
            category = next((cat for cat in categories if cat.slug == listing_data['category']), categories[0])
            
            # Create listing
            listing, created = Listing.objects.get_or_create(
                title=listing_data['title'],
                defaults={
                    'description': listing_data['description'],
                    'price': listing_data['price'],
                    'location': listing_data['location'],
                    'user': users[i % len(users)],
                    'category': category,
                    'status': 'active',
                    'is_featured': i < 3  # Make first 3 featured
                }
            )
            
            if created:
                # Download and save image
                try:
                    response = requests.get(listing_data['image_url'], timeout=10)
                    if response.status_code == 200:
                        image_content = ContentFile(response.content)
                        image_name = f"listing_{listing.id}_{i}.jpg"
                        
                        listing_image = ListingImage.objects.create(
                            listing=listing,
                            is_main=True,
                            order=0
                        )
                        listing_image.image.save(image_name, image_content, save=True)
                        
                        self.stdout.write(f'Created listing: {listing.title} with image')
                    else:
                        self.stdout.write(f'Failed to download image for: {listing.title}')
                except Exception as e:
                    self.stdout.write(f'Error downloading image for {listing.title}: {str(e)}')
            else:
                self.stdout.write(f'Listing already exists: {listing.title}')