
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Favorite

@login_required
def favorites_view(request):
    """View for displaying user's favorite listings"""
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('listing').order_by('-created_at')
    return render(request, 'marketplace/favorites.html', {
        'favorites': favorites
    })

@login_required
def toggle_favorite_view(request, listing_id):
    """View for toggling favorite status of a listing"""
    from django.http import JsonResponse
    from ..models import Listing
    
    listing = Listing.objects.get(id=listing_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing
    )
    
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})
