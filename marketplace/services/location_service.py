"""
Enhanced Location Service for Piața.ro
Provides geocoding, reverse geocoding, and location-based search using OpenStreetMap
"""

import requests
import asyncio
import aiohttp
from django.core.cache import cache
from django.conf import settings
from typing import Dict, List, Optional, Tuple
import logging
from decimal import Decimal
from dataclasses import dataclass
from math import radians, cos, sin, asin, sqrt
import time
from requests_cache import CachedSession

logger = logging.getLogger(__name__)

@dataclass
class LocationResult:
    """Data class for location results"""
    name: str
    latitude: float
    longitude: float
    formatted_address: str
    city: str = ""
    county: str = ""
    postal_code: str = ""
    country: str = "România"
    location_type: str = "location"

class LocationService:
    """Enhanced location service with async support and better error handling"""
    
    BASE_URL = "https://nominatim.openstreetmap.org"
    USER_AGENT = "PiataRo/2.0 (marketplace@piata.ro)"
    RATE_LIMIT_DELAY = 1.0  # Nominatim requires 1 request per second
    
    # Romanian cities with coordinates for fallback
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
    
    def __init__(self):
        self._last_request_time = 0
        self.session = CachedSession(
            'geocoding_cache',
            backend='redis' if hasattr(settings, 'REDIS_URL') else 'memory',
            expire_after=86400  # 24 hours
        )
    
    def _ensure_rate_limit(self):
        """Ensure we don't exceed Nominatim rate limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            sleep_time = self.RATE_LIMIT_DELAY - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make a rate-limited request to Nominatim API with analytics"""
        start_time = time.time()
        success = False
        
        try:
            self._ensure_rate_limit()
            
            headers = {'User-Agent': self.USER_AGENT}
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params, headers=headers, timeout=10)
            
            if response.status_code == 429:  # Rate limited
                logger.warning("Rate limit hit, backing off")
                from .location_analytics import LocationAnalytics
                LocationAnalytics.log_rate_limit_hit()
                time.sleep(2)  # Back off for 2 seconds
                return None
            
            response.raise_for_status()
            success = True
            result = response.json()
            
            response_time = time.time() - start_time
            
            # Log analytics
            try:
                from .location_analytics import LocationAnalytics
                query = params.get('q', f"lat:{params.get('lat', 'N/A')},lon:{params.get('lon', 'N/A')}")
                LocationAnalytics.log_geocoding_request(query, success, response_time)
            except ImportError:
                pass  # Analytics not available
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Nominatim API error for {endpoint}: {e}")
            
            # Log failed request
            try:
                from .location_analytics import LocationAnalytics
                query = params.get('q', f"lat:{params.get('lat', 'N/A')},lon:{params.get('lon', 'N/A')}")
                LocationAnalytics.log_geocoding_request(query, False, response_time)
            except ImportError:
                pass
            
            return None
    
    def normalize_location_name(self, location: str) -> str:
        """Normalize location name for consistency"""
        if not location:
            return ""
        
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
    
    def get_coordinates_from_city(self, city: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a Romanian city from local cache"""
        normalized_city = self.normalize_location_name(city)
        return self.ROMANIA_CITIES.get(normalized_city)
    

    
    def geocode_sync(self, address: str, city: Optional[str] = None, country: str = "România") -> Optional[LocationResult]:
        """Synchronous geocoding using OpenStreetMap Nominatim API"""
        if not address and not city:
            return None
        
        # Create cache key
        cache_key = f"geocode_{address}_{city}_{country}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return LocationResult(**cached_result)
        
        # Build query - try multiple variations
        queries = []
        if address and city:
            queries.append(f"{address}, {city}, {country}")
            queries.append(f"{city}, {country}")
        elif address:
            queries.append(f"{address}, {country}")
        elif city:
            queries.append(f"{city}, {country}")
        
        for query in queries:
            try:
                self._ensure_rate_limit()
                
                params = {
                    'q': query,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'ro',
                    'addressdetails': 1
                }
                
                headers = {'User-Agent': self.USER_AGENT}
                response = requests.get(f"{self.BASE_URL}/search", params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        result = data[0]
                        address_info = result.get('address', {})
                        
                        location_result = LocationResult(
                            name=result.get('display_name', query),
                            latitude=float(result['lat']),
                            longitude=float(result['lon']),
                            formatted_address=result.get('display_name', query),
                            city=address_info.get('city') or address_info.get('town') or city or "",
                            county=address_info.get('county', ''),
                            postal_code=address_info.get('postcode', ''),
                            country=address_info.get('country', country),
                            location_type=result.get('type', 'location')
                        )
                        
                        # Cache successful result
                        cache.set(cache_key, location_result.__dict__, 86400)
                        logger.info(f"✅ Geocoded: {query} -> {location_result.latitude}, {location_result.longitude}")
                        return location_result
                        
            except Exception as e:
                logger.error(f"Geocoding failed for '{query}': {e}")
                continue
        
        # Fallback to known cities
        if city:
            normalized_city = self.normalize_location_name(city)
            coords = self.get_coordinates_from_city(normalized_city)
            if coords:
                location_result = LocationResult(
                    name=f"{normalized_city}, România",
                    latitude=coords[0],
                    longitude=coords[1],
                    formatted_address=f"{normalized_city}, România",
                    city=normalized_city,
                    country="România",
                    location_type="city"
                )
                cache.set(cache_key, location_result.__dict__, 86400)
                logger.info(f"✅ Fallback city: {normalized_city} -> {coords[0]}, {coords[1]}")
                return location_result
        
        return None
    
    async def geocode_async(self, address: str, city: Optional[str] = None, country: str = "România") -> Optional[LocationResult]:
        """Async wrapper for sync geocoding"""
        return self.geocode_sync(address, city, country)
    
    def geocode(self, address: str, city: Optional[str] = None, country: str = "România") -> Optional[LocationResult]:
        """Main geocoding method"""
        return self.geocode_sync(address, city, country)
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[LocationResult]:
        """Reverse geocoding using OpenStreetMap Nominatim API"""
        cache_key = f"reverse_geocode_{latitude}_{longitude}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return LocationResult(**cached_result)
        
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1
        }
        
        try:
            self._ensure_rate_limit()
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(f"{self.BASE_URL}/reverse", params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'address' in data:
                    address_info = data['address']
                    
                    location_result = LocationResult(
                        name=data.get('display_name', ''),
                        latitude=latitude,
                        longitude=longitude,
                        formatted_address=data.get('display_name', ''),
                        city=(
                            address_info.get('city') or 
                            address_info.get('town') or 
                            address_info.get('village') or 
                            address_info.get('municipality', '')
                        ),
                        county=address_info.get('county', ''),
                        postal_code=address_info.get('postcode', ''),
                        country=address_info.get('country', 'România')
                    )
                    
                    # Cache successful result
                    cache.set(cache_key, location_result.__dict__, 86400)
                    return location_result
        
        except Exception as e:
            logger.error(f"Reverse geocoding failed for {latitude}, {longitude}: {e}")
        
        return None
    
    def search_locations(self, query: str, limit: int = 10) -> List[LocationResult]:
        """Search for locations matching a query"""
        cache_key = f"location_search_{query}_{limit}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return [LocationResult(**item) for item in cached_result]
        
        results = []
        
        # First, search in our known Romanian cities
        query_lower = query.lower()
        for city, coords in self.ROMANIA_CITIES.items():
            if query_lower in city.lower():
                results.append(LocationResult(
                    name=city,
                    latitude=coords[0],
                    longitude=coords[1],
                    formatted_address=f"{city}, România",
                    city=city,
                    country="România",
                    location_type="city"
                ))
        
        # If we have enough results, return them
        if len(results) >= limit:
            result_dicts = [result.__dict__ for result in results[:limit]]
            cache.set(cache_key, result_dicts, 3600)
            return results[:limit]
        
        # Otherwise, search using Nominatim
        params = {
            'q': f"{query}, România",
            'format': 'json',
            'limit': limit - len(results),
            'countrycodes': 'ro',
            'addressdetails': 1
        }
        
        try:
            self._ensure_rate_limit()
            headers = {'User-Agent': self.USER_AGENT}
            response = requests.get(f"{self.BASE_URL}/search", params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    address = item.get('address', {})
                    results.append(LocationResult(
                        name=item.get('display_name', ''),
                        latitude=float(item['lat']),
                        longitude=float(item['lon']),
                        formatted_address=item.get('display_name', ''),
                        city=address.get('city') or address.get('town') or address.get('village', ''),
                        county=address.get('county', ''),
                        postal_code=address.get('postcode', ''),
                        country=address.get('country', 'România'),
                        location_type=item.get('type', 'location')
                    ))
        
        except Exception as e:
            logger.error(f"Location search failed for '{query}': {e}")
        
        # Cache results
        result_dicts = [result.__dict__ for result in results[:limit]]
        cache.set(cache_key, result_dicts, 3600)
        return results[:limit]
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def populate_listing_coordinates(self, listing):
        """Populate coordinates for a listing based on its location data"""
        if listing.latitude and listing.longitude:
            return True  # Already has coordinates
        
        # Extract city from location string
        location_parts = listing.location.split(',') if listing.location else []
        city = None
        address = listing.location
        
        # Try to identify city from location string
        for part in location_parts:
            part = part.strip()
            normalized = self.normalize_location_name(part)
            if normalized in self.ROMANIA_CITIES:
                city = normalized
                break
        
        # Try geocoding with different strategies
        location_result = None
        
        # Strategy 1: Full location string
        if listing.location:
            location_result = self.geocode(listing.location)
        
        # Strategy 2: Just the city if found
        if not location_result and city:
            location_result = self.geocode(city)
        
        # Strategy 3: Try each part of location
        if not location_result and location_parts:
            for part in location_parts:
                part = part.strip()
                if len(part) > 2:  # Skip very short parts
                    location_result = self.geocode(part)
                    if location_result:
                        break
        
        if location_result:
            from decimal import Decimal
            listing.latitude = Decimal(str(location_result.latitude))
            listing.longitude = Decimal(str(location_result.longitude))
            if not listing.city and location_result.city:
                listing.city = location_result.city
            if not listing.county and location_result.county:
                listing.county = location_result.county
            listing.save()
            logger.info(f"✅ Populated coordinates for {listing.title}: {listing.latitude}, {listing.longitude}")
            return True
        
        logger.warning(f"❌ Failed to populate coordinates for {listing.title} - {listing.location}")
        return False

# Global instance
location_service = LocationService()