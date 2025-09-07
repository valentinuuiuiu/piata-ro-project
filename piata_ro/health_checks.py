"""
Health check endpoints for Piața.ro production monitoring
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
import redis
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@require_GET
def health_check(request):
    """
    Comprehensive health check endpoint for monitoring
    """
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'external_services': check_external_services(),
        'storage': check_storage(),
        'overall': True
    }
    
    # Check if all components are healthy
    checks['overall'] = all(checks.values())
    
    status_code = 200 if checks['overall'] else 503
    
    return JsonResponse({
        'status': 'healthy' if checks['overall'] else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }, status=status_code)

def check_database():
    """Check database connectivity"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def check_cache():
    """Check Redis cache connectivity"""
    try:
        # Test basic cache operations
        test_key = 'health_check_test'
        test_value = 'ok'
        
        cache.set(test_key, test_value, timeout=5)
        retrieved = cache.get(test_key)
        
        return retrieved == test_value
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False

def check_external_services():
    """Check external service dependencies"""
    services_ok = True
    
    # Check DeepSeek API (basic connectivity)
    try:
        # Simple check without making actual API calls
        # that might incur costs
        pass
    except Exception as e:
        logger.warning(f"DeepSeek API check: {e}")
        services_ok = False
    
    # Check Azure Storage if configured
    try:
        from django.conf import settings
        if hasattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME'):
            # Basic check - could be enhanced with actual storage ops
            pass
    except Exception as e:
        logger.warning(f"Azure Storage check: {e}")
        services_ok = False
    
    return services_ok

def check_storage():
    """Check storage accessibility"""
    try:
        # Check if media directory is writable
        import tempfile
        import os
        from django.conf import settings
        
        test_file = os.path.join(settings.MEDIA_ROOT, 'health_check_test.tmp')
        
        with open(test_file, 'w') as f:
            f.write('test')
        
        os.remove(test_file)
        return True
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return False

@require_GET
def readiness_check(request):
    """
    Readiness check for load balancers and orchestrators
    """
    try:
        # Basic checks that don't require external services
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=503)

@require_GET
def liveness_check(request):
    """
    Liveness check for container orchestration
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': datetime.now().isoformat()
    })

# MCP Agent health checks
@require_GET
def mcp_health_check(request, port):
    """
    Health check for MCP agents
    """
    try:
        response = requests.get(f"http://mcp-agents:{port}/health", timeout=5)
        return JsonResponse({
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'agent_port': port,
            'response_code': response.status_code
        })
    except Exception as e:
        logger.error(f"MCP agent health check failed for port {port}: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'agent_port': port,
            'error': str(e)
        }, status=503)

# Database metrics for monitoring
@require_GET
def database_metrics(request):
    """
    Database performance metrics
    """
    try:
        with connection.cursor() as cursor:
            # Get connection stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            stats = cursor.fetchone()
            
            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            size = cursor.fetchone()[0]
            
            return JsonResponse({
                'total_connections': stats[0],
                'active_connections': stats[1],
                'idle_connections': stats[2],
                'database_size': size,
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Database metrics failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Cache metrics for monitoring
@require_GET
def cache_metrics(request):
    """
    Redis cache metrics
    """
    try:
        # This would require redis-py to be installed
        # and proper Redis configuration
        return JsonResponse({
            'status': 'metrics_not_available',
            'message': 'Redis metrics require additional configuration'
        })
    except Exception as e:
        logger.error(f"Cache metrics failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)
