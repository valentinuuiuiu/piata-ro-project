"""
Cache utilities for Piața.ro marketplace
Implements caching strategies for improved performance
"""
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

# Cache key prefixes
CACHE_PREFIX_LISTING = 'listing'
CACHE_PREFIX_CATEGORY = 'category'
CACHE_PREFIX_USER = 'user'
CACHE_PREFIX_SEARCH = 'search'
CACHE_PREFIX_LOCATION = 'location'

# Cache timeouts (in seconds)
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 3600  # 1 hour
CACHE_TIMEOUT_LONG = 86400  # 24 hours


def make_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a consistent cache key from prefix and arguments
    """
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (list, dict)):
            key_parts.append(hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest())
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = json.dumps(sorted_kwargs)
        key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest())
    
    return ':'.join(key_parts)


def cache_result(prefix: str, timeout: int = CACHE_TIMEOUT_MEDIUM):
    """
    Decorator to cache function results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if DEBUG is True
            if settings.DEBUG and not getattr(settings, 'FORCE_CACHE_IN_DEBUG', False):
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = make_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for key: {cache_key}, cached for {timeout}s")
            
            return result
        return wrapper
    return decorator


class ListingCache:
    """Cache manager for listing data"""
    
    @staticmethod
    def get_listing(listing_id: int) -> Optional[dict]:
        """Get cached listing data"""
        return cache.get(make_cache_key(CACHE_PREFIX_LISTING, listing_id))
    
    @staticmethod
    def set_listing(listing_id: int, data: dict, timeout: int = CACHE_TIMEOUT_MEDIUM):
        """Cache listing data"""
        cache.set(make_cache_key(CACHE_PREFIX_LISTING, listing_id), data, timeout)
    
    @staticmethod
    def delete_listing(listing_id: int):
        """Delete listing from cache"""
        cache.delete(make_cache_key(CACHE_PREFIX_LISTING, listing_id))
    
    @staticmethod
    def get_listing_images(listing_id: int) -> Optional[list]:
        """Get cached listing images"""
        return cache.get(make_cache_key(CACHE_PREFIX_LISTING, 'images', listing_id))
    
    @staticmethod
    def set_listing_images(listing_id: int, images: list, timeout: int = CACHE_TIMEOUT_LONG):
        """Cache listing images"""
        cache.set(make_cache_key(CACHE_PREFIX_LISTING, 'images', listing_id), images, timeout)


class CategoryCache:
    """Cache manager for category data"""
    
    @staticmethod
    @cache_result(CACHE_PREFIX_CATEGORY, CACHE_TIMEOUT_LONG)
    def get_all_categories():
        """Get all categories (cached)"""
        from marketplace.models import Category
        return list(Category.objects.all().values('id', 'name', 'slug', 'parent_id'))
    
    @staticmethod
    @cache_result(CACHE_PREFIX_CATEGORY, CACHE_TIMEOUT_LONG)
    def get_category_tree():
        """Get hierarchical category tree (cached)"""
        from marketplace.models import Category
        
        categories = Category.objects.all().prefetch_related('subcategories')
        tree = {}
        
        for cat in categories:
            if not cat.parent_id:
                tree[cat.id] = {
                    'id': cat.id,
                    'name': cat.name,
                    'slug': cat.slug,
                    'children': [
                        {'id': sub.id, 'name': sub.name, 'slug': sub.slug}
                        for sub in cat.subcategories.all()
                    ]
                }
        
        return tree
    
    @staticmethod
    def invalidate_categories():
        """Clear category cache"""
        try:
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(f"{CACHE_PREFIX_CATEGORY}*")
            elif hasattr(cache, 'keys'):
                # Fallback for caches with keys method
                keys = [key for key in cache.keys(f"{CACHE_PREFIX_CATEGORY}*") if key is not None]
                for key in keys:
                    cache.delete(key)
            else:
                # For LocMemCache and similar, we can't easily invalidate by pattern
                # This is expected behavior for development/testing
                logger.debug("Cache backend doesn't support pattern deletion, skipping category cache invalidation")
        except Exception as e:
            logger.warning(f"Failed to invalidate category cache: {e}")


class SearchCache:
    """Cache manager for search results"""
    
    @staticmethod
    def get_search_results(query: str, filters: dict) -> Optional[list]:
        """Get cached search results"""
        cache_key = make_cache_key(CACHE_PREFIX_SEARCH, query, **filters)
        return cache.get(cache_key)
    
    @staticmethod
    def set_search_results(query: str, filters: dict, results: list, timeout: int = CACHE_TIMEOUT_SHORT):
        """Cache search results"""
        cache_key = make_cache_key(CACHE_PREFIX_SEARCH, query, **filters)
        cache.set(cache_key, results, timeout)
    
    @staticmethod
    @cache_result(CACHE_PREFIX_SEARCH + ':popular', CACHE_TIMEOUT_MEDIUM)
    def get_popular_searches():
        """Get popular search terms (cached)"""
        # This would typically query a search log table
        return [
            'iPhone', 'Samsung', 'Apartament', 'Mașină', 'Laptop',
            'Bicicletă', 'Mobilă', 'Haine', 'Jocuri', 'Cărți'
        ]


class LocationCache:
    """Cache manager for location data"""
    
    @staticmethod
    @cache_result(CACHE_PREFIX_LOCATION, CACHE_TIMEOUT_LONG)
    def get_coordinates(location_name: str) -> Optional[tuple]:
        """Get cached coordinates for a location"""
        from marketplace.services.location_service import LocationService
        service = LocationService()
        return service.get_coordinates_from_city(location_name)
    
    @staticmethod
    @cache_result(CACHE_PREFIX_LOCATION + ':cities', CACHE_TIMEOUT_LONG)
    def get_romanian_cities():
        """Get list of Romanian cities (cached)"""
        return [
            'București', 'Cluj-Napoca', 'Timișoara', 'Iași', 'Constanța',
            'Craiova', 'Brașov', 'Galați', 'Ploiești', 'Oradea',
            'Brăila', 'Arad', 'Pitești', 'Sibiu', 'Bacău',
            'Târgu Mureș', 'Baia Mare', 'Buzău', 'Botoșani', 'Satu Mare'
        ]


class UserCache:
    """Cache manager for user data"""
    
    @staticmethod
    def get_user_profile(user_id: int) -> Optional[dict]:
        """Get cached user profile"""
        return cache.get(make_cache_key(CACHE_PREFIX_USER, 'profile', user_id))
    
    @staticmethod
    def set_user_profile(user_id: int, profile_data: dict, timeout: int = CACHE_TIMEOUT_MEDIUM):
        """Cache user profile"""
        cache.set(make_cache_key(CACHE_PREFIX_USER, 'profile', user_id), profile_data, timeout)
    
    @staticmethod
    def get_user_listings_count(user_id: int) -> Optional[int]:
        """Get cached user listings count"""
        return cache.get(make_cache_key(CACHE_PREFIX_USER, 'listings_count', user_id))
    
    @staticmethod
    def set_user_listings_count(user_id: int, count: int, timeout: int = CACHE_TIMEOUT_SHORT):
        """Cache user listings count"""
        cache.set(make_cache_key(CACHE_PREFIX_USER, 'listings_count', user_id), count, timeout)
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Clear all cache for a specific user"""
        try:
            if hasattr(cache, 'delete_pattern'):
                cache.delete_pattern(f"{CACHE_PREFIX_USER}:*:{user_id}*")
            elif hasattr(cache, 'keys'):
                # Fallback for caches with keys method
                keys = [key for key in cache.keys(f"{CACHE_PREFIX_USER}:*:{user_id}*") if key is not None]
                for key in keys:
                    cache.delete(key)
            else:
                # For LocMemCache and similar, we can't easily invalidate by pattern
                logger.debug("Cache backend doesn't support pattern deletion, skipping user cache invalidation")
        except Exception as e:
            logger.warning(f"Failed to invalidate user cache for user {user_id}: {e}")


# Cache warming utilities
def warm_cache():
    """Pre-populate cache with frequently accessed data"""
    logger.info("Starting cache warming...")
    
    # Warm category cache
    CategoryCache.get_all_categories()
    CategoryCache.get_category_tree()
    
    # Warm location cache
    LocationCache.get_romanian_cities()
    
    # Warm popular searches
    SearchCache.get_popular_searches()
    
    logger.info("Cache warming completed")


# Cache invalidation utilities
def invalidate_listing_cache(listing):
    """Invalidate all caches related to a listing"""
    ListingCache.delete_listing(listing.id)
    # Also invalidate search cache as results might have changed
    try:
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(f"{CACHE_PREFIX_SEARCH}*")
        elif hasattr(cache, 'keys'):
            # Fallback for caches with keys method
            keys = [key for key in cache.keys(f"{CACHE_PREFIX_SEARCH}*") if key is not None]
            for key in keys:
                cache.delete(key)
        else:
            # For LocMemCache and similar, we can't easily invalidate by pattern
            logger.debug("Cache backend doesn't support pattern deletion, skipping search cache invalidation")
    except Exception as e:
        logger.warning(f"Failed to invalidate search cache: {e}")


def invalidate_user_cache(user):
    """Invalidate all caches related to a user"""
    UserCache.invalidate_user_cache(user.id)


# Context manager for bulk operations
class BulkCacheInvalidation:
    """Context manager to batch cache invalidations"""
    
    def __init__(self):
        self.keys_to_delete = set()
    
    def add_key(self, key: str):
        self.keys_to_delete.add(key)
    
    def add_pattern(self, pattern: str):
        # In production, this would use Redis SCAN
        self.keys_to_delete.add(pattern)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.keys_to_delete:
            cache.delete_many(list(self.keys_to_delete))
            logger.info(f"Bulk deleted {len(self.keys_to_delete)} cache keys")
