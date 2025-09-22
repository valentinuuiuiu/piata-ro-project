"""
Comprehensive tests for Piața.ro marketplace
"""
import json
from decimal import Decimal
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from unittest.mock import patch, MagicMock
from marketplace.models import Category, Listing, UserProfile, Favorite, Message, Report
from marketplace.services.location_service import LocationService
from marketplace.services.chat_service import MarketplaceChatService
from marketplace.utils.cache_utils import ListingCache, SearchCache, CategoryCache
from marketplace.views import ListingViewSet
from rest_framework.test import APITestCase
from rest_framework import status
import tempfile
import os

class MarketplaceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.listing = Listing.objects.create(
            title='Test Listing',
            description='Test description',
            price=Decimal('100.00'),
            location='București',
            user=self.user,
            category=self.category,
            status='active'
        )
        
    def test_user_registration(self):
        """Test user registration process"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
    def test_listing_creation(self):
        """Test listing creation with validation"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test valid listing creation
        response = self.client.post('/adauga-anunt/', {
            'title': 'Test Listing',
            'description': 'Test description',
            'price': '100.00',
            'location': 'București',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Listing.objects.filter(title='Test Listing').exists())
        
        # Test invalid listing creation
        response = self.client.post('/adauga-anunt/', {
            'title': '',  # Invalid empty title
            'description': 'Test description',
            'price': '100.00',
            'location': 'București',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 200)  # Should return form with errors
        
    def test_listing_search(self):
        """Test listing search functionality with caching"""
        # Create test listings
        Listing.objects.create(
            title='iPhone 13',
            description='Great phone',
            price=Decimal('2000.00'),
            location='Cluj-Napoca',
            user=self.user,
            category=self.category,
            status='active'
        )
        
        Listing.objects.create(
            title='Samsung Galaxy',
            description='Android phone',
            price=Decimal('1500.00'),
            location='București',
            user=self.user,
            category=self.category,
            status='active'
        )
        
        # Test search functionality
        response = self.client.get('/cautare/?q=iPhone')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 13')
        
        # Test search caching
        with patch('marketplace.utils.cache_utils.SearchCache.get_search_results') as mock_cache:
            mock_cache.return_value = None
            response = self.client.get('/cautare/?q=iPhone')
            mock_cache.assert_called_once()
            
    def test_openrouter_chat_api(self):
        """Test OpenRouter chat API with error handling"""
        # Test successful API call
        with patch('marketplace.services.chat_service.marketplace_chat_service.user_chat') as mock_chat:
            mock_chat.return_value = type('MockResponse', (), {'success': True, 'content': 'Hello! How can I help you today?'})()
            response = self.client.post('/api/openrouter-chat/', {
                'message': 'Salut, cum functioneaza platforma?'
            }, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('response', data)
            self.assertEqual(data['response'], 'Hello! How can I help you today?')
        
        # Test API error handling
        with patch('marketplace.services.chat_service.marketplace_chat_service.user_chat') as mock_chat:
            mock_chat.return_value = type('MockResponse', (), {'success': False, 'error': 'API Error'})()
            response = self.client.post('/api/openrouter-chat/', {
                'message': 'Test message'
            }, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'API Error')
            
        # Test missing message
        response = self.client.post('/api/openrouter-chat/', {
            # No message field
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Message is required')
            
    def test_location_service(self):
        """Test location service functionality with caching"""
        service = LocationService()
        
        # Test normal coordinates
        result = service.get_coordinates_from_city('București')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # lat, lng
        
        # Test caching
        with patch('marketplace.utils.cache_utils.LocationCache.get_coordinates') as mock_cache:
            mock_cache.return_value = (44.4268, 26.1025)
            result = service.get_coordinates_from_city('București')
            mock_cache.assert_called_once()
            
    def test_user_profile_creation(self):
        """Test user profile creation with validation"""
        profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'location': 'București', 
                'credits_balance': Decimal('5.00'),
                'is_premium': True
            }
        )
        self.assertTrue(created or profile.id)
        self.assertEqual(profile.credits_balance, Decimal('5.00'))
        self.assertTrue(profile.is_premium)
        
        # Test credit operations
        self.assertTrue(profile.can_promote_listing())
        self.assertTrue(profile.deduct_credits(Decimal('1.00')))
        self.assertEqual(profile.credits_balance, Decimal('4.00'))
        
    def test_listing_view_count(self):
        """Test listing view count increment"""
        initial_views = self.listing.views
        
        # Access listing detail page
        response = self.client.get(f'/listing/{self.listing.id}/')
        self.assertEqual(response.status_code, 200)
        
        # Refresh listing from database
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.views, initial_views + 1)
        
    def test_listing_images(self):
        """Test listing image handling"""
        # Create test image
        image_content = b"fake_image_content"
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg", 
            image_content, 
            content_type="image/jpeg"
        )
        
        # Test image upload
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/adauga-anunt/', {
            'title': 'Test Listing with Image',
            'description': 'Test description',
            'price': '100.00',
            'location': 'București',
            'category': self.category.id,
            'images': [uploaded_file]
        })
        self.assertEqual(response.status_code, 302)
        
        # Check if image was uploaded
        listing = Listing.objects.get(title='Test Listing with Image')
        self.assertTrue(listing.images.exists())

class CacheTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
    def test_category_cache(self):
        """Test category caching functionality"""
        # Test cache miss
        with patch('marketplace.utils.cache_utils.cache.get') as mock_get:
            mock_get.return_value = None
            result = CategoryCache.get_all_categories()
            mock_get.assert_called_once()
            
        # Test cache hit
        with patch('marketplace.utils.cache_utils.cache.get') as mock_get:
            mock_get.return_value = [{'id': 1, 'name': 'Test'}]
            result = CategoryCache.get_all_categories()
            mock_get.assert_called_once()
            
    def test_search_cache(self):
        """Test search caching functionality"""
        filters = {'category': 1, 'min_price': 100}
        
        # Test cache miss
        with patch('marketplace.utils.cache_utils.cache.get') as mock_get:
            mock_get.return_value = None
            result = SearchCache.get_search_results('active', filters)
            mock_get.assert_called_once()
            
        # Test cache hit
        with patch('marketplace.utils.cache_utils.cache.get') as mock_get:
            mock_get.return_value = ['listing1', 'listing2']
            result = SearchCache.get_search_results('active', filters)
            mock_get.assert_called_once()
            
    def test_cache_invalidation(self):
        """Test cache invalidation on model changes"""
        listing = Listing.objects.create(
            title='Test Listing',
            description='Test description',
            price=Decimal('100.00'),
            location='București',
            user=User.objects.create_user('testuser2'),
            category=self.category,
            status='active'
        )
        
        # Test cache invalidation
        with patch('marketplace.utils.cache_utils.cache.delete') as mock_delete:
            invalidate_listing_cache(listing)
            mock_delete.assert_called()

class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        response = self.client.post('/register/', {
            'username': 'hackuser',
            'password1': 'hackpass123',
            'password2': 'hackpass123'
        })
        # Should fail without CSRF token
        self.assertNotEqual(response.status_code, 200)
        
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        malicious_query = "'; DROP TABLE marketplace_listing; --"
        response = self.client.get(f'/cautare/?q={malicious_query}')
        self.assertEqual(response.status_code, 200)
        # Should not crash the application
        
    def test_xss_protection(self):
        """Test XSS protection"""
        self.client.login(username='testuser', password='testpass123')
        malicious_script = '<script>alert("XSS")</script>'
        response = self.client.post('/adauga-anunt/', {
            'title': malicious_script,
            'description': 'Test',
            'price': '100',
            'location': 'Test'
        })
        # Should not execute the script
        
    def test_rate_limiting(self):
        """Test rate limiting on authentication endpoints"""
        # Test rate limiting
        for i in range(10):
            response = self.client.post('/accounts/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            })
        
        # Should be rate limited after 5 attempts
        self.assertEqual(response.status_code, 429)
        
    def test_input_validation(self):
        """Test input validation on forms"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test price validation
        response = self.client.post('/adauga-anunt/', {
            'title': 'Test Listing',
            'description': 'Test description',
            'price': 'invalid_price',  # Invalid price
            'location': 'București',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 200)  # Should return form with errors

class PerformanceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test listings
        for i in range(100):
            Listing.objects.create(
                title=f'Test Listing {i}',
                description=f'Test description {i}',
                price=Decimal(f'{100 + i}.00'),
                location=f'City {i}',
                user=self.user,
                category=self.category,
                status='active'
            )
            
    def test_database_query_optimization(self):
        """Test database query optimization"""
        # Test optimized query with select_related and prefetch_related
        listings = Listing.objects.select_related('category', 'user').prefetch_related('images').filter(
            status='active'
        )
        
        # Query should be efficient
        self.assertGreaterEqual(len(listings), 100)
        
        # Test query optimization with indexes
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("EXPLAIN ANALYZE SELECT * FROM marketplace_listing WHERE status = 'active' ORDER BY created_at DESC LIMIT 20")
            explain_result = cursor.fetchall()
            
        # Check if query uses indexes
        explain_str = str(explain_result)
        self.assertIn('Index Scan', explain_str)
        
    def test_caching_performance(self):
        """Test caching performance improvements"""
        import time
        
        # Test without cache
        start_time = time.time()
        for _ in range(10):
            list(Listing.objects.filter(status='active'))
        without_cache_time = time.time() - start_time
        
        # Test with cache
        start_time = time.time()
        for _ in range(10):
            cached_results = SearchCache.get_search_results('active', {})
            if not cached_results:
                results = list(Listing.objects.filter(status='active'))
                SearchCache.set_search_results('active', {}, results)
        with_cache_time = time.time() - start_time
        
        # Cache should be faster
        self.assertLess(with_cache_time, without_cache_time)

class IntegrationTestCase(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
    def test_full_listing_workflow(self):
        """Test complete listing workflow from creation to deletion"""
        # Create listing
        listing = Listing.objects.create(
            title='Integration Test Listing',
            description='Integration test description',
            price=Decimal('100.00'),
            location='București',
            user=self.user,
            category=self.category,
            status='active'
        )
        
        # Add to favorites
        favorite = Favorite.objects.create(
            user=self.user,
            listing=listing
        )
        
        # Send message
        message = Message.objects.create(
            sender=self.user,
            receiver=self.user,  # Self-message for testing
            listing=listing,
            content='Test message'
        )
        
        # Report listing
        report = Report.objects.create(
            reporter=self.user,
            listing=listing,
            reason='spam',
            description='Test report'
        )
        
        # Verify all objects were created
        self.assertTrue(Listing.objects.filter(title='Integration Test Listing').exists())
        self.assertTrue(Favorite.objects.filter(user=self.user, listing=listing).exists())
        self.assertTrue(Message.objects.filter(sender=self.user, listing=listing).exists())
        self.assertTrue(Report.objects.filter(reporter=self.user, listing=listing).exists())
        
        # Clean up
        listing.delete()
        
        # Verify deletion
        self.assertFalse(Listing.objects.filter(title='Integration Test Listing').exists())
        self.assertFalse(Favorite.objects.filter(user=self.user, listing=listing).exists())
        self.assertFalse(Message.objects.filter(sender=self.user, listing=listing).exists())
        self.assertFalse(Report.objects.filter(reporter=self.user, listing=listing).exists())

class APITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser',
            password='apipass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.listing = Listing.objects.create(
            title='API Test Listing',
            description='API test description',
            price=Decimal('100.00'),
            location='București',
            user=self.user,
            category=self.category,
            status='active'
        )
        
    def test_api_listings_endpoint(self):
        """Test API listings endpoint with pagination"""
        response = self.client.get('/api/listings/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
    def test_api_listings_filtering(self):
        """Test API listings filtering"""
        # Test category filtering
        response = self.client.get(f'/api/listings/?category={self.category.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        
        # Test price filtering
        response = self.client.get('/api/listings/?min_price=50&max_price=150')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        
        # Test location filtering
        response = self.client.get('/api/listings/?location=București')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        
    def test_api_categories_endpoint(self):
        """Test API categories endpoint"""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        
    def test_authenticated_api_access(self):
        """Test authenticated API access"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/favorites/')
        self.assertEqual(response.status_code, 200)
        
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        # Test rate limiting
        for i in range(15):
            response = self.client.get('/api/listings/')
        
        # Should be rate limited
        self.assertEqual(response.status_code, 429)
        
    def test_api_pagination(self):
        """Test API pagination"""
        # Create additional listings
        for i in range(25):
            Listing.objects.create(
                title=f'API Test Listing {i}',
                description=f'API test description {i}',
                price=Decimal(f'{100 + i}.00'),
                location=f'City {i}',
                user=self.user,
                category=self.category,
                status='active'
            )
        
        # Test pagination
        response = self.client.get('/api/listings/?page_size=10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
        
    def test_api_create_listing(self):
        """Test API listing creation"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'New API Listing',
            'description': 'New API test description',
            'price': '150.00',
            'location': 'Cluj-Napoca',
            'category': self.category.id
        }
        
        response = self.client.post('/api/listings/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Listing.objects.filter(title='New API Listing').exists())
        
    def test_api_update_listing(self):
        """Test API listing update"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'Updated API Listing',
            'description': 'Updated API test description',
            'price': '200.00',
            'location': 'Timișoara',
            'category': self.category.id
        }
        
        response = self.client.put(f'/api/listings/{self.listing.id}/', data, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Updated API Listing')
        self.assertEqual(self.listing.price, Decimal('200.00'))
        
    def test_api_delete_listing(self):
        """Test API listing deletion"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/listings/{self.listing.id}/')
        self.assertEqual(response.status_code, 204)
        
        # Verify deletion
        self.assertFalse(Listing.objects.filter(id=self.listing.id).exists())
        
    def test_api_permissions(self):
        """Test API permissions"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        # Test unauthorized access
        response = self.client.put(f'/api/listings/{self.listing.id}/', {})
        self.assertEqual(response.status_code, 401)
        
        # Test authorized access
        self.client.force_authenticate(user=self.user)
        response = self.client.put(f'/api/listings/{self.listing.id}/', {})
        self.assertEqual(response.status_code, 200)
        
        # Test other user cannot modify listing
        self.client.force_authenticate(user=other_user)
        response = self.client.put(f'/api/listings/{self.listing.id}/', {})
        self.assertEqual(response.status_code, 403)

class HealthCheckTestCase(TestCase):
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['status'], 'healthy')
        
    def test_rate_limiting_endpoint(self):
        """Test rate limiting endpoint"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        # Test rate limiting
        for i in range(10):
            response = self.client.get('/health/')
        
        # Should not be rate limited (health check should be exempt)
        self.assertEqual(response.status_code, 200)

class MigrationTestCase(TransactionTestCase):
    def test_migration_safety(self):
        """Test that migrations are safe and reversible"""
        # Test migration forward
        from django.core.management import call_command
        from django.db import connection
        
        # Check if migration history is consistent
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM django_migrations ORDER BY id DESC LIMIT 1")
            latest_migration = cursor.fetchone()
            
        self.assertIsNotNone(latest_migration)
        
    def test_data_integrity(self):
        """Test data integrity constraints"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Test foreign key constraints
        listing = Listing.objects.create(
            title='Test Listing',
            description='Test description',
            price=Decimal('100.00'),
            location='București',
            user=user,
            category=category,
            status='active'
        )
        
        # Test cascade deletion
        user.delete()
        
        # Listing should be cascade deleted
        self.assertFalse(Listing.objects.filter(id=listing.id).exists())
        
    def test_unique_constraints(self):
        """Test unique constraints"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create first listing
        Listing.objects.create(
            title='Test Listing',
            description='Test description',
            price=Decimal('100.00'),
            location='București',
            user=user,
            category=category,
            status='active'
        )
        
        # Try to create duplicate listing (should fail)
        with self.assertRaises(Exception):
            Listing.objects.create(
                title='Test Listing',  # Same title
                description='Test description',
                price=Decimal('100.00'),
                location='București',
                user=user,
                category=category,
                status='active'
            )
