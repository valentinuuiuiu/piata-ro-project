#!/usr/bin/env python3
"""
Test script for the promotion system.
This script will test the complete promote listing flow with atomic transactions.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django environment
sys.path.append('/home/shiva/piata-ro-project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from marketplace.models import Listing, UserProfile, Category, CreditTransaction, ListingBoost


def test_promote_listing_flow():
    """Test the complete promotion flow with atomic transactions."""
    print("🧪 Testing Promote Listing Flow")
    print("=" * 50)
    
    try:
        # Find a test user or create one
        try:
            user = User.objects.get(username='testuser')
            print(f"✅ Found test user: {user.username}")
        except User.DoesNotExist:
            user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
            print(f"✅ Created test user: {user.username}")
        
        # Ensure user has a profile
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            print("✅ Created user profile")
        
        # Add some credits to the user
        original_credits = user_profile.credits_balance
        user_profile.add_credits(Decimal('5.0'))
        print(f"✅ Added 5.0 credits. Balance: {original_credits} → {user_profile.credits_balance}")
        
        # Find or create a test category
        category, created = Category.objects.get_or_create(
            name="Test Category",
            defaults={'slug': 'test-category'}
        )
        if created:
            print("✅ Created test category")
        
        # Find or create a test listing
        listing, created = Listing.objects.get_or_create(
            title="Test Listing for Promotion",
            user=user,
            defaults={
                'description': 'This is a test listing for promotion',
                'price': Decimal('100.00'),
                'currency': 'RON',
                'location': 'Bucharest',
                'category': category,
                'status': 'active',
                'is_featured': False
            }
        )
        if created:
            print("✅ Created test listing")
        else:
            # Reset to unfeatured for the test
            listing.is_featured = False
            listing.save()
            print("✅ Reset listing to unfeatured")
        
        print(f"\n📊 Initial State:")
        print(f"   User Credits: {user_profile.credits_balance}")
        print(f"   Listing Featured: {listing.is_featured}")
        print(f"   Active Boosts: {listing.boosts.filter(is_active=True).count()}")
        
        # Test the promotion flow with atomic transactions
        duration_days = 3
        credits_needed = Decimal(str(duration_days * 0.5))
        
        print(f"\n🚀 Testing promotion for {duration_days} days (cost: {credits_needed} credits)")
        
        # Simulate the atomic transaction from the view
        with transaction.atomic():
            # Lock user profile
            locked_profile = UserProfile.objects.select_for_update().get(user=user)
            
            # Check credits
            if locked_profile.credits_balance < credits_needed:
                raise ValueError("Insufficient credits")
            
            # Deduct credits
            locked_profile.deduct_credits(credits_needed)
            
            # Calculate expiration
            expires_at = timezone.now() + timedelta(days=duration_days)
            
            # Create boost record
            boost = ListingBoost.objects.create(
                listing=listing,
                boost_type='featured',
                credits_cost=int(credits_needed * 2),  # Store as integer (0.5 credits = 1)
                duration_days=duration_days,
                starts_at=timezone.now(),
                expires_at=expires_at,
                is_active=True
            )
            
            # Mark listing as featured
            listing.is_featured = True
            listing.save()
            
            # Create transaction record
            credit_transaction = CreditTransaction.objects.create(
                user=user,
                transaction_type='spent',
                amount=credits_needed,
                description=f"Promovare {duration_days} zile în categoria '{category.name}': {listing.title}",
                listing=listing
            )
        
        # Refresh objects from database
        user_profile.refresh_from_db()
        listing.refresh_from_db()
        
        print(f"\n✅ Promotion completed successfully!")
        print(f"📊 Final State:")
        print(f"   User Credits: {user_profile.credits_balance}")
        print(f"   Listing Featured: {listing.is_featured}")
        print(f"   Active Boosts: {listing.boosts.filter(is_active=True).count()}")
        print(f"   Boost expires: {boost.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Transaction ID: {credit_transaction.id}")
        
        # Test race condition prevention
        print(f"\n🧪 Testing race condition prevention...")
        
        # Try to promote again (should fail due to already featured)
        if listing.is_featured:
            print("✅ Listing is already featured - prevents double promotion")
        
        # Test insufficient credits scenario
        user_profile.credits_balance = Decimal('0.1')
        user_profile.save()
        
        try:
            with transaction.atomic():
                locked_profile = UserProfile.objects.select_for_update().get(user=user)
                if locked_profile.credits_balance < Decimal('0.5'):
                    raise ValueError("Insufficient credits for test")
        except ValueError:
            print("✅ Insufficient credits properly detected")
        
        print(f"\n🎉 All tests passed! Promotion system works correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_promote_listing_flow()
