
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from ..models import Listing, Category

@cache_page(60 * 15)  # Cache for 15 minutes
def listing_detail(request, slug):
    """Listing detail view with caching"""
    try:
        # Try to get by slug first
        try:
            listing = get_object_or_404(
                Listing.objects.select_related('user', 'category'),
                slug=slug,
                status='active'
            )
        except:
            # If slug fails, try by ID (for backward compatibility)
            listing = get_object_or_404(
                Listing.objects.select_related('user', 'category'),
                id=slug,
                status='active'
            )
        
        return render(request, 'marketplace/listing_detail.html', {'listing': listing})
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f"Error loading listing: {str(e)}")
        return redirect('marketplace:listings')

def listing_list(request):
    """Paginated listing list view"""
    # Get all active listings
    listings = Listing.objects.filter(status='active').select_related('category', 'user')
    
    # Apply filters
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    if search_query:
        listings = listings.filter(title__icontains=search_query)
    
    if category_id and category_id.isdigit():
        listings = listings.filter(category_id=category_id)
    
    if min_price and min_price.isdigit():
        listings = listings.filter(price__gte=min_price)
    
    if max_price and max_price.isdigit():
        listings = listings.filter(price__lte=max_price)
    
    if location:
        listings = listings.filter(location__icontains=location)
    
    # Apply sorting
    listings = listings.order_by(sort_by)
    
    # Get all categories for the filter dropdown
    categories = Category.objects.filter(parent__isnull=True)
    
    # Paginate results
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'marketplace/listings.html', {
        'listings': page_obj,
        'categories': categories
    })
