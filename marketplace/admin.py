from django.contrib import admin
from django.db import models
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import format_html
from django.contrib.admin import AdminSite
import json
import asyncio
import httpx
from datetime import datetime

from .models import Category, Favorite, Listing, Message, UserProfile, ListingReport, Location, ListingImage
from .models_chat import ChatConversation, ChatMessage
from .admin_location import location_admin


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ('image', 'thumbnail_preview', 'is_main', 'order')
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.thumbnail.url)
        return "-"
    thumbnail_preview.short_description = 'Thumbnail Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "listing_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    
    def listing_count(self, obj):
        return obj.listing_set.count()
    listing_count.short_description = 'Listings'


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "price",
        "currency",
        "location",
        "user",
        "category",
        "status",
        "created_at",
        "has_coordinates",
        "main_image_preview"
    )
    list_filter = ("status", "is_premium", "is_verified", "category", "location_verified")
    search_fields = ("title", "description", "location", "city")
    date_hierarchy = "created_at"
    actions = ['populate_coordinates']
    inlines = [ListingImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'price', 'currency', 'user', 'status')
        }),
        ('Location Information', {
            'fields': ('location', 'city', 'county', 'latitude', 'longitude', 'location_verified'),
            'classes': ('collapse',)
        }),
        ('Premium Features', {
            'fields': ('is_premium', 'is_verified', 'is_featured'),
            'classes': ('collapse',)
        })
    )
    
    def has_coordinates(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<span style="color: green;">✓ ({}, {})</span>',
                obj.latitude, obj.longitude
            )
        return format_html('<span style="color: red;">✗ Missing</span>')
    has_coordinates.short_description = 'Coordinates'
    
    def main_image_preview(self, obj):
        img = obj.main_image
        if img and img.thumbnail:
            return format_html('<img src="{}" style="max-height: 50px;"/>', img.thumbnail.url)
        return "-"
    main_image_preview.short_description = 'Main Image'
    
    def populate_coordinates(self, request, queryset):
        from .services.location_service import location_service
        updated = 0
        for listing in queryset:
            if location_service.populate_listing_coordinates(listing):
                updated += 1
        
        self.message_user(
            request,
            f'Successfully updated coordinates for {updated} listings.'
        )
    populate_coordinates.short_description = "Populate missing coordinates"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "listing", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("content", "sender__username", "receiver__username")
    date_hierarchy = "created_at"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "listing__title")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "location", "is_premium", "premium_until")
    list_filter = ("is_premium",)
    search_fields = ("user__username", "user__email", "phone", "location")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'location_type']
    list_filter = ['location_type']
    search_fields = ['name']


@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "reporter", "reason", "status", "created_at")
    list_filter = ("reason", "status", "created_at")
    search_fields = ("listing__title", "reporter__username", "comment")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {"fields": ("listing", "reporter", "reason", "comment")}),
        (
            "Status",
            {"fields": ("status", "reviewed_by", "reviewed_at", "notes")},
        ),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    def save_model(self, request, obj, form, change):
        if change and obj.status in ["reviewed", "resolved", "dismissed"]:
            if not obj.reviewed_by:
                obj.reviewed_by = request.user
            if not obj.reviewed_at:
                from django.utils import timezone
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


# Custom AdminSite to add our location analytics
class PiataRoAdminSite(AdminSite):
    site_header = "Piața.ro Administration"
    site_title = "Piața.ro Admin"
    index_title = "Welcome to Piața.ro Administration"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('location-analytics/', location_admin.location_analytics_view, name='location_analytics'),
            path('location-health/', location_admin.location_health_api, name='location_health_api'),
        ]
        return custom_urls + urls
    
    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request, app_label)
        
        # Add our custom analytics link to the marketplace app
        if 'marketplace' in app_dict:
            app_dict['marketplace']['models'].append({
                'name': 'Location Analytics',
                'object_name': 'LocationAnalytics',
                'perms': {'view': True},
                'admin_url': '/admin/location-analytics/',
                'add_url': None,
                'view_only': True,
            })
        
        # Sort the models alphabetically within each app.
        for app in app_dict.values():
            app['models'].sort(key=lambda x: x['name'])
        
        return app_dict.values()


# Override the default admin site
admin_site = PiataRoAdminSite(name='admin')

# Re-register all models with the custom admin site
admin_site.register(Category, CategoryAdmin)
admin_site.register(Listing, ListingAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(Favorite, FavoriteAdmin)
admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(Location, LocationAdmin)
admin_site.register(ListingReport, ListingReportAdmin)


# Admin Assistant Implementation for default admin site
class AdminAssistant:
    def __init__(self, request):
        self.request = request
        self.agent_url = "http://localhost:8001/process"

    async def query(self, message):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.agent_url,
                    json={
                        "query": message,
                        "context": {
                            "user_id": str(self.request.user.id),
                            "is_admin": True
                        }
                    },
                    timeout=10.0
                )
                return response.json()["response"]
        except Exception as e:
            return f"Assistant error: {str(e)}"

def admin_site_view(request):
    assistant = AdminAssistant(request)
    
    if request.method == "POST":
        message = request.POST.get("message", "")
        response = asyncio.run(assistant.query(message))
        return JsonResponse({"response": response})
    
    return render(request, "admin/assistant.html")

# Register admin assistant view via ModelAdmin
class AdminAssistantAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "assistant/",
                self.admin_site.admin_view(admin_site_view),
                name="admin-assistant"
            ),
        ]
        return custom_urls + urls

# Create a dummy model to attach our admin view
class AdminAssistantModel(models.Model):
    class Meta:
        verbose_name = "Admin Assistant"
        verbose_name_plural = "Admin Assistants"
        managed = False  # Don't create DB table
        default_permissions = ()

# Register the dummy model with our custom admin site
admin.site.register(AdminAssistantModel, AdminAssistantAdmin)
admin_site.register(AdminAssistantModel, AdminAssistantAdmin)
