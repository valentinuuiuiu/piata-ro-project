from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def location_picker_view(request):
    """View for the location picker map"""
    return render(request, 'marketplace/location_picker.html')

def location_picker_modal(request):
    """View for the location picker modal"""
    return render(request, 'marketplace/location_picker_modal.html')