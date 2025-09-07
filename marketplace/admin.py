"""
Django Admin configuration for Marketplace models
"""
from django.contrib import admin
from django.utils import timezone
from .models import (
    Category, Listing, ListingImage, Message, Favorite, 
    UserProfile, CreditPackage, PremiumPlan, CreditTransaction,
    Payment, ListingBoost, UserAnalytics, Location, ListingReport
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'get_listings_count']
    search_fields = ['name', 'slug']
    list_filter = ['parent']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'price', 'currency', 'status', 'created_at', 'is_featured']
    list_filter = ['status', 'category', 'is_featured', 'is_premium', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'views']
    filter_horizontal = []
    date_hierarchy = 'created_at'

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ['listing', 'is_main', 'order', 'created_at']
    list_filter = ['is_main', 'created_at']
    search_fields = ['listing__title']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'listing', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['created_at']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'listing', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'listing__title']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'location', 'is_premium', 'credits_balance']
    list_filter = ['is_premium', 'mfa_enabled']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'total_credits', 'price_eur', 'price_ron', 'is_active']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'description']

@admin.register(PremiumPlan)
class PremiumPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'currency', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name', 'description']

@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'payment_type', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['payment_type', 'status', 'created_at']
    search_fields = ['user__username', 'stripe_payment_intent_id']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(ListingBoost)
class ListingBoostAdmin(admin.ModelAdmin):
    list_display = ['listing', 'boost_type', 'credits_cost', 'starts_at', 'expires_at', 'is_active']
    list_filter = ['boost_type', 'is_active', 'starts_at']
    search_fields = ['listing__title']
    readonly_fields = ['created_at']

@admin.register(UserAnalytics)
class UserAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_views', 'total_messages', 'total_favorites', 'last_updated']
    readonly_fields = ['last_updated']
    search_fields = ['user__username']

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'county', 'location_type', 'is_active']
    list_filter = ['location_type', 'is_active', 'county']
    search_fields = ['name', 'city', 'county']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = ['listing', 'reporter', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['listing__title', 'reporter__username']
    readonly_fields = ['created_at', 'reviewed_at']
    actions = ['mark_as_reviewed', 'mark_as_resolved']

    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_reviewed.short_description = "Mark selected reports as reviewed"

    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', reviewed_by=request.user, reviewed_at=timezone.now())
    mark_as_resolved.short_description = "Mark selected reports as resolved"
