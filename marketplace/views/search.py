

from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from ..models import Listing

def search(request):
    """Unified search view"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    
    results = Listing.objects.filter(status='active')
    
    if query:
        results = results.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    if category:
        results = results.filter(category__slug=category)
        
    if location:
        results = results.filter(
            Q(city__iexact=location) |
            Q(county__iexact=location)
        )
    
    paginator = Paginator(results.select_related('category'), 20)
    return render(request, 'marketplace/search_results.html', {
        'results': paginator.get_page(request.GET.get('page')),
        'query': query
    })

