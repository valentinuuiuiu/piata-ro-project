"""
Add more listings with real images to test OpenStreetMap integration
"""
import requests
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from marketplace.models import Category, Listing, ListingImage
from marketplace.services.location_service import location_service
from decimal import Decimal

class Command(BaseCommand):
    help = 'Add more listings with images and test location services'

    def handle(self, *args, **options):
        self.stdout.write('Adding more listings with location testing...')
        
        # Get existing users and categories
        users = list(User.objects.all()[:3])
        if not users:
            self.stdout.write('No users found. Run populate_sample_data first.')
            return
            
        categories = {cat.slug: cat for cat in Category.objects.all()}
        
        # More diverse listings with specific locations
        new_listings = [
            {
                'title': 'Apartament 3 camere Floreasca',
                'description': 'Apartament modern cu 3 camere în zona Floreasca, București. Complet mobilat și utilat, parcare subterană, vedere la parc.',
                'price': Decimal('150000.00'),
                'location': 'București, Floreasca',
                'address': 'Strada Floreasca nr. 15',
                'city': 'București',
                'category': 'imobiliare',
                'image_url': 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&h=600&fit=crop'
            },
            {
                'title': 'Mercedes C-Class 2020',
                'description': 'Mercedes-Benz C-Class 2020, motor 2.0 benzină, 184 CP. Stare impecabilă, service la zi, interior AMG.',
                'price': Decimal('35000.00'),
                'location': 'Cluj-Napoca',
                'address': 'Strada Memorandumului nr. 28',
                'city': 'Cluj-Napoca',
                'category': 'auto-moto',
                'image_url': 'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=800&h=600&fit=crop'
            },
            {
                'title': 'MacBook Pro M2 2023',
                'description': 'MacBook Pro 14" cu chip M2, 16GB RAM, 512GB SSD. Folosit pentru design grafic, în garanție până în 2025.',
                'price': Decimal('8500.00'),
                'location': 'Timișoara',
                'address': 'Piața Victoriei nr. 2',
                'city': 'Timișoara',
                'category': 'electronice',
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&h=600&fit=crop'
            },
            {
                'title': 'Vilă cu piscină Snagov',
                'description': 'Vilă modernă cu 5 camere și piscină în zona Snagov. Teren 1000mp, garaj pentru 2 mașini, vedere la lac.',
                'price': Decimal('280000.00'),
                'location': 'Snagov, Ilfov',
                'address': 'Strada Lacului nr. 45, Snagov',
                'city': 'Snagov',
                'category': 'imobiliare',
                'image_url': 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop'
            },
            {
                'title': 'Rolex Submariner Original',
                'description': 'Ceas Rolex Submariner original, model 2019, cu certificat de autenticitate. Stare perfectă, cutie și documente.',
                'price': Decimal('25000.00'),
                'location': 'București, Herastrau',
                'address': 'Șoseaua Nordului nr. 7-9',
                'city': 'București',
                'category': 'moda',
                'image_url': 'https://images.unsplash.com/photo-1547996160-81dfa63595aa?w=800&h=600&fit=crop'
            },
            {
                'title': 'Bicicletă electrică Specialized',
                'description': 'Bicicletă electrică Specialized Turbo Vado, autonomie 100km, motor Bosch, perfectă pentru oraș.',
                'price': Decimal('4500.00'),
                'location': 'Brașov',
                'address': 'Strada Republicii nr. 62',
                'city': 'Brașov',
                'category': 'sport-timp-liber',
                'image_url': 'https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=800&h=600&fit=crop'
            },
            {
                'title': 'Apartament cu vedere la mare Constanța',
                'description': 'Apartament 2 camere cu vedere frontală la mare, zona Mamaia. Renovat recent, mobilat complet.',
                'price': Decimal('95000.00'),
                'location': 'Constanța, Mamaia',
                'address': 'Bulevardul Mamaia nr. 283',
                'city': 'Constanța',
                'category': 'imobiliare',
                'image_url': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop'
            },
            {
                'title': 'PlayStation 5 + Jocuri',
                'description': 'PlayStation 5 în stare perfectă + 8 jocuri (FIFA 24, Spider-Man, God of War). Toate accesoriile incluse.',
                'price': Decimal('2800.00'),
                'location': 'Iași',
                'address': 'Strada Păcurari nr. 121',
                'city': 'Iași',
                'category': 'electronice',
                'image_url': 'https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=800&h=600&fit=crop'
            }
        ]

        for i, listing_data in enumerate(new_listings):
            # Find category
            category = categories.get(listing_data['category'])
            if not category:
                continue
                
            # Test location service
            self.stdout.write(f'Testing location for: {listing_data["location"]}')
            location_result = location_service.geocode(
                listing_data.get('address', ''), 
                listing_data.get('city', '')
            )
            
            if location_result:
                self.stdout.write(f'✅ Location found: {location_result.latitude}, {location_result.longitude}')
            else:
                self.stdout.write(f'❌ Location not found for: {listing_data["location"]}')
            
            # Create listing
            listing, created = Listing.objects.get_or_create(
                title=listing_data['title'],
                defaults={
                    'description': listing_data['description'],
                    'price': listing_data['price'],
                    'location': listing_data['location'],
                    'address': listing_data.get('address', ''),
                    'city': listing_data.get('city', ''),
                    'user': users[i % len(users)],
                    'category': category,
                    'status': 'active',
                    'is_featured': i < 4,
                    'latitude': Decimal(str(location_result.latitude)) if location_result else None,
                    'longitude': Decimal(str(location_result.longitude)) if location_result else None,
                    'location_verified': location_result is not None
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
                        
                        self.stdout.write(f'✅ Created: {listing.title} with image and coordinates')
                    else:
                        self.stdout.write(f'❌ Failed to download image for: {listing.title}')
                except Exception as e:
                    self.stdout.write(f'❌ Error downloading image for {listing.title}: {str(e)}')
            else:
                self.stdout.write(f'ℹ️ Listing already exists: {listing.title}')
        
        # Test location search
        self.stdout.write('\n🗺️ Testing location search...')
        search_results = location_service.search_locations('București', limit=5)
        for result in search_results:
            self.stdout.write(f'Found: {result.name} at {result.latitude}, {result.longitude}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ More listings added successfully with location testing!'))