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
    
    def _ensure_rate_limit(self):
        """Ensure we don't exceed Nominatim rate limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self._last_request_time = time.time()
    
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
    

    
    async def geocode_async(self, address: str, city: Optional[str] = None, country: str = "România") -> Optional[LocationResult]:
        """Async geocoding using OpenStreetMap Nominatim API"""
        if not address and not city:
            return None
        
        # Create cache key
        cache_key = f"geocode_{address}_{city}_{country}".replace(" ", "_").lower()
        cached_result = cache.get(cache_key)
        if cached_result:
            return LocationResult(**cached_result)
        
        # Build query
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
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': self.USER_AGENT}
                async with session.get(f"{self.BASE_URL}/search", params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
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
                            return location_result
        
        except Exception as e:
            logger.error(f"Async geocoding failed for '{query}': {e}")
        
        return None
    
    def geocode(self, address: str, city: Optional[str] = None, country: str = "România") -> Optional[LocationResult]:
        """Sync geocoding wrapper"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.geocode_async(address, city, country))
    
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
        
        # Try to geocode based on available information
        address = listing.address or listing.location
        city = listing.city or listing.location
        
        location_result = self.geocode(address, city)
        if location_result:
            listing.latitude = Decimal(str(location_result.latitude))
            listing.longitude = Decimal(str(location_result.longitude))
            if not listing.city and location_result.city:
                listing.city = location_result.city
            if not listing.county and location_result.county:
                listing.county = location_result.county
            if not listing.postal_code and location_result.postal_code:
                listing.postal_code = location_result.postal_code
            listing.location_verified = True
            listing.save()
            return True
        
        return False

# Global instance
location_service = LocationService()