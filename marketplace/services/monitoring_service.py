"""
Comprehensive Monitoring Service for Piața.ro
Tracks performance, errors, and system health across the entire platform
"""
import time
import logging
import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, List, Optional, Any
import psutil
import os

logger = logging.getLogger(__name__)

class MonitoringService:
    """Central monitoring service for platform-wide metrics"""
    
    CACHE_PREFIX = "monitoring"
    
    @classmethod
    def log_request(cls, request_path: str, response_time: float, status_code: int, user_agent: str = ""):
        """Log HTTP request metrics"""
        try:
            date_key = timezone.now().strftime('%Y-%m-%d')
            request_key = f"{cls.CACHE_PREFIX}_requests_{date_key}"
            
            request_stats = cache.get(request_key, {
                'total_requests': 0,
                'avg_response_time': 0,
                'status_codes': {},
                'endpoints': {},
                'user_agents': {}
            })
            
            request_stats['total_requests'] += 1
            
            # Update average response time
            total_time = request_stats['avg_response_time'] * (request_stats['total_requests'] - 1)
            request_stats['avg_response_time'] = (total_time + response_time) / request_stats['total_requests']
            
            # Track status codes
            status_str = str(status_code)
            request_stats['status_codes'][status_str] = request_stats['status_codes'].get(status_str, 0) + 1
            
            # Track endpoints
            endpoint = request_path.split('?')[0]  # Remove query params
            request_stats['endpoints'][endpoint] = request_stats['endpoints'].get(endpoint, 0) + 1
            
            # Track user agents (anonymized)
            if user_agent:
                # Simple user agent categorization
                ua_lower = user_agent.lower()
                if 'mobile' in ua_lower:
                    agent_type = 'mobile'
                elif 'bot' in ua_lower or 'crawler' in ua_lower:
                    agent_type = 'bot'
                else:
                    agent_type = 'desktop'
                
                request_stats['user_agents'][agent_type] = request_stats['user_agents'].get(agent_type, 0) + 1
            
            cache.set(request_key, request_stats, 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Failed to log request metrics: {e}")
    
    @classmethod
    def log_database_query(cls, query_time: float, query_type: str, table: str = ""):
        """Log database query performance"""
        try:
            date_key = timezone.now().strftime('%Y-%m-%d')
            db_key = f"{cls.CACHE_PREFIX}_database_{date_key}"
            
            db_stats = cache.get(db_key, {
                'total_queries': 0,
                'avg_query_time': 0,
                'query_types': {},
                'slow_queries': [],
                'tables': {}
            })
            
            db_stats['total_queries'] += 1
            
            # Update average query time
            total_time = db_stats['avg_query_time'] * (db_stats['total_queries'] - 1)
            db_stats['avg_query_time'] = (total_time + query_time) / db_stats['total_queries']
            
            # Track query types
            db_stats['query_types'][query_type] = db_stats['query_types'].get(query_type, 0) + 1
            
            # Track table usage
            if table:
                db_stats['tables'][table] = db_stats['tables'].get(table, 0) + 1
            
            # Track slow queries (> 100ms)
            if query_time > 0.1:
                slow_query = {
                    'time': query_time,
                    'type': query_type,
                    'table': table,
                    'timestamp': timezone.now().isoformat()
                }
                db_stats['slow_queries'].append(slow_query)
                
                # Keep only last 50 slow queries
                if len(db_stats['slow_queries']) > 50:
                    db_stats['slow_queries'] = db_stats['slow_queries'][-50:]
            
            cache.set(db_key, db_stats, 86400 * 7)
            
        except Exception as e:
            logger.error(f"Failed to log database metrics: {e}")
    
    @classmethod
    def log_error(cls, error_type: str, error_message: str, stack_trace: str = "", context: Optional[Dict] = None):
        """Log application errors"""
        try:
            date_key = timezone.now().strftime('%Y-%m-%d')
            error_key = f"{cls.CACHE_PREFIX}_errors_{date_key}"
            
            error_stats = cache.get(error_key, {
                'total_errors': 0,
                'error_types': {},
                'recent_errors': []
            })
            
            error_stats['total_errors'] += 1
            error_stats['error_types'][error_type] = error_stats['error_types'].get(error_type, 0) + 1
            
            # Store recent errors
            error_entry = {
                'type': error_type,
                'message': error_message[:500],  # Limit message length
                'timestamp': timezone.now().isoformat(),
                'context': context or {}
            }
            
            if stack_trace:
                error_entry['stack_trace'] = stack_trace[:1000]  # Limit stack trace length
            
            error_stats['recent_errors'].append(error_entry)
            
            # Keep only last 100 errors
            if len(error_stats['recent_errors']) > 100:
                error_stats['recent_errors'] = error_stats['recent_errors'][-100:]
            
            cache.set(error_key, error_stats, 86400 * 7)
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    @classmethod
    def log_cache_metrics(cls, cache_hit: bool, key: str, operation: str, response_time: float = 0):
        """Log cache performance metrics"""
        try:
            date_key = timezone.now().strftime('%Y-%m-%d')
            cache_key = f"{cls.CACHE_PREFIX}_cache_{date_key}"
            
            cache_stats = cache.get(cache_key, {
                'total_operations': 0,
                'hits': 0,
                'misses': 0,
                'avg_response_time': 0,
                'operations': {}
            })
            
            cache_stats['total_operations'] += 1
            
            if cache_hit:
                cache_stats['hits'] += 1
            else:
                cache_stats['misses'] += 1
            
            # Update average response time
            if response_time > 0:
                total_time = cache_stats['avg_response_time'] * (cache_stats['total_operations'] - 1)
                cache_stats['avg_response_time'] = (total_time + response_time) / cache_stats['total_operations']
            
            # Track operation types
            cache_stats['operations'][operation] = cache_stats['operations'].get(operation, 0) + 1
            
            cache.set(cache_key, cache_stats, 86400 * 7)
            
        except Exception as e:
            logger.error(f"Failed to log cache metrics: {e}")
    
    @classmethod
    def get_system_metrics(cls) -> Dict:
        """Get current system metrics (CPU, memory, disk)"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            
            # Process info
            process = psutil.Process(os.getpid())
            process_memory_mb = process.memory_info().rss / (1024 ** 2)
            process_threads = process.num_threads()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'status': 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
                },
                'memory': {
                    'percent': memory_percent,
                    'used_gb': round(memory_used_gb, 2),
                    'total_gb': round(memory_total_gb, 2),
                    'status': 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 95 else 'critical'
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': round(disk_used_gb, 2),
                    'total_gb': round(disk_total_gb, 2),
                    'status': 'healthy' if disk_percent < 80 else 'warning' if disk_percent < 95 else 'critical'
                },
                'process': {
                    'memory_mb': round(process_memory_mb, 2),
                    'threads': process_threads
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    @classmethod
    def get_daily_summary(cls, date: Optional[str] = None) -> Dict:
        """Get comprehensive daily summary"""
        if not date:
            date = timezone.now().strftime('%Y-%m-%d')
        
        metrics = {
            'date': date,
            'requests': cache.get(f"{cls.CACHE_PREFIX}_requests_{date}", {}),
            'database': cache.get(f"{cls.CACHE_PREFIX}_database_{date}", {}),
            'errors': cache.get(f"{cls.CACHE_PREFIX}_errors_{date}", {}),
            'cache': cache.get(f"{cls.CACHE_PREFIX}_cache_{date}", {}),
            'system': cls.get_system_metrics(),
            'location': {},  # Will be populated by LocationAnalytics if available
        }
        
        # Add location analytics if available
        try:
            from .location_analytics import LocationAnalytics
            metrics['location'] = LocationAnalytics.get_daily_stats(date)
        except ImportError:
            pass
        
        return metrics
    
    @classmethod
    def get_health_status(cls) -> Dict:
        """Get overall system health status"""
        system_metrics = cls.get_system_metrics()
        today_stats = cls.get_daily_summary()
        
        # Check various health indicators
        health_indicators = {
            'system_cpu': system_metrics.get('cpu', {}).get('status', 'unknown'),
            'system_memory': system_metrics.get('memory', {}).get('status', 'unknown'),
            'system_disk': system_metrics.get('disk', {}).get('status', 'unknown'),
        }
        
        # Check error rate
        error_stats = today_stats.get('errors', {})
        total_errors = error_stats.get('total_errors', 0)
        request_stats = today_stats.get('requests', {})
        total_requests = request_stats.get('total_requests', 1)  # Avoid division by zero
        
        error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
        health_indicators['error_rate'] = 'healthy' if error_rate < 1 else 'warning' if error_rate < 5 else 'critical'
        
        # Determine overall status
        if any(status == 'critical' for status in health_indicators.values()):
            overall_status = 'critical'
        elif any(status == 'warning' for status in health_indicators.values()):
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'status': overall_status,
            'indicators': health_indicators,
            'error_rate': round(error_rate, 2),
            'total_requests': total_requests,
            'total_errors': total_errors,
            'timestamp': timezone.now().isoformat()
        }
    
    @classmethod
    def cleanup_old_data(cls, days_to_keep: int = 30):
        """Clean up monitoring data older than specified days"""
        try:
            current_date = timezone.now().date()
            
            for i in range(days_to_keep, 365):  # Check up to a year back
                old_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Delete old cache keys
                keys_to_delete = [
                    f"{cls.CACHE_PREFIX}_requests_{old_date}",
                    f"{cls.CACHE_PREFIX}_database_{old_date}",
                    f"{cls.CACHE_PREFIX}_errors_{old_date}",
                    f"{cls.CACHE_PREFIX}_cache_{old_date}",
                ]
                
                for key in keys_to_delete:
                    cache.delete(key)
            
            logger.info(f"Cleaned up monitoring data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup monitoring data: {e}")


# Global monitoring instance
monitoring = MonitoringService()
