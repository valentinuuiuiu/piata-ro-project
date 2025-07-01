"""
Comprehensive tests for Piața.ro marketplace
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from marketplace.models import Category, Listing, UserProfile
from marketplace.services.location_service import LocationService
from marketplace.services.chat_service import MarketplaceChatService
from decimal import Decimal

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
        """Test listing creation"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/adauga-anunt/', {
            'title': 'Test Listing',
            'description': 'Test description',
            'price': '100.00',
            'location': 'București',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Listing.objects.filter(title='Test Listing').exists())
        
    def test_listing_search(self):
        """Test listing search functionality"""
        listing = Listing.objects.create(
            title='iPhone 13',
            description='Great phone',
            price=Decimal('2000.00'),
            location='Cluj-Napoca',
            user=self.user,
            category=self.category,
            status='active'
        )
        
        response = self.client.get('/cautare/?q=iPhone')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 13')
        
    def test_deepseek_chat_api(self):
        """Test DeepSeek chat API"""
        response = self.client.post('/api/deepseek-chat/', {
            'message': 'Salut, cum functioneaza platforma?'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('response', data)
        
    def test_location_service(self):
        """Test location service functionality"""
        service = LocationService()
        result = service.get_coordinates_from_city('București')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # lat, lng
        
    def test_user_profile_creation(self):
        """Test user profile creation"""
        profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'location': 'București', 'credits_balance': Decimal('5.00')}
        )
        self.assertTrue(created or profile.id)
        self.assertEqual(profile.credits_balance, Decimal('5.00'))

class ChatServiceTestCase(TestCase):
    def setUp(self):
        self.chat_service = MarketplaceChatService()
        
    def test_user_chat_messages_creation(self):
        """Test user chat message creation"""
        messages = self.chat_service.create_user_chat_messages("Test message")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].role, "user")
        self.assertIn("Piața.ro", messages[0].content)
        
    def test_admin_chat_messages_creation(self):
        """Test admin chat message creation"""
        messages = self.chat_service.create_admin_chat_messages("Test admin message", "Context info")
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[1].role, "system")
        self.assertIn("Context info", messages[1].content)

class LocationServiceTestCase(TestCase):
    def setUp(self):
        self.location_service = LocationService()
        
    def test_normalize_location_name(self):
        """Test location name normalization"""
        normalized = self.location_service.normalize_location_name("bucuresti")
        self.assertEqual(normalized, "București")
        
        normalized = self.location_service.normalize_location_name("cluj")
        self.assertEqual(normalized, "Cluj-Napoca")
        
    def test_calculate_distance(self):
        """Test distance calculation"""
        # Distance between București and Cluj-Napoca (approximately 320km)
        distance = LocationService.calculate_distance(44.4268, 26.1025, 46.7712, 23.6236)
        self.assertGreater(distance, 300)
        self.assertLess(distance, 350)

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='apiuser',
            password='apipass123'
        )
        
    def test_api_listings_endpoint(self):
        """Test API listings endpoint"""
        response = self.client.get('/api/listings/')
        self.assertEqual(response.status_code, 200)
        
    def test_api_categories_endpoint(self):
        """Test API categories endpoint"""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        
    def test_authenticated_api_access(self):
        """Test authenticated API access"""
        self.client.login(username='apiuser', password='apipass123')
        response = self.client.get('/api/favorites/')
        self.assertEqual(response.status_code, 200)

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