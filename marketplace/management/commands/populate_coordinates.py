"""
Management command to populate coordinates for existing listings
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from marketplace.models import Listing
from marketplace.services.location_service import location_service
import time

class Command(BaseCommand):
    help = 'Populate coordinates for listings that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of listings to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if coordinates exist'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        # Get listings without coordinates or force update all
        if force:
            listings = Listing.objects.filter(status='active')[:limit]
            self.stdout.write(f'Processing {listings.count()} listings (force mode)')
        else:
            listings = Listing.objects.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True),
                status='active'
            )[:limit]
            self.stdout.write(f'Processing {listings.count()} listings without coordinates')
        
        success_count = 0
        error_count = 0
        
        for listing in listings:
            try:
                self.stdout.write(f'Processing: {listing.title} - {listing.location}')
                
                if location_service.populate_listing_coordinates(listing):
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Updated coordinates for: {listing.title}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Could not geocode: {listing.title}')
                    )
                
                # Rate limiting - respect Nominatim's 1 request per second
                time.sleep(1.1)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {listing.title}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Success: {success_count}, Errors: {error_count}'
            )
        )