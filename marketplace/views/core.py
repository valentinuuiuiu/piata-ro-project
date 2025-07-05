


from django.shortcuts import render
from django.views.decorators.cache import cache_page
from ..models import Listing, Category

@cache_page(60 * 15)  # Cache for 15 minutes
def home_view(request):
    """Homepage view showing featured listings"""
    featured = Listing.objects.filter(
        status='active',
        is_featured=True
    ).select_related('category', 'user')[:12]
    categories = Category.objects.filter(parent__isnull=True)[:8]
    return render(request, 'marketplace/home.html', {
        'featured_listings': featured,
        'categories': categories
    })

def categories_view(request):
    """All categories listing"""
    categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'marketplace/categories.html', {
        'categories': categories
    })

def listings_view(request):
    """All active listings"""
    listings = Listing.objects.filter(status='active')
    return render(request, 'marketplace/listings.html', {
        'listings': listings
    })


