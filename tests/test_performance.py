"""
Performance tests for Piața.ro marketplace
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.urls import reverse
from marketplace.models import Category, Listing, UserProfile
from decimal import Decimal
import time
from django.db import connection
from django.test import TransactionTestCase


# class PerformanceTestCase(TransactionTestCase):
#     """Test performance of critical operations"""
    
#     def setUp(self):
#         self.client = Client()
#         # Create test data
#         self.categories = []
#         for i in range(5):
#             cat = Category.objects.create(
#                 name=f'Category {i}',
#                 slug=f'category-{i}'
#             )
#             self.categories.append(cat)
        
#         # Create users
#         self.users = []
#         for i in range(10):
#             user = User.objects.create_user(
#                 username=f'user{i}',
#                 email=f'user{i}@example.com',
#                 password='testpass123'
#             )
#             self.users.append(user)
        
#         # Create listings
#         self.listings = []
#         for i in range(100):
#             listing = Listing.objects.create(
#                 title=f'Test Listing {i}',
#                 description=f'Description for listing {i}',
#                 price=Decimal(str(100 + i * 10)),
#                 location='București',
#                 user=self.users[i % 10],
#                 category=self.categories[i % 5],
#                 status='active',
#                 latitude=44.4268 + (i * 0.001),
#                 longitude=26.1025 + (i * 0.001)
#             )
#             self.listings.append(listing)
    
#     def test_homepage_load_time(self):
#         """Test homepage load time with many listings"""
#         start_time = time.time()
#         response = self.client.get('/')
#         end_time = time.time()
        
#         self.assertEqual(response.status_code, 200)
#         load_time = end_time - start_time
#         self.assertLess(load_time, 1.0, f"Homepage took {load_time}s to load, should be under 1s")
    
#     def test_search_performance(self):
#         """Test search performance"""
#         queries = ['Test', 'Listing', 'București', 'Description']
        
#         for query in queries:
#             with self.subTest(query=query):
#                 start_time = time.time()
#                 response = self.client.get('/cautare/', {'q': query})
#                 end_time = time.time()
                
#                 self.assertEqual(response.status_code, 200)
#                 load_time = end_time - start_time
#                 self.assertLess(load_time, 0.5, f"Search for '{query}' took {load_time}s")
    
#     def test_category_filter_performance(self):
#         """Test category filtering performance"""
#         for category in self.categories[:3]:
#             with self.subTest(category=category.name):
#                 start_time = time.time()
#                 response = self.client.get('/anunturi/', {'category': category.id})
#                 end_time = time.time()
                
#                 self.assertEqual(response.status_code, 200)
#                 load_time = end_time - start_time
#                 self.assertLess(load_time, 0.5, f"Category filter took {load_time}s")
    
#     def test_database_query_count(self):
#         """Test that views don't have N+1 query problems"""
#         with self.assertNumQueries(10):  # Adjust based on actual needs
#             response = self.client.get('/anunturi/')
#             self.assertEqual(response.status_code, 200)
    
#     def test_location_search_performance(self):
#         """Test geospatial search performance"""
#         start_time = time.time()
#         response = self.client.get('/api/listings/', {
#             'ref_latitude': 44.4268,
#             'ref_longitude': 26.1025,
#             'radius': 10
#         })
#         end_time = time.time()
        
#         self.assertEqual(response.status_code, 200)
#         load_time = end_time - start_time
#         self.assertLess(load_time, 0.5, f"Geospatial search took {load_time}s")
    
#     def test_concurrent_requests(self):
#         """Test handling of concurrent requests"""
#         import threading
#         import queue
        
#         results = queue.Queue()
        
#         def make_request():
#             start = time.time()
#             response = self.client.get('/anunturi/')
#             results.put({
#                 'status': response.status_code,
#                 'time': time.time() - start
#             })
        
#         threads = []
#         for _ in range(10):
#             t = threading.Thread(target=make_request)
#             threads.append(t)
#             t.start()
        
#         for t in threads:
#             t.join()
        
#         # Check all requests succeeded
#         total_time = 0
#         while not results.empty():
#             result = results.get()
#             self.assertEqual(result['status'], 200)
#             total_time += result['time']
        
#         avg_time = total_time / 10
#         self.assertLess(avg_time, 1.0, f"Average concurrent request time: {avg_time}s")


# class DatabaseOptimizationTest(TestCase):
#     """Test database optimization strategies"""
    
#     def test_index_usage(self):
#         """Ensure queries are using indexes properly"""
#         from django.db import connection
        
#         # Create test data
#         user = User.objects.create_user('testuser', 'test@example.com', 'pass')
#         category = Category.objects.create(name='Test', slug='test')
        
#         for i in range(50):
#             Listing.objects.create(
#                 title=f'Item {i}',
#                 price=Decimal('100'),
#                 location='Test',
#                 user=user,
#                 category=category,
#                 status='active'
#             )
        
#         with connection.cursor() as cursor:
#             # Test that status+created_at index is used
#             cursor.execute(
#                 "EXPLAIN QUERY PLAN SELECT * FROM marketplace_listing "
#                 "WHERE status = 'active' ORDER BY created_at DESC"
#             )
#             plan = cursor.fetchall()
#             # Check that an index is being used (SQLite specific)
#             self.assertTrue(any('USING INDEX' in str(row) for row in plan))
