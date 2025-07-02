"""
Management command to clean up expired promotions and boosts.
This should be run periodically via cron job or Django-Q/Celery.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from marketplace.models import Listing, ListingBoost


class Command(BaseCommand):
    help = 'Clean up expired promotions and update listing featured status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        now = timezone.now()
        
        # Find expired boosts
        expired_boosts = ListingBoost.objects.filter(
            is_active=True,
            expires_at__lt=now
        )
        
        self.stdout.write(f"Found {expired_boosts.count()} expired boosts")
        
        listing_ids_to_update = []
        
        for boost in expired_boosts:
            self.stdout.write(
                f"  - Boost #{boost.id}: {boost.listing.title} "
                f"(expired {boost.expires_at.strftime('%Y-%m-%d %H:%M')})"
            )
            listing_ids_to_update.append(boost.listing.id)
        
        if not dry_run:
            # Mark boosts as inactive
            expired_count = expired_boosts.update(is_active=False)
            
            # Update listings that no longer have active boosts
            for listing_id in listing_ids_to_update:
                listing = Listing.objects.get(id=listing_id)
                active_boosts = listing.boosts.filter(is_active=True).count()
                
                if active_boosts == 0 and listing.is_featured:
                    listing.is_featured = False
                    listing.save()
                    self.stdout.write(
                        f"  ✅ Removed featured status from: {listing.title}"
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {expired_count} expired boosts'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Would have processed {expired_boosts.count()} expired boosts'
                )
            )
        
        # Show statistics
        total_active_boosts = ListingBoost.objects.filter(is_active=True).count()
        total_featured_listings = Listing.objects.filter(is_featured=True).count()
        
        self.stdout.write("\n📊 Current Status:")
        self.stdout.write(f"  - Active boosts: {total_active_boosts}")
        self.stdout.write(f"  - Featured listings: {total_featured_listings}")
