"""
Location Analytics Service for monitoring OpenStreetMap usage and performance
"""

import logging
from django.core.cache import cache
from django.utils import timezone
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class LocationAnalytics:
    """Analytics service for location operations"""
    
    CACHE_PREFIX = "location_analytics"
    
    @classmethod
    def log_geocoding_request(cls, query: str, success: bool, response_time: float, service: str = "nominatim"):
        """Log a geocoding request for analytics"""
        try:
            # Daily stats
            date_key = timezone.now().strftime('%Y-%m-%d')
            stats_key = f"{cls.CACHE_PREFIX}_daily_{date_key}"
            
            daily_stats = cache.get(stats_key, {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'queries': []
            })
            
            daily_stats['total_requests'] += 1
            if success:
                daily_stats['successful_requests'] += 1
            else:
                daily_stats['failed_requests'] += 1
            
            # Update average response time
            total_time = daily_stats['avg_response_time'] * (daily_stats['total_requests'] - 1)
            daily_stats['avg_response_time'] = (total_time + response_time) / daily_stats['total_requests']
            
            # Store recent queries (max 100)
            daily_stats['queries'].append({
                'query': query,
                'success': success,
                'response_time': response_time,
                'timestamp': timezone.now().isoformat()
            })
            
            if len(daily_stats['queries']) > 100:
                daily_stats['queries'] = daily_stats['queries'][-100:]
            
            cache.set(stats_key, daily_stats, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Failed to log geocoding analytics: {e}")
    
    @classmethod
    def log_location_search(cls, query: str, results_count: int, response_time: float):
        """Log a location search request"""
        try:
            date_key = timezone.now().strftime('%Y-%m-%d')
            search_key = f"{cls.CACHE_PREFIX}_search_{date_key}"
            
            search_stats = cache.get(search_key, {
                'total_searches': 0,
                'avg_results': 0,
                'avg_response_time': 0,
                'popular_queries': {}
            })
            
            search_stats['total_searches'] += 1
            
            # Update averages
            total_results = search_stats['avg_results'] * (search_stats['total_searches'] - 1)
            search_stats['avg_results'] = (total_results + results_count) / search_stats['total_searches']
            
            total_time = search_stats['avg_response_time'] * (search_stats['total_searches'] - 1)
            search_stats['avg_response_time'] = (total_time + response_time) / search_stats['total_searches']
            
            # Track popular queries
            query_lower = query.lower()
            search_stats['popular_queries'][query_lower] = search_stats['popular_queries'].get(query_lower, 0) + 1
            
            cache.set(search_key, search_stats, 86400)
            
        except Exception as e:
            logger.error(f"Failed to log search analytics: {e}")
    
    @classmethod
    def get_daily_stats(cls, date: Optional[str] = None) -> Dict:
        """Get daily location service statistics"""
        if not date:
            date = timezone.now().strftime('%Y-%m-%d')
        
        geocoding_key = f"{cls.CACHE_PREFIX}_daily_{date}"
        search_key = f"{cls.CACHE_PREFIX}_search_{date}"
        
        geocoding_stats = cache.get(geocoding_key, {})
        search_stats = cache.get(search_key, {})
        
        return {
            'date': date,
            'geocoding': geocoding_stats,
            'search': search_stats
        }
    
    @classmethod
    def get_weekly_stats(cls) -> List[Dict]:
        """Get weekly statistics"""
        stats = []
        today = timezone.now().date()
        
        for i in range(7):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats = cls.get_daily_stats(date)
            stats.append(daily_stats)
        
        return list(reversed(stats))
    
    @classmethod
    def get_service_health(cls) -> Dict:
        """Get current service health status"""
        today_stats = cls.get_daily_stats()
        geocoding = today_stats.get('geocoding', {})
        
        total_requests = geocoding.get('total_requests', 0)
        successful_requests = geocoding.get('successful_requests', 0)
        
        if total_requests == 0:
            success_rate = 100  # No requests yet today
        else:
            success_rate = (successful_requests / total_requests) * 100
        
        avg_response_time = geocoding.get('avg_response_time', 0)
        
        # Determine health status
        if success_rate >= 95 and avg_response_time < 2.0:
            status = "healthy"
        elif success_rate >= 90 and avg_response_time < 5.0:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            'status': status,
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(avg_response_time, 3),
            'total_requests_today': total_requests,
            'last_updated': timezone.now().isoformat()
        }
    
    @classmethod
    def get_popular_locations(cls, days: int = 7) -> List[Dict]:
        """Get most popular searched locations"""
        popular_queries = {}
        today = timezone.now().date()
        
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            search_key = f"{cls.CACHE_PREFIX}_search_{date}"
            search_stats = cache.get(search_key, {})
            
            day_queries = search_stats.get('popular_queries', {})
            for query, count in day_queries.items():
                popular_queries[query] = popular_queries.get(query, 0) + count
        
        # Sort by popularity
        sorted_queries = sorted(popular_queries.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'query': query, 'search_count': count}
            for query, count in sorted_queries[:20]
        ]

    @classmethod
    def log_rate_limit_hit(cls):
        """Log when we hit rate limits"""
        try:
            date_key = timezone.now().strftime('%Y-%m-%d')
            rate_limit_key = f"{cls.CACHE_PREFIX}_rate_limits_{date_key}"
            
            rate_limit_stats = cache.get(rate_limit_key, {
                'total_hits': 0,
                'timestamps': []
            })
            
            rate_limit_stats['total_hits'] += 1
            rate_limit_stats['timestamps'].append(timezone.now().isoformat())
            
            # Keep only last 100 timestamps
            if len(rate_limit_stats['timestamps']) > 100:
                rate_limit_stats['timestamps'] = rate_limit_stats['timestamps'][-100:]
            
            cache.set(rate_limit_key, rate_limit_stats, 86400)
            
        except Exception as e:
            logger.error(f"Failed to log rate limit hit: {e}")
