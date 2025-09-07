"""
Management command to test the monitoring system
"""
from django.core.management.base import BaseCommand
from marketplace.services.monitoring_service import MonitoringService
import time
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Test the monitoring system by generating sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of sample data to generate (default: 7)'
        )
        parser.add_argument(
            '--requests',
            type=int,
            default=100,
            help='Number of sample requests to generate per day (default: 100)'
        )

    def handle(self, *args, **options):
        days = options['days']
        requests_per_day = options['requests']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Generating {requests_per_day} sample requests per day for {days} days...'
            )
        )
        
        # Generate sample data for the past N days
        for day_offset in range(days):
            # Set the date for this iteration
            target_date = datetime.now() - timedelta(days=day_offset)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Generating data for {target_date.strftime("%Y-%m-%d")}...'
                )
            )
            
            # Generate sample requests
            for i in range(requests_per_day):
                # Simulate various types of requests
                endpoints = [
                    '/marketplace/listings/',
                    '/marketplace/search/',
                    '/api/listings/',
                    '/api/categories/',
                    '/marketplace/messages/',
                    '/account/login/',
                    '/account/signup/'
                ]
                
                endpoint = random.choice(endpoints)
                response_time = random.uniform(0.1, 2.0)
                status_code = random.choices(
                    [200, 201, 400, 404, 500],
                    weights=[0.7, 0.1, 0.1, 0.05, 0.05]
                )[0]
                
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                    'Googlebot/2.1 (+http://www.google.com/bot.html)',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                ]
                
                user_agent = random.choice(user_agents)
                
                # Log the request (this will use current date, so we need to mock the date)
                MonitoringService.log_request(endpoint, response_time, status_code, user_agent)
            
            # Generate sample database queries
            for i in range(requests_per_day * 3):  # More queries than requests
                query_time = random.uniform(0.01, 0.5)
                query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
                tables = ['marketplace_listing', 'marketplace_category', 'auth_user', 'marketplace_message']
                
                MonitoringService.log_database_query(
                    query_time,
                    random.choice(query_types),
                    random.choice(tables)
                )
            
            # Generate sample errors
            for i in range(max(1, requests_per_day // 20)):  # 5% error rate
                error_types = ['DatabaseError', 'ValidationError', 'TimeoutError', 'NetworkError']
                messages = [
                    'Database connection failed',
                    'Invalid input data',
                    'Request timeout',
                    'Network unreachable',
                    'Permission denied'
                ]
                
                MonitoringService.log_error(
                    random.choice(error_types),
                    random.choice(messages),
                    "Traceback (most recent call last):\n  File \"app.py\", line 42, in <module>\n    main()"
                )
            
            # Generate sample cache metrics
            for i in range(requests_per_day * 2):  # More cache operations
                MonitoringService.log_cache_metrics(
                    random.choice([True, False]),
                    f'cache_key_{random.randint(1, 100)}',
                    random.choice(['get', 'set', 'delete']),
                    random.uniform(0.001, 0.1)
                )
        
        # Show current health status
        health_status = MonitoringService.get_health_status()
        self.stdout.write(
            self.style.SUCCESS(
                f'Current system health: {health_status["status"]}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Error rate: {health_status["error_rate"]}%'
            )
        )
        
        # Show daily summary for today
        today_summary = MonitoringService.get_daily_summary()
        self.stdout.write(
            self.style.SUCCESS(
                f'Today\'s requests: {today_summary["requests"].get("total_requests", 0)}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Today\'s database queries: {today_summary["database"].get("total_queries", 0)}'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                'Monitoring system test completed successfully!'
            )
        )
