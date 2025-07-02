"""
Management command to check OpenStreetMap service health and populate missing coordinates
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from marketplace.models import Listing
from marketplace.services.location_service import location_service
import time

class Command(BaseCommand):
    help = 'Check OpenStreetMap service health and populate missing coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Perform service health check only',
        )
        parser.add_argument(
            '--populate-coords',
            action='store_true',
            help='Populate missing coordinates for listings',
        )
        parser.add_argument(
            '--test-geocoding',
            action='store_true',
            help='Test geocoding with sample Romanian locations',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of listings to process (default: 50)',
        )

    def handle(self, *args, **options):
        if options['health_check']:
            self.perform_health_check()
        
        if options['test_geocoding']:
            self.test_geocoding()
        
        if options['populate_coords']:
            self.populate_coordinates(options['limit'])
        
        if not any([options['health_check'], options['test_geocoding'], options['populate_coords']]):
            self.stdout.write(
                self.style.WARNING('No action specified. Use --help for available options.')
            )

    def perform_health_check(self):
        """Perform OpenStreetMap service health check"""
        self.stdout.write("🔍 Performing OpenStreetMap Service Health Check...")
        
        try:
            from marketplace.services.location_analytics import LocationAnalytics
            
            # Get service health
            health = LocationAnalytics.get_service_health()
            
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌'
            }
            
            self.stdout.write(
                f"\n{status_emoji.get(health['status'], '❓')} Service Status: {health['status'].upper()}"
            )
            self.stdout.write(f"📊 Success Rate: {health['success_rate']}%")
            self.stdout.write(f"⏱️  Average Response Time: {health['avg_response_time']}s")
            self.stdout.write(f"📈 Total Requests Today: {health['total_requests_today']}")
            
            # Test geocoding with a known location
            test_start = time.time()
            result = location_service.geocode("București")
            test_time = time.time() - test_start
            
            if result:
                self.stdout.write(
                    f"✅ Test Geocoding: București -> {result.latitude}, {result.longitude} ({test_time:.2f}s)"
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Test Geocoding Failed for București")
                )
            
            # Get popular locations
            popular = LocationAnalytics.get_popular_locations(7)
            if popular:
                self.stdout.write("\n🔥 Most Popular Locations (Last 7 days):")
                for i, location in enumerate(popular[:5], 1):
                    self.stdout.write(f"  {i}. {location['query']} ({location['search_count']} searches)")
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING("⚠️ Analytics not available, performing basic health check...")
            )
            
            # Basic health check
            test_start = time.time()
            result = location_service.geocode("București")
            test_time = time.time() - test_start
            
            if result:
                self.stdout.write(
                    f"✅ Service Healthy: București -> {result.latitude}, {result.longitude} ({test_time:.2f}s)"
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Service Unhealthy: Geocoding failed")
                )

    def test_geocoding(self):
        """Test geocoding with sample Romanian locations"""
        self.stdout.write("🧪 Testing Geocoding with Sample Locations...")
        
        test_locations = [
            ("București", "Bucharest - capital city"),
            ("Cluj-Napoca", "Cluj-Napoca - major city"),
            ("Piața Unirii, București", "Piața Unirii - famous square"),
            ("Strada Victoriei, București", "Strada Victoriei - famous street"),
            ("Castelul Peleș, Sinaia", "Castelul Peleș - tourist attraction"),
            ("Universitatea Babeș-Bolyai, Cluj-Napoca", "University in Cluj"),
            ("Constanța port", "Constanța - port city"),
            ("Brașov centrul vechi", "Brașov old town"),
            ("Timișoara piața victoriei", "Victory Square in Timișoara"),
            ("InvalidLocationXYZ123", "Invalid location test")
        ]
        
        success_count = 0
        total_time = 0
        
        for location, description in test_locations:
            start_time = time.time()
            result = location_service.geocode(location)
            response_time = time.time() - start_time
            total_time += response_time
            
            if result:
                success_count += 1
                self.stdout.write(
                    f"✅ {location} -> {result.latitude:.4f}, {result.longitude:.4f} ({response_time:.2f}s)"
                )
                self.stdout.write(f"   📍 {result.formatted_address}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"❌ {location} -> Failed ({response_time:.2f}s)")
                )
            
            # Respect rate limits
            time.sleep(1.1)
        
        success_rate = (success_count / len(test_locations)) * 100
        avg_time = total_time / len(test_locations)
        
        self.stdout.write(f"\n📊 Test Results:")
        self.stdout.write(f"   Success Rate: {success_rate:.1f}% ({success_count}/{len(test_locations)})")
        self.stdout.write(f"   Average Response Time: {avg_time:.2f}s")
        self.stdout.write(f"   Total Test Time: {total_time:.2f}s")

    def populate_coordinates(self, limit):
        """Populate missing coordinates for listings"""
        self.stdout.write(f"📍 Populating missing coordinates (limit: {limit})...")
        
        # Get listings without coordinates
        listings = Listing.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True
        )[:limit]
        
        if not listings.exists():
            self.stdout.write(
                self.style.SUCCESS("✅ All listings already have coordinates!")
            )
            return
        
        self.stdout.write(f"Found {listings.count()} listings without coordinates")
        
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        for i, listing in enumerate(listings, 1):
            try:
                if location_service.populate_listing_coordinates(listing):
                    success_count += 1
                    self.stdout.write(
                        f"✅ [{i}/{listings.count()}] {listing.title[:50]}... -> {listing.latitude}, {listing.longitude}"
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ [{i}/{listings.count()}] Failed: {listing.title[:50]}...")
                    )
                
                # Rate limiting - respect Nominatim's 1 request per second
                time.sleep(1.1)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ [{i}/{listings.count()}] Error: {listing.title[:50]}... - {str(e)}")
                )
        
        total_time = time.time() - start_time
        
        self.stdout.write(f"\n📊 Population Results:")
        self.stdout.write(f"   ✅ Success: {success_count}")
        self.stdout.write(f"   ❌ Errors: {error_count}")
        self.stdout.write(f"   ⏱️  Total Time: {total_time:.1f}s")
        self.stdout.write(f"   📈 Rate: {len(listings) / total_time:.1f} listings/minute")
