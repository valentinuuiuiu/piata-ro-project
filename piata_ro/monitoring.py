

"""
Monitoring and metrics system for Piața.ro marketplace
"""
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.db import connection, connections
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
import psutil
import os
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect application metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self._setup_metrics()
        self._setup_custom_metrics()
        
    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        # HTTP request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['database', 'operation'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['database', 'operation'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            registry=self.registry
        )
        
        # Application metrics
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.active_listings = Gauge(
            'active_listings',
            'Number of active listings',
            registry=self.registry
        )
        
        self.total_revenue = Gauge(
            'total_revenue',
            'Total revenue',
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )
        
        # Performance metrics
        self.response_time = Histogram(
            'response_time_seconds',
            'Response time',
            registry=self.registry
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )
        
    def _setup_custom_metrics(self):
        """Setup custom application metrics"""
        self.custom_metrics = {
            'user_registration': Counter('user_registration_total', 'Total user registrations'),
            'listing_creation': Counter('listing_creation_total', 'Total listing creations'),
            'search_queries': Counter('search_queries_total', 'Total search queries'),
            'api_calls': Counter('api_calls_total', 'Total API calls'),
            'payment_transactions': Counter('payment_transactions_total', 'Total payment transactions'),
            'chat_messages': Counter('chat_messages_total', 'Total chat messages'),
            'email_sent': Counter('email_sent_total', 'Total emails sent'),
            'file_uploads': Counter('file_uploads_total', 'Total file uploads'),
        }
        
        # Add custom metrics to registry
        for metric in self.custom_metrics.values():
            metric.registry = self.registry
            
        # Performance tracking
        self.response_times = defaultdict(lambda: deque(maxlen=100))
        self.error_rates = defaultdict(lambda: deque(maxlen=100))
        
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        
    def record_db_query(self, database: str, operation: str, duration: float):
        """Record database query metrics"""
        self.db_queries_total.labels(database=database, operation=operation).inc()
        self.db_query_duration.labels(database=database, operation=operation).observe(duration)
        
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics"""
        self.cache_operations_total.labels(operation=operation, result=result).inc()
        
    def record_error(self, error_type: str, endpoint: str):
        """Record error metrics"""
        self.errors_total.labels(error_type=error_type, endpoint=endpoint).inc()
        
    def record_custom_metric(self, metric_name: str, value: float = 1.0):
        """Record custom metric"""
        if metric_name in self.custom_metrics:
            self.custom_metrics[metric_name].inc(value)
            
    def record_response_time(self, endpoint: str, response_time: float):
        """Record response time"""
        self.response_times[endpoint].append(response_time)
        
    def update_system_metrics(self):
        """Update system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.disk_usage.set(disk.percent)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            cache_stats = cache._cache.stats() if hasattr(cache, '_cache') else {}
            
            total_operations = (
                cache_stats.get('hits', 0) + 
                cache_stats.get('misses', 0) + 
                cache_stats.get('hits', 0)
            )
            
            hit_ratio = cache_stats.get('hits', 0) / total_operations if total_operations > 0 else 0
            
            self.cache_hit_ratio.set(hit_ratio)
            
            return {
                'hits': cache_stats.get('hits', 0),
                'misses': cache_stats.get('misses', 0),
                'hit_ratio': hit_ratio,
                'total_operations': total_operations
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        performance_data = {}
        
        for endpoint, times in self.response_times.items():
            if times:
                performance_data[endpoint] = {
                    'avg_response_time': sum(times) / len(times),
                    'min_response_time': min(times),
                    'max_response_time': max(times),
                    'count': len(times)
                }
                
        return performance_data
        
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics"""
        error_data = {}
        
        for endpoint, errors in self.error_rates.items():
            if errors:
                error_data[endpoint] = {
                    'error_count': len(errors),
                    'error_rate': len(errors) / max(1, len(self.response_times.get(endpoint, [])))
                }
                
        return error_data
        
    def generate_metrics(self) -> str:
        """Generate metrics in Prometheus format"""
        self.update_system_metrics()
        return generate_latest(self.registry).decode('utf-8')


class ApplicationMonitor:
    """Main application monitor"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.monitoring_enabled = getattr(settings, 'MONITORING_ENABLED', True)
        self.monitoring_interval = getattr(settings, 'MONITORING_INTERVAL', 60)
        self.background_thread = None
        self.running = False
        
    def start_background_monitoring(self):
        """Start background monitoring thread"""
        if not self.monitoring_enabled:
            return
            
        if self.background_thread and self.background_thread.is_alive():
            return
            
        self.running = True
        self.background_thread = threading.Thread(target=self._monitoring_loop)
        self.background_thread.daemon = True
        self.background_thread.start()
        
        logger.info("Background monitoring started")
        
    def stop_background_monitoring(self):
        """Stop background monitoring thread"""
        self.running = False
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=5)
            
        logger.info("Background monitoring stopped")
        
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                self.update_application_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
                
    def update_application_metrics(self):
        """Update application metrics"""
        try:
            # Update database metrics
            self._update_database_metrics()
            
            # Update cache metrics
            self._update_cache_metrics()
            
            # Update application-specific metrics
            self._update_application_specific_metrics()
            
            # Cache metrics
            self._cache_metrics()
            
        except Exception as e:
            logger.error(f"Error updating application metrics: {e}")
            
    def _update_database_metrics(self):
        """Update database metrics"""
        try:
            for alias in settings.DATABASES:
                connection = connections[alias]
                
                if hasattr(connection, 'queries_log'):
                    queries = connection.queries_log
                    
                    for query in queries:
                        duration = float(query.get('time', 0))
                        operation = self._extract_operation_type(query.get('sql', ''))
                        
                        self.metrics_collector.record_db_query(alias, operation, duration)
                        
        except Exception as e:
            logger.error(f"Error updating database metrics: {e}")
            
    def _extract_operation_type(self, sql: str) -> str:
        """Extract operation type from SQL query"""
        sql = sql.strip().upper()
        
        if sql.startswith('SELECT'):
            return 'select'
        elif sql.startswith('INSERT'):
            return 'insert'
        elif sql.startswith('UPDATE'):
            return 'update'
        elif sql.startswith('DELETE'):
            return 'delete'
        elif sql.startswith('CREATE'):
            return 'create'
        elif sql.startswith('ALTER'):
            return 'alter'
        elif sql.startswith('DROP'):
            return 'drop'
        else:
            return 'other'
            
    def _update_cache_metrics(self):
        """Update cache metrics"""
        try:
            cache_stats = self.metrics_collector.get_cache_stats()
            
            # Store cache stats in cache for dashboard
            cache.set('cache_stats', cache_stats, 300)
            
        except Exception as e:
            logger.error(f"Error updating cache metrics: {e}")
            
    def _update_application_specific_metrics(self):
        """Update application-specific metrics"""
        try:
            # Update active users
            from django.contrib.auth.models import User
            active_users = User.objects.filter(is_active=True).count()
            self.metrics_collector.active_users.set(active_users)
            
            # Update active listings
            from marketplace.models import Listing
            active_listings = Listing.objects.filter(status='active').count()
            self.metrics_collector.active_listings.set(active_listings)
            
            # Update total revenue (if applicable)
            from django.db.models import Sum
            from marketplace.models import Transaction
            
            total_revenue = Transaction.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            self.metrics_collector.total_revenue.set(float(total_revenue))
            
        except Exception as e:
            logger.error(f"Error updating application-specific metrics: {e}")
            
    def _cache_metrics(self):
        """Cache metrics for dashboard"""
        try:
            metrics_data = {
                'timestamp': timezone.now().isoformat(),
                'system_metrics': {
                    'cpu_usage': self.metrics_collector.cpu_usage._value._value,
                    'memory_usage': self.metrics_collector.memory_usage._value._value,
                    'disk_usage': self.metrics_collector.disk_usage._value._value,
                },
                'performance_metrics': self.metrics_collector.get_performance_metrics(),
                'error_metrics': self.metrics_collector.get_error_metrics(),
                'cache_stats': self.metrics_collector.get_cache_stats(),
            }
            
            cache.set('application_metrics', metrics_data, 300)
            
        except Exception as e:
            logger.error(f"Error caching metrics: {e}")
            
    def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Get metrics dashboard data"""
        try:
            cached_metrics = cache.get('application_metrics')
            
            if cached_metrics:
                return cached_metrics
                
            # If no cached metrics, generate fresh ones
            self.update_application_metrics()
            return cache.get('application_metrics', {})
            
        except Exception as e:
            logger.error(f"Error getting metrics dashboard: {e}")
            return {}
            
    def record_event(self, event_type: str, data: Dict[str, Any]):
        """Record custom event"""
        try:
            event_key = f"event_{event_type}_{int(time.time() // 3600)}"  # Hourly buckets
            
            events = cache.get(event_key, [])
            events.append({
                'timestamp': timezone.now().isoformat(),
                'type': event_type,
                'data': data
            })
            
            # Keep only last 1000 events
            if len(events) > 1000:
                events = events[-1000:]
                
            cache.set(event_key, events, 3600)  # Cache for 1 hour
            
        except Exception as e:
            logger.error(f"Error recording event: {e}")


# Global monitor instance
application_monitor = ApplicationMonitor()


# Middleware for metrics collection
class MetricsMiddleware:
    """Middleware to collect metrics"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        if application_monitor.monitoring_enabled:
            application_monitor.metrics_collector.record_http_request(
                method=request.method,
                endpoint=request.path,
                status_code=response.status_code,
                duration=duration
            )
            
            application_monitor.metrics_collector.record_response_time(
                endpoint=request.path,
                response_time=duration
            )
            
        return response


# Views for metrics
@require_http_methods(["GET"])
def metrics_view(request):
    """Prometheus metrics endpoint"""
    if not application_monitor.monitoring_enabled:
        return JsonResponse({'error': 'Monitoring disabled'}, status=503)
        
    try:
        metrics = application_monitor.metrics_collector.generate_metrics()
        return HttpResponse(metrics, content_type='text/plain')
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def dashboard_view(request):
    """Metrics dashboard endpoint"""
    if not application_monitor.monitoring_enabled:
        return JsonResponse({'error': 'Monitoring disabled'}, status=503)
        
    try:
        dashboard_data = application_monitor.get_metrics_dashboard()
        return JsonResponse(dashboard_data, json_dumps_params={'indent': 2})
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def health_metrics_view(request):
    """Health metrics endpoint"""
    if not application_monitor.monitoring_enabled:
        return JsonResponse({'error': 'Monitoring disabled'}, status=503)
        
    try:
        from .health_checks import health_check_manager
        
        health_results = health_check_manager.run_checks()
        metrics_data = application_monitor.get_metrics_dashboard()
        
        combined_data = {
            'health': health_results,
            'metrics': metrics_data,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(combined_data, json_dumps_params={'indent': 2})
        
    except Exception as e:
        logger.error(f"Error generating health metrics: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def record_event_view(request):
    """Record custom event endpoint"""
    if not application_monitor.monitoring_enabled:
        return JsonResponse({'error': 'Monitoring disabled'}, status=503)
        
    try:
        data = json.loads(request.body)
        event_type = data.get('type')
        event_data = data.get('data', {})
        
        if not event_type:
            return JsonResponse({'error': 'Event type is required'}, status=400)
            
        application_monitor.record_event(event_type, event_data)
        
        return JsonResponse({'status': 'success', 'message': 'Event recorded'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error recording event: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# Export monitoring functions
__all__ = [
    'MetricsCollector',
    'ApplicationMonitor',
    'MetricsMiddleware',
    'application_monitor',
    'metrics_view',
    'dashboard_view',
    'health_metrics_view',
    'record_event_view'
]

