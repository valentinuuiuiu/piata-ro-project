"""
Admin interface for the monitoring system
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
import json
from datetime import datetime, timedelta
from django.utils import timezone
from marketplace.services.monitoring_service import MonitoringService

def is_staff_user(user):
    """Check if user is staff member"""
    return user.is_staff

@method_decorator(never_cache, name='dispatch')
class MonitoringAdmin(admin.AdminSite):
    """Custom admin site for monitoring"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('monitoring/', self.admin_view(self.monitoring_dashboard), name='monitoring_dashboard'),
            path('monitoring/api/health/', self.admin_view(self.health_api), name='monitoring_health_api'),
            path('monitoring/api/summary/', self.admin_view(self.summary_api), name='monitoring_summary_api'),
            path('monitoring/api/system/', self.admin_view(self.system_api), name='monitoring_system_api'),
        ]
        # Return the combined list of custom and default URLs
        return custom_urls + urls
    
    @user_passes_test(is_staff_user)
    def monitoring_dashboard(self, request):
        """Render monitoring dashboard"""
        context = {
            'title': 'System Monitoring Dashboard',
            **self.each_context(request),
        }
        return render(request, 'admin/monitoring_dashboard.html', context)
    
    @user_passes_test(is_staff_user)
    def health_api(self, request):
        """API endpoint for health status"""
        try:
            health_status = MonitoringService.get_health_status()
            return JsonResponse(health_status)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    @user_passes_test(is_staff_user)
    def summary_api(self, request):
        """API endpoint for daily summary"""
        try:
            date = request.GET.get('date')
            summary = MonitoringService.get_daily_summary(date)
            return JsonResponse(summary)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    @user_passes_test(is_staff_user)
    def system_api(self, request):
        """API endpoint for system metrics"""
        try:
            system_metrics = MonitoringService.get_system_metrics()
            return JsonResponse(system_metrics)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# Create monitoring admin instance
monitoring_admin = MonitoringAdmin(name='monitoring')

# Register monitoring views with the main admin site
def register_monitoring_admin(admin_site):
    """Register monitoring admin with the main admin site"""
    admin_site.get_urls = lambda: monitoring_admin.get_urls() + admin_site.get_urls()
