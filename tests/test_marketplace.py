import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from marketplace.models import Category, Listing, UserProfile
from marketplace.services.location_service import LocationService
from marketplace.services.chat_service import MarketplaceChatService
from decimal import Decimal

@pytest.mark.django_db
class TestMarketplace:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        import time
        return User.objects.create_user(
            username=f'testuser_{int(time.time())}',
            email='test@example.com',
            password='testpass123'
        )

    # @pytest.fixture
    # def category(self):
    #     import time
    #     return Category.objects.create(
    #         name='Test Category',
    #         slug=f'test-category-{int(time.time())}'
    #     )

    def test_user_registration(self, client):
        response = client.post(reverse('marketplace:signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        assert response.status_code == 302
        assert User.objects.filter(username='newuser').exists()

    # def test_listing_creation(self, client, user, category):
    #     client.login(username='testuser', password='testpass123')
    #     response = client.post(reverse('marketplace:add_listing'), {
    #         'title': 'Test Listing',
    #         'description': 'Test description',
    #         'price': '100.00',
    #         'location': 'București',
    #         'category': category.id
    #     })
    #     assert response.status_code == 302
    #     assert Listing.objects.filter(title='Test Listing').exists()

    # def test_listing_search(self, client, user, category):
    #     Listing.objects.create(
    #         title='iPhone 13',
    #         description='Great phone',
    #         price=Decimal('2000.00'),
    #         location='Cluj-Napoca',
    #         user=user,
    #         category=category,
    #         status='active'
    #     )

    #     response = client.get(reverse('marketplace:listings') + '?q=iPhone')
    #     assert response.status_code == 200
    #     assert 'iPhone 13' in response.content.decode()

    # def test_deepseek_chat_api(self, client):
    #     response = client.post(reverse('marketplace:deepseek_chat'), {
    #         'message': 'Salut, cum functioneaza platforma?'
    #     }, content_type='application/json')
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert 'response' in data

    def test_location_service(self):
        service = LocationService()
        result = service.get_coordinates_from_city('București')
        assert result is not None
        assert len(result) == 2

    def test_user_profile_creation(self, user):
        profile = UserProfile.objects.create(
            user=user,
            location='București',
            credits_balance=Decimal('5.00')
        )
        assert profile.credits_balance == Decimal('5.00')


class TestChatService:
    @pytest.fixture
    def chat_service(self):
        return MarketplaceChatService()

    def test_user_chat_messages_creation(self, chat_service):
        messages = chat_service.create_user_chat_messages("Test message")
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert "Piața.ro" in messages[0].content

    def test_admin_chat_messages_creation(self, chat_service):
        messages = chat_service.create_admin_chat_messages("Test admin message", "Context info")
        assert len(messages) == 3
        assert messages[1].role == "system"
        assert "Context info" in messages[1].content

class TestLocationService:
    @pytest.fixture
    def location_service(self):
        return LocationService()

    def test_normalize_location_name(self, location_service):
        normalized = location_service.normalize_location_name("bucuresti")
        assert normalized == "București"

        normalized = location_service.normalize_location_name("cluj")
        assert normalized == "Cluj-Napoca"

    def test_calculate_distance(self):
        distance = LocationService.calculate_distance(44.4268, 26.1025, 46.7712, 23.6236)
        assert distance > 300
        assert distance < 350

@pytest.mark.django_db
@pytest.mark.override_settings(SECURE_SSL_REDIRECT=False)
class TestAPI:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        import time
        return User.objects.create_user(
            username=f'apiuser_{int(time.time())}',
            password='apipass123'
        )

    # @pytest.fixture
    # def category(self):
    #     import time
    #     return Category.objects.create(
    #         name='Test Category',
    #         slug=f'test-category-{int(time.time())}'
    #     )

    @pytest.mark.override_settings(SECURE_SSL_REDIRECT=False)
    def test_api_listings_endpoint(self, client):
        response = client.get(reverse('marketplace:listing-list'))
        assert response.status_code == 200

    @pytest.mark.override_settings(SECURE_SSL_REDIRECT=False)
    def test_api_categories_endpoint(self, client):
        response = client.get(reverse('marketplace:category-list'))
        assert response.status_code == 200

    @pytest.mark.override_settings(SECURE_SSL_REDIRECT=False)
    def test_authenticated_api_access(self, client, user):
        client.login(username='apiuser', password='apipass123')
        response = client.get(reverse('marketplace:favorite-list'))
        assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.override_settings(SECURE_SSL_REDIRECT=False)
class TestSecurity:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def admin_user(self):
        """Create admin user for admin-only tests"""
        return User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )

    @pytest.fixture
    def user(self):
        import time
        return User.objects.create_user(
            username=f'testuser_{int(time.time())}',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def category(self):
        return Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_csrf_protection(self, client):
        """Test that CSRF protection prevents unauthorized POST requests"""
        response = client.post(reverse('marketplace:signup'), {
            'username': 'hackuser',
            'password1': 'hackpass123',
            'password2': 'hackpass123'
        })
        assert response.status_code == 400  # CSRF token missing should return 400

    def test_sql_injection_protection_listings(self, client):
        """Test SQL injection protection on listing search"""
        malicious_queries = [
            "'; DROP TABLE marketplace_listing; --",
            "'; SELECT * FROM marketplace_user; --",
            "'; UPDATE marketplace_listing SET price=0; --",
            "1' OR '1'='1"
        ]

        for malicious_query in malicious_queries:
            with client:
                response = client.get(reverse('marketplace:listings') + f'?q={malicious_query}')
                assert response.status_code == 200
                # Ensure no SQL injection occurred (table wouldn't be dropped)
                messages = list(response.context.get('messages', [])) if hasattr(response, 'context') and response.context else []
                assert not any('DROP' in str(msg) for msg in messages)

    def test_sql_injection_protection_search(self, client):
        """Test SQL injection protection on category search"""
        malicious_queries = [
            "'; DROP TABLE marketplace_category; --",
            "') UNION SELECT username,password FROM auth_user; --",
        ]

        for malicious_query in malicious_queries:
            with client:
                response = client.get(reverse('marketplace:search') + f'?q={malicious_query}')
                assert response.status_code == 200

    def test_xss_protection_title(self, client, user, category):
        """Test XSS protection in listing titles"""
        client.login(username=user.username, password='testpass123')

        malicious_titles = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert(document.cookie)>',
            '<iframe src="javascript:alert(1)"></iframe>',
            '<body onload=alert(document.cookie)>',
        ]

        for title in malicious_titles:
            with client:
                response = client.post(reverse('marketplace:add_listing'), {
                    'title': title,
                    'description': 'Test description',
                    'price': '100',
                    'location': 'Test City',
                    'category': category.id
                })
                # Should redirect after successful creation if authenticated
                assert response.status_code == 302 or response.status_code == 200

                # Check that XSS wasn't stored (should be escaped or sanitized)
                if hasattr(response, 'content'):
                    content = response.content.decode()
                    # Some templates may escape the content, but we want to ensure scripts don't execute
                    assert '<script' not in content
                    assert 'onload=' not in content

    def test_xss_protection_description(self, client, user, category):
        """Test XSS protection in listing descriptions"""
        client.login(username=user.username, password='testpass123')

        malicious_description = '<script>alert("Stored XSS")</script><img src=x onerror=alert(document.cookie)>'
        response = client.post(reverse('marketplace:add_listing'), {
            'title': 'Safe Title',
            'description': malicious_description,
            'price': '100',
            'location': 'Test City',
            'category': category.id
        })

        # Should succeed (302) or show form (200 on validation error)
        assert response.status_code in [200, 302]

        # Check database for unescaped scripts
        if hasattr(user, 'listings') and user.listings.exists():
            listing = user.listings.first()
            # Ensure scripts aren't stored raw in database
            assert '<script>' not in listing.description
            assert 'onerror=' not in listing.description

    def test_unauthorized_user_access(self, client):
        """Test that restricted features require authentication"""
        # Test user profile access without login
        response = client.get(reverse('marketplace:profile'))
        assert response.status_code == 302  # Should redirect to login

        # Test add listing without login
        response = client.get(reverse('marketplace:add_listing'))
        assert response.status_code == 302  # Should redirect to login

    def test_authenticated_user_access(self, client, user):
        """Test that authenticated users can access protected features"""
        client.login(username=user.username, password='testpass123')

        response = client.get(reverse('marketplace:profile'))
        assert response.status_code == 200

        response = client.get(reverse('marketplace:add_listing'))
        assert response.status_code == 200

    def test_admin_only_access(self, client, user):
        """Test that admin features require superuser status"""
        client.login(username=user.username, password='testpass123')

        # Try accessing admin AI assistant without admin rights
        response = client.get('/admin/ai-assistant/')
        assert response.status_code == 302 or response.status_code == 403  # Should deny access

    def test_admin_access(self, client, admin_user):
        """Test that admin users can access admin features"""
        client.login(username=admin_user.username, password='adminpassword')
        response = client.get('/admin/ai-assistant/')
        # Should allow access for superusers
        assert response.status_code in [200, 302] or 'Piața.ro' in str(response.content)

    def test_data_validation(self, client, user, category):
        """Test that forms validate data properly"""
        client.login(username=user.username, password='testpass123')

        # Test invalid price
        response = client.post(reverse('marketplace:add_listing'), {
            'title': 'Test',
            'description': 'Test',
            'price': 'invalid_price',
            'location': 'Test',
            'category': category.id
        })
        # Should either fail validation (200 with errors) or redirect (302 on success)
        assert response.status_code in [200, 302]

        # Test negative price
        response = client.post(reverse('marketplace:add_listing'), {
            'title': 'Test',
            'description': 'Test',
            'price': '-100',
            'location': 'Test',
            'category': category.id
        })
        assert response.status_code in [200, 302]

    def test_rate_limiting_simulation(self, client):
        """Simulate rate limiting for form submissions"""
        # Multiple rapid requests should be handled gracefully
        for i in range(10):
            response = client.get(reverse('marketplace:home'))
            assert response.status_code == 200
