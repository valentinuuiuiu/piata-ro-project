from django.http import JsonResponse
from django.views.decorators.http import require_GET
from ..location_services import LocationService

@require_GET
def location_search_api(request):
    """API endpoint for location search"""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if not query or len(query.strip()) < 2:
        return JsonResponse({'results': [], 'error': 'Query too short'})
    
    try:
        results = LocationService.search_locations(query, limit)
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def reverse_geocode_api(request):
    """API endpoint for reverse geocoding"""
    try:
        lat = float(request.GET.get('lat', 0))
        lon = float(request.GET.get('lon', 0))
        
        if not lat or not lon:
            return JsonResponse({'error': 'Missing coordinates'}, status=400)
        
        result = LocationService.reverse_geocode(lat, lon)
        if result:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': 'No results found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def geocode_api(request):
    """API endpoint for geocoding addresses"""
    address = request.GET.get('address', '')
    city = request.GET.get('city', '')
    
    if not address and not city:
        return JsonResponse({'error': 'Missing address or city'}, status=400)
    
    try:
        result = LocationService.geocode_address(address, city)
        if result:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': 'No results found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)