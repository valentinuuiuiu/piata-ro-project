


from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
from ..models import Listing, Category
import logging

logger = logging.getLogger(__name__)

@cache_page(60 * 15)  # Cache for 15 minutes
def home_view(request):
    """Homepage view showing featured listings"""
    try:
        logger.info("Home view accessed")
        featured = Listing.objects.filter(
            status='active',
            is_featured=True
        ).select_related('category', 'user')[:12]
        categories = Category.objects.filter(parent__isnull=True)[:8]
        
        logger.info(f"Found {featured.count()} featured listings and {categories.count()} categories")
        
        context = {
            'featured_listings': featured,
            'categories': categories
        }
        
        # Debug logging
        logger.info(f"Rendering template with context keys: {list(context.keys())}")
        
        return render(request, 'marketplace/index.html', context)
    except Exception as e:
        import traceback
        logger.error(f"Error in home_view: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return HttpResponse(f"Error: {e}", status=500)

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


