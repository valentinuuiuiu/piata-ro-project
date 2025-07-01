"""
Process automatic reposts for listings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from marketplace.models import AutoRepost, CreditTransaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Process automatic reposts for listings'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Get all active auto-reposts that are due
        due_reposts = AutoRepost.objects.filter(
            is_active=True,
            next_repost_at__lte=now
        ).select_related('listing', 'user', 'user__profile')
        
        processed = 0
        failed = 0
        
        for auto_repost in due_reposts:
            try:
                user_profile = auto_repost.user.profile
                
                # Check if user has enough credits
                if user_profile.credits_balance >= auto_repost.credits_per_repost:
                    # Deduct credits
                    user_profile.credits_balance -= auto_repost.credits_per_repost
                    user_profile.save()
                    
                    # Mark listing as featured
                    auto_repost.listing.is_featured = True
                    auto_repost.listing.save()
                    
                    # Create transaction record
                    CreditTransaction.objects.create(
                        user=auto_repost.user,
                        transaction_type='spent',
                        amount=auto_repost.credits_per_repost,
                        description=f"Auto-repromovare: {auto_repost.listing.title}",
                        listing=auto_repost.listing
                    )
                    
                    # Update next repost time
                    auto_repost.next_repost_at = now + timezone.timedelta(minutes=auto_repost.interval_minutes)
                    auto_repost.total_reposts += 1
                    auto_repost.save()
                    
                    processed += 1
                    self.stdout.write(f'✅ Repromoved: {auto_repost.listing.title}')
                    
                else:
                    # Not enough credits - disable auto-repost
                    auto_repost.is_active = False
                    auto_repost.save()
                    
                    self.stdout.write(f'❌ Disabled auto-repost for {auto_repost.listing.title} - insufficient credits')
                    failed += 1
                    
            except Exception as e:
                self.stdout.write(f'❌ Error processing {auto_repost.listing.title}: {str(e)}')
                failed += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {processed} auto-reposts, {failed} failed/disabled')
        )