"""
Admin views for location service monitoring
"""

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import path
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

def is_staff_user(user):
    """Check if user is staff member"""
    return user.is_authenticated and user.is_staff

class LocationServiceAdmin:
    """Admin interface for location service monitoring"""
    
    def get_urls(self):
        return [
            path('location-analytics/', self.location_analytics_view, name='location_analytics'),
            path('location-health/', self.location_health_api, name='location_health_api'),
        ]
    
    @user_passes_test(is_staff_user)
    def location_analytics_view(self, request):
        """Render location analytics dashboard"""
        context = {
            'title': 'Location Service Analytics',
            'current_date': timezone.now().strftime('%Y-%m-%d'),
        }
        return render(request, 'admin/location_analytics.html', context)
    
    @user_passes_test(is_staff_user)
    @require_http_methods(["GET"])
    def location_health_api(self, request):
        """API endpoint for location service health data"""
        try:
            from marketplace.services.location_analytics import LocationAnalytics
            
            period = request.GET.get('period', 'daily')
            
            if period == 'weekly':
                stats = LocationAnalytics.get_weekly_stats()
            else:
                date = request.GET.get('date')
                stats = LocationAnalytics.get_daily_stats(date)
            
            health = LocationAnalytics.get_service_health()
            popular = LocationAnalytics.get_popular_locations()
            
            return JsonResponse({
                'success': True,
                'period': period,
                'stats': stats,
                'health': health,
                'popular_locations': popular
            })
            
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'Analytics not available',
                'stats': {},
                'health': {'status': 'unknown'},
                'popular_locations': []
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'stats': {},
                'health': {'status': 'error'},
                'popular_locations': []
            })

# Register the custom admin
location_admin = LocationServiceAdmin()
