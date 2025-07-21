"""
AI Search Views for Piata.ro Marketplace
Provides REST API endpoints for AI-powered search and recommendations
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
import json
import logging

from marketplace.models import Listing, Category
from .enhanced_search import search_engine
from .recommendation_engine import recommendation_engine
from .image_recognition import image_recognition

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def ai_search(request):
    """
    AI-powered search endpoint
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        category = data.get('category')
        location = data.get('location')
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius_km = data.get('radius_km')
        limit = int(data.get('limit', 20))
        offset = int(data.get('offset', 0))
        
        # Perform hybrid search
        results = search_engine.hybrid_search(
            query=query,
            category=category,
            location=location,
            min_price=min_price,
            max_price=max_price,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
            offset=offset
        )
        
        # Format results
        formatted_results = []
        for result in results['results']:
            listing = result['listing']
            formatted_results.append({
                'id': listing.id,
                'title': listing.title,
                'description': listing.description,
                'price': float(listing.price) if listing.price else None,
                'currency': listing.currency,
                'location': listing.location,
                'city': listing.city,
                'county': listing.county,
                'category': listing.category.name,
                'category_slug': listing.category.slug,
                'images': [img.image.url for img in listing.images.all()[:3]],
                'created_at': listing.created_at.isoformat(),
                'score': result.get('final_score', result.get('score', 0)),
                'type': result.get('type', 'search')
            })
        
        return JsonResponse({
            'results': formatted_results,
            'total_count': results['total_count'],
            'has_more': results.get('has_more', False),
            'search_metadata': results.get('search_metadata', {})
        })
        
    except Exception as e:
        logger.error(f"AI search error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_recommendations(request):
    """
    Get personalized recommendations
    """
    try:
        data = json.loads(request.body)
        limit = int(data.get('limit', 10))
        category = data.get('category')
        location = data.get('location')
        
        if request.user.is_authenticated:
            # Get personalized recommendations
            recommendations = recommendation_engine.get_personalized_recommendations(
                user=request.user,
                limit=limit
            )
        else:
            # Get trending items for anonymous users
            recommendations = recommendation_engine.get_trending_items(
                category=category,
                location=location,
                limit=limit
            )
        
        # Format results
        formatted_recommendations = []
        for rec in recommendations:
            listing = rec['listing']
            formatted_recommendations.append({
                'id': listing.id,
                'title': listing.title,
                'description': listing.description[:200] + '...' if len(listing.description) > 200 else listing.description,
                'price': float(listing.price) if listing.price else None,
                'currency': listing.currency,
                'location': listing.location,
                'city': listing.city,
                'county': listing.county,
                'category': listing.category.name,
                'category_slug': listing.category.slug,
                'images': [img.image.url for img in listing.images.all()[:3]],
                'created_at': listing.created_at.isoformat(),
                'score': rec.get('score', 0),
                'reason': rec.get('reason', 'recommended')
            })
        
        return JsonResponse({
            'recommendations': formatted_recommendations,
            'total_count': len(formatted_recommendations)
        })
        
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_similar_items(request):
    """
    Get similar items for a given listing
    """
    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        limit = int(data.get('limit', 5))
        
        listing = get_object_or_404(Listing, id=listing_id)
        
        similar_items = recommendation_engine.get_similar_items(
            listing=listing,
            user=request.user if request.user.is_authenticated else None,
            limit=limit
        )
        
        # Format results
        formatted_items = []
        for item in similar_items:
            listing = item['listing']
            formatted_items.append({
                'id': listing.id,
                'title': listing.title,
                'description': listing.description[:150] + '...' if len(listing.description) > 150 else listing.description,
                'price': float(listing.price) if listing.price else None,
                'currency': listing.currency,
                'location': listing.location,
                'city': listing.city,
                'county': listing.county,
                'category': listing.category.name,
                'images': [img.image.url for img in listing.images.all()[:2]],
                'created_at': listing.created_at.isoformat(),
                'similarity_score': item.get('similarity_score', 0)
            })
        
        return JsonResponse({
            'similar_items': formatted_items,
            'total_count': len(formatted_items)
        })
        
    except Exception as e:
        logger.error(f"Similar items error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_trending_items(request):
    """
    Get trending items
    """
    try:
        data = json.loads(request.body)
        category = data.get('category')
        location = data.get('location')
        days = int(data.get('days', 7))
        limit = int(data.get('limit', 10))
        
        trending_items = recommendation_engine.get_trending_items(
            category=category,
            location=location,
            days=days,
            limit=limit
        )
        
        # Format results
        formatted_items = []
        for item in trending_items:
            listing = item['listing']
            formatted_items.append({
                'id': listing.id,
                'title': listing.title,
                'description': listing.description[:150] + '...' if len(listing.description) > 150 else listing.description,
                'price': float(listing.price) if listing.price else None,
                'currency': listing.currency,
                'location': listing.location,
                'city': listing.city,
                'county': listing.county,
                'category': listing.category.name,
                'images': [img.image.url for img in listing.images.all()[:2]],
                'created_at': listing.created_at.isoformat(),
                'trending_score': item.get('trending_score', 0),
                'reason': item.get('reason', 'trending')
            })
        
        return JsonResponse({
            'trending_items': formatted_items,
            'total_count': len(formatted_items)
        })
        
    except Exception as e:
        logger.error(f"Trending items error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_price_recommendations(request):
    """
    Get price recommendations for a listing
    """
    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        
        listing = get_object_or_404(Listing, id=listing_id)
        
        price_recommendations = recommendation_engine.get_price_recommendations(listing)
        
        return JsonResponse(price_recommendations)
        
    except Exception as e:
        logger.error(f"Price recommendations error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def analyze_listing_images(request):
    """
    Analyze images for a listing using AI
    """
    try:
        data = json.loads(request.body)
        listing_id = data.get('listing_id')
        
        listing = get_object_or_404(Listing, id=listing_id)
        
        # Analyze images
        analysis_result = image_recognition.auto_tag_listing(listing)
        
        return JsonResponse(analysis_result)
        
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_search_suggestions(request):
    """
    Get search suggestions
    """
    try:
        query = request.GET.get('query', '')
        limit = int(request.GET.get('limit', 5))
        
        suggestions = search_engine.get_search_suggestions(query)
        
        return JsonResponse({
            'suggestions': suggestions,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
