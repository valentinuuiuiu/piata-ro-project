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
def call_nominatim(params, endpoint="search"):
    """
    Call Nominatim API with proper rate limiting and error handling
    """
    headers = {
        'User-Agent': 'PiataRo/2.0 (marketplace@piata.ro; support@piata.ro)'
    }
    
    base_url = "https://nominatim.openstreetmap.org"
    url = f"{base_url}/{endpoint}"
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        # Log successful requests for monitoring
        logger.debug(f"Nominatim API call successful: {endpoint} - {params.get('q', params.get('lat', 'N/A'))}")
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Nominatim API error for {endpoint}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error calling Nominatim: {e}")
        raise


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
        Enhanced geocoding using OpenStreetMap Nominatim API with multiple query strategies
        Returns dict with latitude, longitude, and formatted address
        """
        if not address and not city:
            return None
        
        # Create cache key
        cache_key = f"geocode_{address}_{city}_{country}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Try multiple query strategies for better results
        query_strategies = []
        
        if address and city:
            # Strategy 1: Full address with city
            query_strategies.append(f"{address}, {city}, {country}")
            # Strategy 2: Just city (fallback)
            query_strategies.append(f"{city}, {country}")
            # Strategy 3: Address without city
            query_strategies.append(f"{address}, {country}")
        elif address:
            # Strategy 1: Address only
            query_strategies.append(f"{address}, {country}")
            # Strategy 2: Try to extract city from address
            address_parts = address.split(',')
            if len(address_parts) > 1:
                possible_city = address_parts[-1].strip()
                query_strategies.append(f"{possible_city}, {country}")
        elif city:
            # Strategy 1: City only
            query_strategies.append(f"{city}, {country}")

        for query in query_strategies:
            try:
                params = {
                    'q': query,
                    'format': 'json',
                    'limit': 3,  # Get top 3 results for better accuracy
                    'countrycodes': 'ro' if country.lower() in ['romania', 'românia'] else None,
                    'addressdetails': 1,
                    'extratags': 1  # Get additional information
                }
                
                data = call_nominatim(params, "search")
                if data:
                    # Select best result based on ranking and type
                    best_result = None
                    for result in data:
                        # Prefer results with higher importance score
                        importance = float(result.get('importance', 0))
                        if not best_result or importance > float(best_result.get('importance', 0)):
                            best_result = result
                    
                    if best_result:
                        address_info = best_result.get('address', {})
                        geocoded = {
                            'latitude': float(best_result['lat']),
                            'longitude': float(best_result['lon']),
                            'formatted_address': best_result.get('display_name', query),
                            'city': (
                                address_info.get('city') or 
                                address_info.get('town') or 
                                address_info.get('village') or 
                                city
                            ),
                            'county': address_info.get('county', ''),
                            'country': address_info.get('country', country),
                            'postal_code': address_info.get('postcode', ''),
                            'importance': float(best_result.get('importance', 0)),
                            'place_type': best_result.get('type', 'unknown')
                        }
                        
                        # Cache successful result
                        cache.set(cache_key, geocoded, 86400)
                        logger.info(f"✅ Geocoded: {query} -> {geocoded['latitude']}, {geocoded['longitude']} (importance: {geocoded['importance']})")
                        return geocoded
                        
            except Exception as e:
                logger.warning(f"Geocoding attempt failed for '{query}': {e}")
                continue
        
        logger.warning(f"❌ All geocoding strategies failed for address: {address}, city: {city}")
        return None
    
    @staticmethod
    def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Enhanced reverse geocode coordinates to get address information
        """
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            logger.error(f"Invalid coordinates: lat={latitude}, lng={longitude}")
            return None
        
        cache_key = f"reverse_geocode_{latitude:.6f}_{longitude:.6f}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1,
                'extratags': 1,
                'zoom': 18  # High zoom for detailed results
            }
            
            data = call_nominatim(params, "reverse")
            if data and 'address' in data:
                address_info = data['address']
                
                # Extract address components with fallbacks
                road = address_info.get('road', '')
                house_number = address_info.get('house_number', '')
                address = f"{road} {house_number}".strip() if road else ''
                
                city = (
                    address_info.get('city') or 
                    address_info.get('town') or 
                    address_info.get('village') or 
                    address_info.get('municipality') or
                    address_info.get('suburb', '')
                )
                
                result = {
                    'formatted_address': data.get('display_name', ''),
                    'address': address,
                    'road': road,
                    'house_number': house_number,
                    'city': city,
                    'county': address_info.get('county', ''),
                    'state': address_info.get('state', ''),
                    'postal_code': address_info.get('postcode', ''),
                    'country': address_info.get('country', 'România'),
                    'country_code': address_info.get('country_code', 'ro'),
                    'neighbourhood': address_info.get('neighbourhood', ''),
                    'suburb': address_info.get('suburb', ''),
                    'place_type': data.get('type', 'unknown'),
                    'osm_id': data.get('osm_id', ''),
                    'osm_type': data.get('osm_type', ''),
                    'licence': data.get('licence', ''),
                    'coordinates': {
                        'latitude': latitude,
                        'longitude': longitude
                    }
                }
                
                # Cache successful result
                cache.set(cache_key, result, 86400)
                logger.info(f"✅ Reverse geocoded: {latitude}, {longitude} -> {city}")
                return result
                
        except Exception as e:
            logger.error(f"Reverse geocoding failed for {latitude}, {longitude}: {e}")
        
        return None
    
    @staticmethod
    def search_locations(query: str, limit: int = 10) -> List[Dict]:
        """Enhanced location search with fuzzy matching and multiple strategies"""
        if not query or len(query.strip()) < 2:
            return []
            
        cache_key = f"location_search_{query}_{limit}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        results = []
        query_lower = query.lower().strip()
        
        # Strategy 1: OpenStreetMap search for detailed results including villages
        try:
            # Try multiple search variations for better results
            search_queries = [
                f"{query}, România",  # With country
                f"{query}",           # Just the query
                f"{LocationService.normalize_location_name(query)}, România"  # Normalized
            ]
            
            for search_query in search_queries:
                if len(results) >= limit:
                    break
                    
                params = {
                    'q': search_query,
                    'format': 'json',
                    'limit': limit * 2,  # Get more results to filter
                    'countrycodes': 'ro',
                    'addressdetails': 1,
                    'extratags': 1,
                    'dedupe': 1,  # Remove duplicates
                    'bounded': 1,  # Restrict to Romania
                    'viewbox': '20.2,48.3,29.7,43.6'  # Romania bounding box
                }
                
                data = call_nominatim(params, "search")
                
                # Process results and avoid duplicates
                existing_coords = {(r['latitude'], r['longitude']) for r in results}
                
                for item in data:
                    lat, lon = float(item['lat']), float(item['lon'])
                    
                    # Skip if coordinates already exist
                    if (lat, lon) in existing_coords:
                        continue
                        
                    address = item.get('address', {})
                    
                    # Extract location name with priority for smaller localities
                    city = (
                        address.get('village') or
                        address.get('town') or 
                        address.get('city') or 
                        address.get('municipality') or
                        address.get('hamlet') or
                        address.get('suburb') or
                        ''
                    )
                    
                    # Get place type with more detail
                    place_type = item.get('type', 'location')
                    if 'village' in address:
                        place_type = 'village'
                    elif 'hamlet' in address:
                        place_type = 'hamlet'
                    elif 'town' in address:
                        place_type = 'town'
                    elif 'city' in address:
                        place_type = 'city'
                    
                    # Calculate importance based on type
                    importance = float(item.get('importance', 0))
                    
                    # Create detailed result
                    result = {
                        'name': city or item.get('display_name', ''),
                        'latitude': lat,
                        'longitude': lon,
                        'type': place_type,
                        'formatted_address': item.get('display_name', ''),
                        'city': city,
                        'county': address.get('county', ''),
                        'state': address.get('state', ''),
                        'country': address.get('country', 'România'),
                        'postal_code': address.get('postcode', ''),
                        'importance': importance,
                        'osm_id': item.get('osm_id', ''),
                        'osm_type': item.get('osm_type', '')
                    }
                    
                    results.append(result)
                    existing_coords.add((lat, lon))
                    
                    if len(results) >= limit * 2:
                        break
                        
        except Exception as e:
            logger.error(f"OpenStreetMap search failed for '{query}': {e}")
        
        # Strategy 2: Fallback to known cities if no results
        if not results:
            # Search in known cities with scoring
            city_matches = []
            for city, coords in LocationService.ROMANIA_CITIES.items():
                # Calculate match score
                city_lower = city.lower()
                score = 0
                
                if city_lower == query_lower:
                    score = 100  # Exact match
                elif city_lower.startswith(query_lower):
                    score = 90   # Starts with query
                elif query_lower in city_lower:
                    score = 80   # Contains query
                else:
                    # Fuzzy matching for diacritics
                    normalized_city = LocationService.normalize_location_name(city).lower()
                    normalized_query = LocationService.normalize_location_name(query).lower()
                    
                    if normalized_city == normalized_query:
                        score = 95
                    elif normalized_city.startswith(normalized_query):
                        score = 85
                    elif normalized_query in normalized_city:
                        score = 75
                
                if score > 0:
                    city_matches.append((score, {
                        'name': city,
                        'latitude': coords[0],
                        'longitude': coords[1],
                        'type': 'city',
                        'formatted_address': f"{city}, România",
                        'city': city,
                        'county': '',
                        'match_score': score
                    }))
            
            # Sort by score and add to results
            city_matches.sort(key=lambda x: x[0], reverse=True)
            for score, city_result in city_matches[:limit]:
                results.append(city_result)
        
        # Sort results by relevance
        def sort_key(result):
            # Prioritize villages and smaller localities
            type_priority = {
                'village': 1,
                'hamlet': 2,
                'town': 3,
                'city': 4,
                'administrative': 5
            }.get(result['type'], 10)
            
            # Then by match score or importance
            score = result.get('match_score', result.get('importance', 0))
            return (type_priority, -score)  # Lower type_priority is better, higher score is better
        
        results.sort(key=sort_key)
        
        # Limit final results
        final_results = results[:limit]
        
        # Cache results
        cache.set(cache_key, final_results, 3600)
        logger.info(f"✅ Location search for '{query}' returned {len(final_results)} results")
        return final_results
    
    @staticmethod
    def populate_listing_coordinates(listing):
        """Populate coordinates for a listing based on its location data"""
        if listing.latitude and listing.longitude:
            return True  # Already has coordinates
        
        # Extract location information from different fields
        location_info = []
        
        # Try different location fields
        if hasattr(listing, 'address') and listing.address:
            location_info.append(listing.address)
        if hasattr(listing, 'location') and listing.location:
            location_info.append(listing.location)
        if hasattr(listing, 'city') and listing.city:
            location_info.append(listing.city)
        
        # If no location info, skip
        if not location_info:
            logger.warning(f"No location information available for listing: {listing.title}")
            return False
        
        # Try geocoding with different strategies
        for address_str in location_info:
            city = getattr(listing, 'city', None) if hasattr(listing, 'city') else None
            
            geocoded = LocationService.geocode_address(address_str, city)
            if geocoded:
                listing.latitude = Decimal(str(geocoded['latitude']))
                listing.longitude = Decimal(str(geocoded['longitude']))
                
                # Update additional fields if available and empty
                if hasattr(listing, 'city') and not listing.city and geocoded.get('city'):
                    listing.city = geocoded['city']
                if hasattr(listing, 'county') and not getattr(listing, 'county', None) and geocoded.get('county'):
                    setattr(listing, 'county', geocoded['county'])
                if hasattr(listing, 'formatted_address') and geocoded.get('formatted_address'):
                    setattr(listing, 'formatted_address', geocoded['formatted_address'])
                if hasattr(listing, 'location_verified'):
                    listing.location_verified = True
                
                listing.save()
                logger.info(f"✅ Populated coordinates for {listing.title}: {listing.latitude}, {listing.longitude}")
                return True
        
        logger.warning(f"❌ Failed to populate coordinates for {listing.title}")
        return False
