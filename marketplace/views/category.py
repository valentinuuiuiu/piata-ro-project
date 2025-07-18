

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from ..models import Category, Listing

@cache_page(60 * 60)  # Cache for 1 hour
def category_list(request):
    """All categories view"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Category list view accessed")
        categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
        logger.info(f"Found {categories.count()} parent categories")
        
        # Debug: Check if subcategories are accessible
        for category in categories:
            try:
                subcategories_count = category.subcategories.count()
                logger.info(f"Category {category.name} has {subcategories_count} subcategories")
            except Exception as e:
                logger.error(f"Error accessing subcategories for {category.name}: {e}")
        
        # Try to get featured categories
        try:
            featured_categories = Category.objects.filter(parent__isnull=True)[:5]
            context = {
                'categories': categories,
                'featured_categories': featured_categories
            }
        except Exception as e:
            logger.error(f"Error getting featured categories: {e}")
            context = {'categories': categories}
        
        return render(request, 'marketplace/categories.html', context)
    except Exception as e:
        import traceback
        logger.error(f"Error in category_list view: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return render(request, 'marketplace/error.html', {'error': str(e)})

def category_detail(request, slug):
    """Category detail with listings"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Category detail view accessed for slug: {slug}")
        category = get_object_or_404(Category, slug=slug)
        logger.info(f"Found category: {category.name}")
        
        try:
            listings = category.listings.filter(status='active').select_related('user')
            listings_count = listings.count()
            logger.info(f"Found {listings_count} active listings for category {category.name}")
            
            paginator = Paginator(listings, 20)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            return render(request, 'marketplace/category_detail.html', {
                'category': category,
                'listings': page_obj
            })
        except Exception as e:
            logger.error(f"Error getting listings for category {category.name}: {e}")
            raise
    except Exception as e:
        import traceback
        logger.error(f"Error in category_detail view: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return render(request, 'marketplace/error.html', {'error': str(e)})

