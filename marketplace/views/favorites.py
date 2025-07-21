from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from ..models import Listing, UserProfile, Favorite

@login_required
@require_POST
def toggle_favorite_view(request, listing_id):
    """Toggle favorite status for a listing"""
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Check if already favorited
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing
    )
    
    # If it existed and we didn't create it, then delete it
    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True
    
    return JsonResponse({
        'success': True,
        'is_favorited': is_favorited,
        'listing_id': listing_id,
        'favorites_count': listing.favorited_by.count()
    })

def show_phone_view(request, listing_id):
    """Show phone number for a listing"""
    listing = get_object_or_404(Listing, id=listing_id)
    
    # Get seller's profile
    try:
        profile = UserProfile.objects.get(user=listing.user)
        phone = profile.phone
    except UserProfile.DoesNotExist:
        phone = None
    
    # Record that this user viewed the phone number
    # This could be used for analytics or limiting views
    
    return JsonResponse({
        'success': True,
        'phone': phone or "Număr de telefon indisponibil",
        'listing_id': listing_id
    })