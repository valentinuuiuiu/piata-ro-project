
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from ..models import Listing, Category

@cache_page(60 * 15)  # Cache for 15 minutes
def listing_detail(request, slug):
    """Listing detail view with caching"""
    listing = get_object_or_404(
        Listing.objects.select_related('user', 'category'),
        slug=slug,
        status='active'
    )
    return render(request, 'marketplace/listing_detail.html', {'listing': listing})

def listing_list(request):
    """Paginated listing list view"""
    listings = Listing.objects.filter(status='active').select_related('category')
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'marketplace/listing_list.html', {'listings': page_obj})
