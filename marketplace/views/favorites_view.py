from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Favorite

@login_required
def favorites_view(request):
    """View for displaying user's favorite listings"""
    favorites = Favorite.objects.filter(user=request.user).select_related('listing')
    
    return render(request, 'marketplace/favorites.html', {
        'favorites': favorites
    })