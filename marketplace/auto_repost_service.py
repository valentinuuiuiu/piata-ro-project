"""
Automatic repost service that runs in background
"""
import threading
import time
from django.utils import timezone
from django.db import transaction
from .models import AutoRepost, CreditTransaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class AutoRepostService:
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_service, daemon=True)
            self.thread.start()
            logger.info("Auto-repost service started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Auto-repost service stopped")
    
    def _run_service(self):
        while self.running:
            try:
                self._process_reposts()
            except Exception as e:
                logger.error(f"Error in auto-repost service: {e}")
            
            # Check every 60 seconds
            time.sleep(60)
    
    def _process_reposts(self):
        now = timezone.now()
        
        # Get due reposts
        due_reposts = AutoRepost.objects.filter(
            is_active=True,
            next_repost_at__lte=now
        ).select_related('listing', 'user', 'user__profile')
        
        for auto_repost in due_reposts:
            try:
                with transaction.atomic():
                    user_profile = auto_repost.user.profile
                    
                    if user_profile.credits_balance >= auto_repost.credits_per_repost:
                        # Deduct credits
                        user_profile.credits_balance -= auto_repost.credits_per_repost
                        user_profile.save()
                        
                        # Mark listing as featured
                        auto_repost.listing.is_featured = True
                        auto_repost.listing.save()
                        
                        # Create transaction
                        CreditTransaction.objects.create(
                            user=auto_repost.user,
                            transaction_type='spent',
                            amount=auto_repost.credits_per_repost,
                            description=f"Auto-repromovare: {auto_repost.listing.title}",
                            listing=auto_repost.listing
                        )
                        
                        # Schedule next repost
                        auto_repost.next_repost_at = now + timezone.timedelta(minutes=auto_repost.interval_minutes)
                        auto_repost.total_reposts += 1
                        auto_repost.save()
                        
                        logger.info(f"Auto-reposted: {auto_repost.listing.title}")
                    else:
                        # Disable if no credits
                        auto_repost.is_active = False
                        auto_repost.save()
                        logger.info(f"Disabled auto-repost for {auto_repost.listing.title} - no credits")
                        
            except Exception as e:
                logger.error(f"Error processing auto-repost {auto_repost.id}: {e}")

# Global service instance
auto_repost_service = AutoRepostService()