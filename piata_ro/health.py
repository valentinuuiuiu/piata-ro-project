"""
Health check views for monitoring and Azure deployment
"""

from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
from django.conf import settings
import redis
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Comprehensive health check for all services
    Returns 200 if all services are healthy, 503 if any service is down
    """
    health_status = {
        'status': 'healthy',
        'services': {}
    }
    overall_healthy = True
    
    # Check database
    try:
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        overall_healthy = False
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 30)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            health_status['services']['cache'] = 'healthy'
        else:
            health_status['services']['cache'] = 'unhealthy: cache test failed'
            overall_healthy = False
    except Exception as e:
        health_status['services']['cache'] = f'unhealthy: {str(e)}'
        overall_healthy = False
        logger.error(f"Cache health check failed: {e}")
    
    # Check pgvector extension
    try:
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
            if result:
                health_status['services']['pgvector'] = 'healthy'
            else:
                health_status['services']['pgvector'] = 'unhealthy: extension not found'
                # Don't mark as unhealthy since it's not critical for basic operation
    except Exception as e:
        health_status['services']['pgvector'] = f'warning: {str(e)}'
        logger.warning(f"pgvector health check failed: {e}")
    
    # Overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    
    # Add application info
    health_status['app'] = {
        'name': 'Piata.ro',
        'version': '1.0.0',
        'debug': settings.DEBUG
    }
    
    status_code = 200 if overall_healthy else 503
    return JsonResponse(health_status, status=status_code)

def ready_check(request):
    """
    Readiness check - returns 200 when app is ready to serve traffic
    """
    # Simple check to see if Django is responding
    return JsonResponse({
        'status': 'ready',
        'message': 'Application is ready to serve requests'
    })

def live_check(request):
    """
    Liveness check - returns 200 if application is running
    """
    return JsonResponse({
        'status': 'alive',
        'message': 'Application is running'
    })
