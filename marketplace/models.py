from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import uuid
from math import radians, cos, sin, asin, sqrt
import logging
from .utils.cache_utils import ListingCache, invalidate_listing_cache

# Set up logger
logger = logging.getLogger(__name__)

# Import chat models
from .models_chat import ChatConversation, ChatMessage


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="subcategories",
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # Invalidate cache after saving
        from .utils.cache_utils import CategoryCache
        CategoryCache.invalidate_categories()
        
    def get_listings_count(self):
        """Safely get the count of listings for this category"""
        try:
            return self.listings.count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting listings count for category {self.name}: {e}")
            return 0


def listing_image_path(instance, filename):
    # Generate path like: listings/user_id/listing_id/image.jpg
    return f"listings/{instance.listing.user.id}/{instance.listing.id}/{filename}"


class Listing(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("sold", "Sold"),
        ("expired", "Expired"),
        ("rejected", "Rejected"),
    )
    
    CURRENCY_CHOICES = (
        ("RON", "Lei (RON)"),
        ("EUR", "Euro (EUR)"),
        ("USD", "Dolari (USD)"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default="RON", choices=CURRENCY_CHOICES)
    location = models.CharField(max_length=100)
    # Enhanced location fields for geolocation services
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='România')
    location_verified = models.BooleanField(default=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="listings"
    )
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subcategory_listings",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(blank=True, null=True)  # For additional attributes
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["is_featured", "created_at"]),
            models.Index(fields=["price", "status"]),
            models.Index(fields=["city", "status"]),
            models.Index(fields=["latitude", "longitude"]),  # For geospatial queries
        ]

    def __str__(self):
        return self.title

    @property
    def main_image(self):
        """Get the main image or first image if none marked as main"""
        return self.images.filter(is_main=True).first() or self.images.first()

    def add_image(self, image_file, is_main=False):
        """Add new image to listing"""
        from .image_utils import process_uploaded_image
        
        # Process image and create thumbnail
        processed = process_uploaded_image(image_file)
        
        # Create image record
        image = self.images.create(
            image=processed['original'],
            thumbnail=processed['thumbnail'],
            is_main=is_main,
            order=self.images.count()
        )
        
        # If this is main image, unset others
        if is_main:
            self.images.exclude(pk=image.pk).update(is_main=False)
            
        return image

    def get_images_ordered(self):
        """Get all images in correct order"""
        return self.images.all().order_by('order')
    
    @property
    def has_coordinates(self):
        """Check if listing has valid coordinates"""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def full_address(self):
        """Get full formatted address"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.county:
            parts.append(self.county)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country:
            parts.append(self.country)
        return ', '.join(parts)
    
    def distance_to_point(self, latitude, longitude):
        """Calculate distance to a specific point"""
        if not self.has_coordinates or self.latitude is None or self.longitude is None:
            return None
        return Location.calculate_distance(
            float(self.latitude), float(self.longitude),
            float(latitude), float(longitude)
        )
    
    def distance_to_listing(self, other_listing):
        """Calculate distance to another listing"""
        if not self.has_coordinates or not other_listing.has_coordinates:
            return None
        return self.distance_to_point(
            float(other_listing.latitude), 
            float(other_listing.longitude)
        )
    
    @classmethod
    def get_nearby_listings(cls, latitude, longitude, radius_km=10, exclude_listing=None):
        """Get listings within a certain radius"""
        from django.db.models import Q
        from decimal import Decimal
        from math import cos, radians
        
        # Rough conversion: 1 degree ≈ 111 km
        lat_range = Decimal(str(radius_km)) / Decimal('111')
        lon_range = lat_range / Decimal(str(cos(radians(float(latitude)))))
        
        min_lat = Decimal(str(latitude)) - lat_range
        max_lat = Decimal(str(latitude)) + lat_range
        min_lon = Decimal(str(longitude)) - lon_range
        max_lon = Decimal(str(longitude)) + lon_range
        
        queryset = cls.objects.filter(
            latitude__range=(min_lat, max_lat),
            longitude__range=(min_lon, max_lon),
            status='active'
        ).exclude(latitude__isnull=True, longitude__isnull=True)
        
        if exclude_listing:
            queryset = queryset.exclude(pk=exclude_listing.pk)
        
        return queryset


class Report(models.Model):
    REASON_CHOICES = (
        ('spam', 'Spam or misleading'),
        ('fraud', 'Fraud or scam'),
        ('prohibited', 'Prohibited item'),
        ('wrong_category', 'Wrong category'),
        ('duplicate', 'Duplicate listing'),
        ('other', 'Other reason'),
    )
    
    reporter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Listing Report'
        verbose_name_plural = 'Listing Reports'
    
    def __str__(self):
        return f"Report on {self.listing.title} by {self.reporter.username}"

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=listing_image_path)
    is_main = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def save(self, *args, **kwargs):
        if self.is_main:
            # Ensure only one main image per listing
            ListingImage.objects.filter(listing=self.listing).update(is_main=False)
        super().save(*args, **kwargs)


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="messages",
        blank=True,
        null=True,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} favorited {self.listing.title}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    premium_until = models.DateTimeField(blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Credits system - 1 credit = 1 Euro = 5 RON, 0.5 credits = promote listing
    credits_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_credits_purchased = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # MFA and Security Fields
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    mfa_backup_codes = models.JSONField(default=list, blank=True)
    last_mfa_used = models.DateTimeField(blank=True, null=True)
    last_password_change = models.DateTimeField(auto_now_add=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
    
    @property
    def is_premium_active(self):
        """Check if premium subscription is still active"""
        if not self.is_premium or not self.premium_until:
            return False
        return timezone.now() < self.premium_until
    
    def can_promote_listing(self):
        """Determine if the user can promote a listing based on credits balance"""
        logger.info(f"Checking promotion ability for user {self.user.username} with balance {self.credits_balance}")
        """Check if user has enough credits to promote a listing (0.5 credits)"""
        return self.credits_balance >= 0.50
    
    def deduct_credits(self, amount):
        """Process of deducting credits from user account"""
        logger.info(f"Attempting to deduct {amount} credits for user {self.user.username}")
        """Safely deduct credits from user balance"""
        if self.credits_balance >= amount:
            self.credits_balance -= amount
            self.save()
            logger.info(f"Deducted {amount} credits from {self.user.username}, new balance {self.credits_balance}")
            return True
        logger.warning(f"Insufficient credits for user {self.user.username}: {self.credits_balance} available")
        return False
    def add_credits(self, amount):
        """Add credits to user balance"""
        self.credits_balance += amount
        self.total_credits_purchased += amount
        self.save()


class CreditPackage(models.Model):
    """Enhanced credit packages with bonuses and referral rewards"""
    TIER_CHOICES = (
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    )
    
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic')
    base_credits = models.DecimalField(max_digits=10, decimal_places=1)
    bonus_credits = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    price_eur = models.DecimalField(max_digits=10, decimal_places=2)
    price_ron = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    referral_bonus = models.DecimalField(max_digits=10, decimal_places=1, default=0,
                                       help_text="Bonus credits for both referrer and referee")
    expires_days = models.PositiveIntegerField(default=365,
                                             help_text="Days before purchased credits expire")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['base_credits']
        verbose_name = 'Credit Package'
        verbose_name_plural = 'Credit Packages'
    
    def __str__(self):
        return f"{self.tier.title()} - {self.total_credits} credits - €{self.price_eur}"

    @property
    def total_credits(self):
        return self.base_credits + self.bonus_credits

    def get_effective_price(self, currency='EUR'):
        """Calculate price per credit"""
        price = self.price_eur if currency == 'EUR' else self.price_ron
        return price / self.total_credits



class PremiumPlan(models.Model):
    """Premium subscription plans"""
    PLAN_TYPES = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    )
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="RON")
    credits_included = models.PositiveIntegerField(default=0)
    max_premium_listings = models.PositiveIntegerField(default=5)
    max_featured_listings = models.PositiveIntegerField(default=2)
    priority_support = models.BooleanField(default=True)
    analytics_access = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)  # List of features
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} ({self.plan_type})"


class CreditTransaction(models.Model):
    """Track all credit transactions"""
    TRANSACTION_TYPES = (
        ('purchase', 'Purchase'),
        ('spent', 'Spent'),
        ('bonus', 'Bonus'),
        ('refund', 'Refund'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()  # Can be negative for spent credits
    description = models.CharField(max_length=255)
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, blank=True, null=True)
    payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type}: {self.amount} credits"


class Payment(models.Model):
    """Track all payments made through Stripe"""
    PAYMENT_TYPES = (
        ('credits', 'Credits Purchase'),
        ('premium', 'Premium Subscription'),
        ('listing_boost', 'Listing Boost'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="RON")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict)  # Store additional data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.amount} {self.currency}"


class ListingBoost(models.Model):
    """Track listing boosts and premium features"""
    BOOST_TYPES = (
        ('featured', 'Featured Listing'),
        ('top_ad', 'Top Ad'),
        ('highlighted', 'Highlighted'),
        ('urgent', 'Urgent'),
    )
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='boosts')
    boost_type = models.CharField(max_length=20, choices=BOOST_TYPES)
    credits_cost = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField()
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    auto_repost = models.BooleanField(default=False)
    auto_repost_interval = models.PositiveIntegerField(null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.listing.title} - {self.boost_type}"
    
    @property
    def is_expired(self):
        """Check if boost has expired"""
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.starts_at + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)


class UserAnalytics(models.Model):
    """Track user analytics for premium users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    total_views = models.PositiveIntegerField(default=0)
    total_messages = models.PositiveIntegerField(default=0)
    total_favorites = models.PositiveIntegerField(default=0)
    total_listings = models.PositiveIntegerField(default=0)
    total_sales = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)
    monthly_data = models.JSONField(default=dict)  # Store monthly breakdown
    
    def __str__(self):
        return f"Analytics for {self.user.username}"
    
    def update_analytics(self):
        """Update analytics data"""
        from . import models  # Import to access Listing model
        self.total_listings = models.Listing.objects.filter(user=self.user).count()
        self.total_views = sum(listing.views for listing in models.Listing.objects.filter(user=self.user))
        self.total_messages = models.Message.objects.filter(receiver=self.user).count()
        
        # Calculate favorites for user's listings
        user_listings = models.Listing.objects.filter(user=self.user)
        self.total_favorites = sum(models.Favorite.objects.filter(listing=listing).count() for listing in user_listings)
        
        # Calculate conversion rate (favorites to messages ratio)
        if self.total_favorites > 0:
            self.conversion_rate = (self.total_messages / self.total_favorites) * 100
        
        self.save()


class Location(models.Model):
    """Model for managing locations and geographical data"""
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='România')
    location_type = models.CharField(max_length=50, choices=[
        ('city', 'City'),
        ('neighborhood', 'Neighborhood'),
        ('landmark', 'Landmark'),
        ('custom', 'Custom Location')
    ], default='city')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('latitude', 'longitude')
        indexes = [
            models.Index(fields=['city', 'county']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.name}, {self.city}, {self.county}"
    
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def distance_to(self, other_location):
        """Calculate distance to another location"""
        if isinstance(other_location, Location):
            return self.calculate_distance(
                float(self.latitude), float(self.longitude),
                float(other_location.latitude), float(other_location.longitude)
            )
        elif hasattr(other_location, 'latitude') and hasattr(other_location, 'longitude'):
            return self.calculate_distance(
                float(self.latitude), float(self.longitude),
                float(other_location.latitude), float(other_location.longitude)
            )
        return None


class ListingReport(models.Model):
    """Model for reporting inappropriate listings"""
    REASON_CHOICES = (
        ('spam', 'Spam sau anunț duplicat'),
        ('inappropriate', 'Conținut nepotrivit'),
        ('fake', 'Anunț fals'),
        ('price', 'Preț incorect sau înșelător'),
        ('contact', 'Informații de contact false'),
        ('copyright', 'Încălcarea drepturilor de autor'),
        ('other', 'Altul'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'În așteptare'),
        ('reviewed', 'Revizuit'),
        ('resolved', 'Rezolvat'),
        ('dismissed', 'Respins'),
    )
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='listing_reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='reviewed_reports')
    notes = models.TextField(blank=True, null=True, help_text="Admin notes")
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('listing', 'reporter')  # One report per user per listing
    
    def __str__(self):
        return f"Report #{self.id} - {self.get_reason_display()} by {self.reporter.username}"
