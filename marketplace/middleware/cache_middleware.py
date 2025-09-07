"""
Cache middleware for Piața.ro marketplace
Provides intelligent caching strategies for improved performance
"""
import time
import hashlib
import json
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class CacheMiddleware(MiddlewareMixin):
    """
    Middleware for intelligent request caching
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cacheable_paths = [
            '/api/listings/',
            '/api/categories/',
            '/api/search/',
            '/marketplace/',
        ]
        self.ignore_paths = [
            '/admin/',
            '/auth/',
            '/api/auth/',
            '/marketplace/create/',
            '/marketplace/edit/',
        ]
    
    def should_cache_request(self, request):
        """Determine if this request should be cached"""
        path = request.path
        
        # Don't cache non-GET requests
        if request.method != 'GET':
            return False
        
        # Don't cache authenticated requests (except public APIs)
        if request.user.is_authenticated and not path.startswith('/api/'):
            return False
        
        # Check if path is in cacheable paths
        for cacheable_path in self.cacheable_paths:
            if path.startswith(cacheable_path):
                # Check if path is not in ignore paths
                for ignore_path in self.ignore_paths:
                    if path.startswith(ignore_path):
                        return False
                return True
        
        return False
    
    def generate_cache_key(self, request):
        """Generate a unique cache key for the request"""
        # Use path, query params, and headers that affect response
        key_parts = [
            request.path,
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
            request.META.get('HTTP_USER_AGENT', '')[:100],
        ]
        
        # Add query parameters if present
        if request.GET:
            sorted_params = sorted(request.GET.items())
            key_parts.append(hashlib.md5(json.dumps(sorted_params).encode()).hexdigest())
        
        return f"request:{hashlib.md5(':'.join(key_parts).encode()).hexdigest()}"
    
    def process_request(self, request):
        """Process incoming request - check cache"""
        if not self.should_cache_request(request):
            return None
        
        cache_key = self.generate_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.debug(f"Cache hit for request: {request.path}")
            return cached_response
        
        # Store cache key for later use in process_response
        request._cache_key = cache_key
        return None
    
    def process_response(self, request, response):
        """Process outgoing response - cache if appropriate"""
        if not hasattr(request, '_cache_key'):
            return response
        
        # Only cache successful responses
        if response.status_code == 200:
            # Set appropriate cache timeout based on content
            timeout = self.get_cache_timeout(request, response)
            cache.set(request._cache_key, response, timeout)
            logger.debug(f"Cached response for {request.path} for {timeout}s")
        
        return response
    
    def get_cache_timeout(self, request, response):
        """Determine appropriate cache timeout based on request and response"""
        path = request.path
        
        if path.startswith('/api/listings/'):
            # Listings API - cache for shorter time as they change frequently
            return 300  # 5 minutes
        
        elif path.startswith('/api/categories/'):
            # Categories API - cache longer as they don't change often
            return 3600  # 1 hour
        
        elif path.startswith('/api/search/'):
            # Search results - cache for short time
            return 180  # 3 minutes
        
        elif path.startswith('/marketplace/'):
            # Marketplace pages - moderate caching
            return 600  # 10 minutes
        
        # Default cache time
        return 300  # 5 minutes


class DatabaseQueryCacheMiddleware(MiddlewareMixin):
    """
    Middleware to track and optimize database queries
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def process_request(self, request):
        """Start tracking queries at the beginning of request"""
        from django.db import connection
        connection.queries_log.clear()
        request._query_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Analyze and log database queries at the end of request"""
        from django.db import connection
        
        if not hasattr(request, '_query_start_time'):
            return response
        
        query_time = time.time() - request._query_start_time
        queries = connection.queries
        num_queries = len(queries)
        
        # Log slow requests or those with many queries
        if query_time > 1.0 or num_queries > 20:
            logger.warning(
                f"Slow request: {request.path} - "
                f"{num_queries} queries in {query_time:.2f}s"
            )
            
            # Log individual slow queries
            for i, query in enumerate(queries):
                if float(query.get('time', 0)) > 0.1:  # Queries taking > 100ms
                    logger.debug(
                        f"Slow query #{i+1}: {query['sql'][:200]}... "
                        f"({query.get('time', 0):.3f}s)"
                    )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware for API rate limiting using Redis
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.limits = {
            '/api/': {'limit': 100, 'window': 3600},  # 100 requests per hour
            '/api/auth/': {'limit': 10, 'window': 300},  # 10 requests per 5 minutes
            '/api/listings/create': {'limit': 5, 'window': 60},  # 5 requests per minute
        }
    
    def process_request(self, request):
        """Check rate limits for API requests"""
        if not request.path.startswith('/api/'):
            return None
        
        # Find matching rate limit rule
        matching_rule = None
        for path_prefix, rule in self.limits.items():
            if request.path.startswith(path_prefix):
                matching_rule = rule
                break
        
        if not matching_rule:
            return None
        
        # Generate rate limit key
        client_ip = self.get_client_ip(request)
        rate_key = f"ratelimit:{client_ip}:{request.path}"
        
        # Get current count
        current_count = cache.get(rate_key, 0)
        
        if current_count >= matching_rule['limit']:
            from django.http import JsonResponse
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.path}")
            return JsonResponse(
                {'error': 'Rate limit exceeded', 'retry_after': matching_rule['window']},
                status=429
            )
        
        # Increment count
        cache.set(rate_key, current_count + 1, matching_rule['window'])
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
