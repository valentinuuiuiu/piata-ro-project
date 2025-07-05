

from django.shortcuts import render
from django.views.decorators.http import require_GET

@require_GET
def terms_of_service_view(request):
    """View for displaying terms of service"""
    return render(request, 'marketplace/legal/terms_of_service.html')

@require_GET
def privacy_policy_view(request):
    """View for displaying privacy policy"""
    return render(request, 'marketplace/legal/privacy_policy.html')

@require_GET
def cookie_policy_view(request):
    """View for displaying cookie policy"""
    return render(request, 'marketplace/legal/cookie_policy.html')

@require_GET
def about_view(request):
    """View for displaying about us page"""
    return render(request, 'marketplace/legal/about.html')

@require_GET
def help_view(request):
    """View for displaying help/FAQ page"""
    return render(request, 'marketplace/legal/help.html')

