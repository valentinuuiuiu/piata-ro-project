"""
Monitoring views for admin interface
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views import View
from marketplace.services.monitoring_service import MonitoringService

@method_decorator(never_cache, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class MonitoringDashboardView(View):
    """Monitoring dashboard view for admin"""
    
    def get(self, request):
        """Render monitoring dashboard"""
        context = {
            'title': 'System Monitoring Dashboard',
        }
        return render(request, 'admin/monitoring_dashboard.html', context)

@method_decorator(never_cache, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class HealthAPIView(View):
    """API endpoint for health status"""
    
    def get(self, request):
        try:
            health_status = MonitoringService.get_health_status()
            return JsonResponse(health_status)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(never_cache, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class SummaryAPIView(View):
    """API endpoint for daily summary"""
    
    def get(self, request):
        try:
            date = request.GET.get('date')
            summary = MonitoringService.get_daily_summary(date)
            return JsonResponse(summary)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(never_cache, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class SystemAPIView(View):
    """API endpoint for system metrics"""
    
    def get(self, request):
        try:
            system_metrics = MonitoringService.get_system_metrics()
            return JsonResponse(system_metrics)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
