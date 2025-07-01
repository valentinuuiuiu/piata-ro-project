"""
Management command to populate more listings with real images and test location services
"""
import os
import requests
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from marketplace.models import Category, Listing, ListingImage, UserProfile
from marketplace.services.location_service import location_service
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Populate more listings with real images and test location functionality'

    def handle(self, *args, **options):
        self.stdout.write('Populating more listings with location testing...')
        
        # Get existing users and categories
        users = list(User.objects.all())
        categories = list(Category.objects.all())
        
        if not users:
            self.stdout.write('No users found. Run populate_sample_data first.')
            return
            
        # Create more detailed listings
        self.create_detailed_listings(users, categories)
        
        # Test location service
        self.test_location_service()
        
        self.stdout.write(self.style.SUCCESS('More listings populated successfully!'))

    def create_detailed_listings(self, users, categories):
        detailed_listings = [
            {
                'title': 'Apartament 3 camere Herastrau',
                'description': 'Apartament superb cu 3 camere în zona Herastrau, 85mp, etaj 4/8, complet mobilat și utilat. Vedere spre parc, parcare subterană, lift. Ideal pentru familie.',
                'price': Decimal('180000.00'),
                'location': 'București, Sector 1, Herastrau',
                'address': 'Strada Aviatorilor nr. 15',
                'city': 'București',
                'county': 'Ilfov',
                'category': 'imobiliare',
                'image_url': 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=600&fit=crop'
            },
            {
                'title': 'Mercedes-Benz C-Class 2020',
                'description': 'Mercedes-Benz C220d AMG Line, an 2020, 45.000 km, motor diesel 2.0L, 194 CP. Mașina este în garanție, service la reprezentanță, fără accidente.',
                'price': Decimal('35000.00'),
                'location': 'Cluj-Napoca, Cluj',
                'address': 'Strada Memorandumului nr. 28',
                'city': 'Cluj-Napoca',
                'county': 'Cluj',
                'category': 'auto-moto',
                'image_url': 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=800&h=600&fit=crop'
            },
            {
                'title': 'MacBook Pro M2 2023',
                'description': 'MacBook Pro 14" cu chip M2, 16GB RAM, 512GB SSD. Stare perfectă, folosit pentru programare. Include încărcător original și husă de protecție.',
                'price': Decimal('8500.00'),
                'location': 'Timișoara, Timiș',
                'address': 'Bulevardul Vasile Parvan nr. 4',
                'city': 'Timișoara',
                'county': 'Timiș',
                'category': 'electronice',
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&h=600&fit=crop'
            },
            {
                'title': 'Casă cu grădină Brașov',
                'description': 'Casă individuală cu 4 camere și grădină de 500mp în Brașov. Renovată recent, încălzire centrală, garaj pentru 2 mașini. Zonă liniștită.',
                'price': Decimal('250000.00'),
                'location': 'Brașov, Brașov',
                'address': 'Strada Măceșului nr. 12',
                'city': 'Brașov',
                'county': 'Brașov',
                'category': 'imobiliare',
                'image_url': 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop'
            },
            {
                'title': 'PlayStation 5 + jocuri',
                'description': 'PlayStation 5 în stare perfectă + 5 jocuri (FIFA 24, Spider-Man, God of War, etc.). Include 2 controllere și toate cablurile originale.',
                'price': Decimal('2800.00'),
                'location': 'Constanța, Constanța',
                'address': 'Bulevardul Mamaia nr. 150',
                'city': 'Constanța',
                'county': 'Constanța',
                'category': 'electronice',
                'image_url': 'https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=800&h=600&fit=crop'
            },
            {
                'title': 'Rochie de mireasă designer',
                'description': 'Rochie de mireasă marca Pronovias, mărimea 36-38, purtată o singură dată. Include voal și accesorii. Curățată profesional.',
                'price': Decimal('3500.00'),
                'location': 'Iași, Iași',
                'address': 'Strada Lascăr Catargi nr. 54',
                'city': 'Iași',
                'county': 'Iași',
                'category': 'moda',
                'image_url': 'https://images.unsplash.com/photo-1594736797933-d0401ba2fe65?w=800&h=600&fit=crop'
            },
            {
                'title': 'Mobilă living modern',
                'description': 'Set complet mobilă living: canapea extensibilă, fotolii, masă de cafea, bibliotecă. Design modern, culoare gri, stare foarte bună.',
                'price': Decimal('4500.00'),
                'location': 'Ploiești, Prahova',
                'address': 'Strada Republicii nr. 89',
                'city': 'Ploiești',
                'county': 'Prahova',
                'category': 'casa-gradina',
                'image_url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&h=600&fit=crop'
            },
            {
                'title': 'Bicicletă electrică Cube',
                'description': 'Bicicletă electrică Cube Touring Hybrid, autonomie 100km, baterie Samsung, 8 viteze Shimano. Perfectă pentru oraș și trasee lungi.',
                'price': Decimal('6500.00'),
                'location': 'Sibiu, Sibiu',
                'address': 'Strada Nicolae Bălcescu nr. 25',
                'city': 'Sibiu',
                'county': 'Sibiu',
                'category': 'sport-timp-liber',
                'image_url': 'https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=800&h=600&fit=crop'
            }
        ]

        for i, listing_data in enumerate(detailed_listings):
            # Find category
            category = next((cat for cat in categories if cat.slug == listing_data['category']), categories[0])
            
            # Create listing with detailed location info
            listing, created = Listing.objects.get_or_create(
                title=listing_data['title'],
                defaults={
                    'description': listing_data['description'],
                    'price': listing_data['price'],
                    'location': listing_data['location'],
                    'address': listing_data.get('address', ''),
                    'city': listing_data.get('city', ''),
                    'county': listing_data.get('county', ''),
                    'user': random.choice(users),
                    'category': category,
                    'status': 'active',
                    'is_featured': i < 4  # Make first 4 featured
                }
            )
            
            if created:
                # Test location service - populate coordinates
                self.stdout.write(f'Testing location service for: {listing.title}')
                success = location_service.populate_listing_coordinates(listing)
                if success:
                    self.stdout.write(f'✅ Coordinates populated: {listing.latitude}, {listing.longitude}')
                else:
                    self.stdout.write(f'❌ Failed to get coordinates for: {listing.location}')
                
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
                        
                        self.stdout.write(f'✅ Created listing: {listing.title} with image')
                    else:
                        self.stdout.write(f'❌ Failed to download image for: {listing.title}')
                except Exception as e:
                    self.stdout.write(f'❌ Error downloading image for {listing.title}: {str(e)}')
            else:
                self.stdout.write(f'Listing already exists: {listing.title}')

    def test_location_service(self):
        self.stdout.write('\n🗺️ Testing Location Service...')
        
        # Test city coordinates
        test_cities = ['București', 'Cluj-Napoca', 'Timișoara', 'Brașov', 'Constanța']
        for city in test_cities:
            coords = location_service.get_coordinates_from_city(city)
            if coords:
                self.stdout.write(f'✅ {city}: {coords[0]}, {coords[1]}')
            else:
                self.stdout.write(f'❌ No coordinates for {city}')
        
        # Test geocoding
        test_addresses = [
            'Strada Aviatorilor 15, București',
            'Bulevardul Eroilor 29, Cluj-Napoca',
            'Piața Victoriei 2, Timișoara'
        ]
        
        for address in test_addresses:
            result = location_service.geocode(address)
            if result:
                self.stdout.write(f'✅ Geocoded: {address} -> {result.latitude}, {result.longitude}')
            else:
                self.stdout.write(f'❌ Failed to geocode: {address}')
        
        # Test location search
        search_results = location_service.search_locations('Cluj', limit=3)
        self.stdout.write(f'🔍 Search results for "Cluj": {len(search_results)} found')
        for result in search_results:
            self.stdout.write(f'   - {result.name}: {result.latitude}, {result.longitude}')
        
        self.stdout.write('🗺️ Location service testing completed!')