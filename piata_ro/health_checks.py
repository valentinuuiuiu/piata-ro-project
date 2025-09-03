
"""
Health check system for Piața.ro marketplace
"""
import time
import redis
import logging
from django.db import connections
from django.core.cache import cache
from django.conf import settings
from django.core.mail import get_connection
from django.test.utils import override_settings
from django.db.utils import OperationalError
from django.core.exceptions import ImproperlyConfigured
from django.core.cache.backends.base import BaseCache
from django.core.mail.backends.base import BaseEmailBackend
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import requests
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HealthCheckError(Exception):
    """Custom exception for health check failures"""
    pass


class DatabaseHealthCheck:
    """Database health check implementation"""
    
    def __init__(self, alias='default'):
        self.alias = alias
    
    def check(self) -> Dict[str, Any]:
        """Check database connection and performance"""
        try:
            connection = connections[self.alias]
            cursor = connection.cursor()
            
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result[0] != 1:
                raise HealthCheckError("Database query returned unexpected result")
            
            # Test database performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            cursor.fetchone()
            query_time = time.time() - start_time
            
            # Check connection pool status
            connection_health = {
                'status': 'healthy',
                'database': self.alias,
                'query_time': round(query_time, 4),
                'connections': connection.connection_pool.max_connections if hasattr(connection, 'connection_pool') else 'N/A',
                'timestamp': timezone.now().isoformat()
            }
            
            return connection_health
            
        except OperationalError as e:
            logger.error(f"Database health check failed for {self.alias}: {e}")
            return {
                'status': 'unhealthy',
                'database': self.alias,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error in database health check for {self.alias}: {e}")
            return {
                'status': 'unhealthy',
                'database': self.alias,
                'error': f"Unexpected error: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }


class RedisHealthCheck:
    """Redis health check implementation"""
    
    def __init__(self, alias='default'):
        self.alias = alias
    
    def check(self) -> Dict[str, Any]:
        """Check Redis connection and performance"""
        try:
            redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            start_time = time.time()
            redis_client.ping()
            ping_time = time.time() - start_time
            
            # Test basic operations
            start_time = time.time()
            redis_client.set('health_check_test', 'value', ex=10)
            redis_client.get('health_check_test')
            redis_client.delete('health_check_test')
            operation_time = time.time() - start_time
            
            # Get Redis info
            info = redis_client.info()
            
            redis_health = {
                'status': 'healthy',
                'alias': self.alias,
                'ping_time': round(ping_time, 4),
                'operation_time': round(operation_time, 4),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'N/A'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'timestamp': timezone.now().isoformat()
            }
            
            return redis_health
            
        except redis.ConnectionError as e:
            logger.error(f"Redis health check failed for {self.alias}: {e}")
            return {
                'status': 'unhealthy',
                'alias': self.alias,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error in Redis health check for {self.alias}: {e}")
            return {
                'status': 'unhealthy',
                'alias': self.alias,
                'error': f"Unexpected error: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }


class CacheHealthCheck:
    """Cache health check implementation"""
    
    def __init__(self, alias='default'):
        self.alias = alias
    
    def check(self) -> Dict[str, Any]:
        """Check cache functionality"""
        try:
            cache_instance = cache
            test_key = f'health_check_{self.alias}_{int(time.time())}'
            test_value = 'test_value'
            
            # Test set operation
            start_time = time.time()
            cache_instance.set(test_key, test_value, 60)
            set_time = time.time() - start_time
            
            # Test get operation
            start_time = time.time()
            retrieved_value = cache_instance.get(test_key)
            get_time = time.time() - start_time
            
            # Test delete operation
            cache_instance.delete(test_key)
            
            if retrieved_value != test_value:
                raise HealthCheckError("Cache returned unexpected value")
            
            cache_health = {
                'status': 'healthy',
                'alias': self.alias,
                'set_time': round(set_time, 4),
                'get_time': round(get_time, 4),
                'backend': cache_instance.__class__.__name__,
                'timestamp': timezone.now().isoformat()
            }
            
            return cache_health
            
        except Exception as e:
            logger.error(f"Cache health check failed for {self.alias}: {e}")
            return {
                'status': 'unhealthy',
                'alias': self.alias,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


class EmailHealthCheck:
    """Email health check implementation"""
    
    def __init__(self, backend='default'):
        self.backend = backend
    
    def check(self) -> Dict[str, Any]:
        """Check email configuration"""
        try:
            # Test email connection without sending
            email_backend = get_connection(self.backend)
            
            if not isinstance(email_backend, BaseEmailBackend):
                raise HealthCheckError(f"Invalid email backend: {email_backend.__class__.__name__}")
            
            # Test email configuration
            host = getattr(email_backend, 'host', None)
            port = getattr(email_backend, 'port', None)
            username = getattr(email_backend, 'username', None)
            use_tls = getattr(email_backend, 'use_tls', False)
            use_ssl = getattr(email_backend, 'use_ssl', False)
            
            email_health = {
                'status': 'healthy',
                'backend': self.backend,
                'host': host,
                'port': port,
                'username': username,
                'use_tls': use_tls,
                'use_ssl': use_ssl,
                'timestamp': timezone.now().isoformat()
            }
            
            return email_health
            
        except Exception as e:
            logger.error(f"Email health check failed for {self.backend}: {e}")
            return {
                'status': 'unhealthy',
                'backend': self.backend,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


class ExternalAPIHealthCheck:
    """External API health check implementation"""
    
    def __init__(self, name: str, url: str, timeout: int = 5):
        self.name = name
        self.url = url
        self.timeout = timeout
    
    def check(self) -> Dict[str, Any]:
        """Check external API availability"""
        try:
            start_time = time.time()
            response = requests.get(self.url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                raise HealthCheckError(f"API returned status code: {response.status_code}")
            
            api_health = {
                'status': 'healthy',
                'name': self.name,
                'url': self.url,
                'status_code': response.status_code,
                'response_time': round(response_time, 4),
                'timestamp': timezone.now().isoformat()
            }
            
            return api_health
            
        except requests.exceptions.Timeout:
            logger.error(f"External API health check timeout for {self.name}: {self.url}")
            return {
                'status': 'unhealthy',
                'name': self.name,
                'url': self.url,
                'error': 'Timeout',
                'timestamp': timezone.now().isoformat()
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"External API health check connection error for {self.name}: {self.url}")
            return {
                'status': 'unhealthy',
                'name': self.name,
                'url': self.url,
                'error': 'Connection error',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"External API health check failed for {self.name}: {e}")
            return {
                'status': 'unhealthy',
                'name': self.name,
                'url': self.url,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


class StorageHealthCheck:
    """Storage health check implementation"""
    
    def __init__(self, backend='default'):
        self.backend = backend
    
    def check(self) -> Dict[str, Any]:
        """Check storage functionality"""
        try:
            from django.core.files.storage import default_storage
            
            # Test file operations
            test_filename = f'health_check_{self.backend}_{int(time.time())}.txt'
            test_content = b'health_check_content'
            
            # Test save operation
            start_time = time.time()
            with default_storage.open(test_filename, 'wb') as f:
                f.write(test_content)
            save_time = time.time() - start_time
            
            # Test read operation
            start_time = time.time()
            with default_storage.open(test_filename, 'rb') as f:
                content = f.read()
            read_time = time.time() - start_time
            
            # Test delete operation
            default_storage.delete(test_filename)
            
            if content != test_content:
                raise HealthCheckError("Storage returned unexpected content")
            
            storage_health = {
                'status': 'healthy',
                'backend': self.backend,
                'save_time': round(save_time, 4),
                'read_time': round(read_time, 4),
                'storage_backend': default_storage.__class__.__name__,
                'timestamp': timezone.now().isoformat()
            }
            
            return storage_health
            
        except Exception as e:
            logger.error(f"Storage health check failed for {self.backend}: {e}")
            return {
                'status': 'unhealthy',
                'backend': self.backend,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


class HealthCheckManager:
    """Main health check manager"""
    
    def __init__(self):
        self.checks = []
        self._setup_checks()
    
    def _setup_checks(self):
        """Setup all health checks"""
        # Database checks
        if hasattr(settings, 'DATABASES'):
            for alias in settings.DATABASES:
                self.checks.append(DatabaseHealthCheck(alias))
        
        # Redis checks
        if hasattr(settings, 'REDIS_URL') or hasattr(settings, 'REDIS_HOST'):
            self.checks.append(RedisHealthCheck())
        
        # Cache checks
        self.checks.append(CacheHealthCheck())
        
        # Email checks
        if hasattr(settings, 'EMAIL_BACKEND'):
            self.checks.append(EmailHealthCheck())
        
        # Storage checks
        self.checks.append(StorageHealthCheck())
        
        # External API checks
        external_apis = getattr(settings, 'EXTERNAL_API_HEALTH_CHECKS', {})
        for name, url in external_apis.items():
            self.checks.append(ExternalAPIHealthCheck(name, url))
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            'overall_status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        unhealthy_count = 0
        
        for check in self.checks:
            try:
                result = check.check()
                results['checks'][check.__class__.__name__] = result
                
                if result['status'] != 'healthy':
                    unhealthy_count += 1
                    results['overall_status'] = 'unhealthy'
                    
            except Exception as e:
                logger.error(f"Error running health check {check.__class__.__name__}: {e}")
                results['checks'][check.__class__.__name__] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                unhealthy_count += 1
                results['overall_status'] = 'unhealthy'
        
        # Add system information
        results['system'] = {
            'python_version': os.sys.version,
            'django_version': os.getenv('DJANGO_VERSION', 'unknown'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug_mode': getattr(settings, 'DEBUG', False)
        }
        
        return results
    
    def run_checks_with_timeout(self, timeout: int = 30) -> Dict[str, Any]:
        """Run all health checks with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Health check timed out after {timeout} seconds")
        
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            results = self.run_checks()
            signal.alarm(0)  # Cancel the alarm
            return results
        except TimeoutError as e:
            logger.error(f"Health check timeout: {e}")
            return {
                'overall_status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e),
                'checks': {}
            }


# Global health check manager instance
health_check_manager = HealthCheckManager()


@require_http_methods(["GET"])
def comprehensive_health_check(request):
    """Comprehensive health check endpoint"""
    try:
        results = health_check_manager.run_checks_with_timeout()
        
        status_code = 200 if results['overall_status'] == 'healthy' else 503
        
        return JsonResponse(results, status=status_code, json_dumps_params={'indent': 2})
        
    except Exception as e:
        logger.error(f"Error in comprehensive health check: {e}")
        return JsonResponse({
            'overall_status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def database_health_check(request):
    """Database-specific health check"""
    try:
        db_check = DatabaseHealthCheck()
        result = db_check.check()
        
        status_code = 200 if result['status'] == 'healthy' else 503
        
        return JsonResponse(result, status=status_code)
        
    except Exception as e:
        logger.error(f"Error in database health check: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def redis_health_check(request):
    """Redis-specific health check"""
    try:
        redis_check = RedisHealthCheck()
        result = redis_check.check()
        
        status_code = 200 if result['status'] == 'healthy' else 503
        
        return JsonResponse(result, status=status_code)
        
    except Exception as e:
        logger.error(f"Error in Redis health check: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
def cache_health_check(request):
    """Cache-specific health check"""
    try:
        cache_check = CacheHealthCheck()
        result = cache_check.check()
        
        status_code = 200 if result['status'] == 'healthy' else 503
        
        return JsonResponse(result, status=status_code)
        
    except Exception as e:
        logger.error(f"Error in cache health check: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


def invalidate_health_cache():
    """Invalidate health check cache"""
    try:
        cache.delete('health_check_results')
        cache.delete('health_check_timestamp')
        logger.info("Health check cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating health check cache: {e}")


def get_cached_health_results() -> Optional[Dict[str, Any]]:
    """Get cached health check results"""
    try:
        cached_results = cache.get('health_check_results')
        cached_timestamp = cache.get('health_check_timestamp')
        
        if cached_results and cached_timestamp:
            # Check if cache is still valid (5 minutes)
            if timezone.now() - cached_timestamp < timedelta(minutes=5):
                return cached_results
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached health results: {e}")
        return None


def cache_health_results(results: Dict[str, Any]):
    """Cache health check results"""
    try:
        cache.set('health_check_results', results, 300)  # Cache for 5 minutes
        cache.set('health_check_timestamp', timezone.now(), 300)
        logger.info("Health check results cached")
    except Exception as e:
        logger.error(f"Error caching health results: {e}")


# Health check middleware
class HealthCheckMiddleware:
    """Middleware to add health check headers"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add health check headers to all responses
        response = self.get_response(request)
        
        # Add X-Health-Check header
        response['X-Health-Check'] = 'available'
        
        # Add timestamp
        response['X-Response-Timestamp'] = timezone.now().isoformat()
        
        return response


# Export health check functions
__all__ = [
    'HealthCheckManager',
    'DatabaseHealthCheck',
    'RedisHealthCheck',
    'CacheHealthCheck',
    'EmailHealthCheck',
    'ExternalAPIHealthCheck',
    'StorageHealthCheck',
    'comprehensive_health_check',
    'database_health_check',
    'redis_health_check',
    'cache_health_check',
    'invalidate_health_cache',
    'get_cached_health_results',
    'cache_health_results',
    'HealthCheckMiddleware'
]
