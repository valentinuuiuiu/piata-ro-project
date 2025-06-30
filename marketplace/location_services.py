"""
Location services for the marketplace application.
Provides utilities for geocoding, reverse geocoding, and location-based search.
"""

import requests
import time
from django.conf import settings
from django.core.cache import cache
from typing import Dict, List, Optional, Tuple
import logging
from decimal import Decimal
from ratelimit import limits, sleep_and_retry

# Nominatim usage policy requires max 1 request per second
NOMINATIM_RATE_LIMIT = 1  # requests per second

logger = logging.getLogger(__name__)

@sleep_and_retry
@limits(calls=NOMINATIM_RATE_LIMIT, period=1)
def call_nominatim(params):
    headers = {
        'User-Agent': 'PiataRo/1.0 (marketplace application)'
    }
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params=params,
        headers=headers,
        timeout=5
    )
    response.raise_for_status()
    return response.json()


class LocationService:
    """Service for handling location-related operations"""
    
    # Romania's major cities with coordinates for fallback
    ROMANIA_CITIES = {
        'București': (44.4268, 26.1025),
        'Cluj-Napoca': (46.7712, 23.6236),
        'Iași': (47.1585, 27.6014),
        'Timișoara': (45.7489, 21.2087),
        'Constanța': (44.1598, 28.6348),
        'Craiova': (44.3302, 23.7949),
        'Brașov': (45.6427, 25.5887),
        'Galați': (45.4353, 28.0080),
        'Ploiești': (44.9536, 26.0123),
        'Oradea': (47.0465, 21.9189),
        'Brăila': (45.2692, 27.9574),
        'Arad': (46.1865, 21.3123),
        'Pitești': (44.8565, 24.8692),
        'Sibiu': (45.7983, 24.1256),
        'Bacău': (46.5670, 26.9146),
        'Târgu Mureș': (46.5527, 24.5582),
        'Baia Mare': (47.6567, 23.5846),
        'Buzău': (45.1500, 26.8203),
        'Botoșani': (47.7402, 26.6656),
        'Satu Mare': (47.7914, 22.8816),
    }
    
    @staticmethod
    def normalize_location_name(location: str) -> str:
        """Normalize location name for consistency"""
        if not location:
            return ""
        
        # Remove extra spaces and normalize case
        location = location.strip().title()
        
        # Handle common variations
        replacements = {
            'Bucuresti': 'București',
            'Bucharest': 'București',
            'Cluj': 'Cluj-Napoca',
            'Iasi': 'Iași',
            'Timisoara': 'Timișoara',
            'Constanta': 'Constanța',
            'Brasov': 'Brașov',
            'Galati': 'Galați',
            'Ploiesti': 'Ploiești',
            'Braila': 'Brăila',
            'Pitesti': 'Pitești',
            'Targu Mures': 'Târgu Mureș',
            'Botosani': 'Botoșani',
        }
        
        for old, new in replacements.items():
            if location.lower() == old.lower():
                return new
        
        return location
    
    @staticmethod
    def get_coordinates_from_city(city: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a Romanian city"""
        normalized_city = LocationService.normalize_location_name(city)
        return LocationService.ROMANIA_CITIES.get(normalized_city)
    
    @staticmethod
    def geocode_address(address: str, city: Optional[str] = None, country: str = "România") -> Optional[Dict]:
        """
        Geocode an address using OpenStreetMap Nominatim API (free)
        Returns dict with latitude, longitude, and formatted address
        """
        if not address and not city:
            return None
        
        # Create cache key
        cache_key = f"geocode_{address}_{city}_{country}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        # Use OpenStreetMap Nominatim API with rate limiting

        query_parts = []
        def call_nominatim(params):
            headers = {
                'User-Agent': 'PiataRo/1.0 (marketplace application)'
            }
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()

        try:
            query_parts = []
            if address:
                query_parts.append(address)
            if city:
                query_parts.append(city)
            query_parts.append(country)
            
            query = ", ".join(query_parts)
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'ro' if country.lower() in ['romania', 'românia'] else None,
                'addressdetails': 1
            }
            
            data = call_nominatim(params)
            if data:
                result = data[0]
                geocoded = {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'formatted_address': result.get('display_name', query),
                    'city': result.get('address', {}).get('city') or city,
                    'country': result.get('address', {}).get('country') or country
                }
                
                # Cache successful result
                cache.set(cache_key, geocoded, 86400)
                return geocoded
                
        except Exception as e:
            logger.error(f"Geocoding failed for '{query}': {e}")
        
        return None
    
    @staticmethod
    def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Reverse geocode coordinates to get address information
        """
        cache_key = f"reverse_geocode_{latitude}_{longitude}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1
            }
            
            data = call_nominatim(params)
            if data and 'address' in data:
                address_info = data['address']
                result = {
                    'formatted_address': data.get('display_name', ''),
                    'address': address_info.get('road', '') or address_info.get('house_number', ''),
                    'city': (
                        address_info.get('city') or 
                        address_info.get('town') or 
                        address_info.get('village') or 
                        address_info.get('municipality', '')
                    ),
                    'county': address_info.get('county', ''),
                    'postal_code': address_info.get('postcode', ''),
                    'country': address_info.get('country', 'România')
                }
                
                # Cache successful result
                cache.set(cache_key, result, 86400)
                return result
                
        except Exception as e:
            logger.error(f"Reverse geocoding failed for {latitude}, {longitude}: {e}")
        
        return None
    
    @staticmethod
    def search_locations(query: str, limit: int = 10) -> List[Dict]:
        """Search for locations matching a query"""
        cache_key = f"location_search_{query}_{limit}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        results = []
        
        # First, search in our known Romanian cities
        query_lower = query.lower()
        for city, coords in LocationService.ROMANIA_CITIES.items():
            if query_lower in city.lower():
                results.append({
                    'name': city,
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'type': 'city',
                    'formatted_address': f"{city}, România"
                })
        
        # If we have enough results, return them
        if len(results) >= limit:
            cache.set(cache_key, results[:limit], 3600)
            return results[:limit]
        
        # Otherwise, search using Nominatim
        try:
            params = {
                'q': f"{query}, România",
                'format': 'json',
                'limit': limit - len(results),
                'countrycodes': 'ro',
                'addressdetails': 1
            }
            
            data = call_nominatim(params)
            for item in data:
                address = item.get('address', {})
                results.append({
                    'name': item.get('display_name', ''),
                    'latitude': float(item['lat']),
                    'longitude': float(item['lon']),
                    'type': item.get('type', 'location'),
                    'formatted_address': item.get('display_name', ''),
                    'city': address.get('city') or address.get('town') or address.get('village', ''),
                    'county': address.get('county', '')
                })
                
        except Exception as e:
            logger.error(f"Location search failed for '{query}': {e}")
        
        # Cache results
        cache.set(cache_key, results[:limit], 3600)
        return results[:limit]
    
    @staticmethod
    def populate_listing_coordinates(listing):
        """Populate coordinates for a listing based on its location data"""
        if listing.latitude and listing.longitude:
            return True  # Already has coordinates
        
        # Try to geocode based on available information
        address = listing.address or listing.location
        city = listing.city or listing.location
        
        geocoded = LocationService.geocode_address(address, city)
        if geocoded:
            listing.latitude = Decimal(str(geocoded['latitude']))
            listing.longitude = Decimal(str(geocoded['longitude']))
            if not listing.city and geocoded.get('city'):
                listing.city = geocoded['city']
            if not listing.address and address != city:
                listing.formatted_address = geocoded['formatted_address']
            listing.location_verified = True
            listing.save()
            return True
        
        return False
