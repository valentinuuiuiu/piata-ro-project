

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from ..models import Category, Listing

@cache_page(60 * 60)  # Cache for 1 hour
def category_list(request):
    """All categories view"""
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    return render(request, 'marketplace/category_list.html', {'categories': categories})

def category_detail(request, slug):
    """Category detail with listings"""
    category = get_object_or_404(Category, slug=slug)
    listings = category.listings.filter(status='active').select_related('user')
    paginator = Paginator(listings, 20)
    return render(request, 'marketplace/category_detail.html', {
        'category': category,
        'listings': paginator.get_page(request.GET.get('page'))
    })

