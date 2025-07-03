
from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from .models import Listing, ListingBoost
import logging

logger = logging.getLogger(__name__)

@shared_task
def auto_repost_listing(listing_id, interval_minutes):
    """
    Automatically reposts a listing at the specified interval
    """
    try:
        listing = Listing.objects.get(id=listing_id)
        boost = ListingBoost.objects.filter(listing=listing).first()
        
        if boost and boost.auto_repost:
            # Update listing's created_at to make it appear "fresh"
            listing.created_at = timezone.now()
            listing.save(update_fields=['created_at'])
            logger.info(f"Auto-reposted listing {listing_id} (interval: {interval_minutes} minutes)")
            return True
    except Exception as e:
        logger.error(f"Failed to auto-repost listing {listing_id}: {str(e)}")
    return False

