from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model, SESSION_KEY
from django.conf import settings
from unittest.mock import patch, MagicMock

User = get_user_model()

# Define placeholder Clerk redirect URLs in settings for tests
TEST_CLERK_SIGN_IN_URL = '/test-clerk/sign-in/'
TEST_CLERK_SIGN_UP_URL = '/test-clerk/sign-up/'
TEST_LOGIN_REDIRECT_URL = '/test-dashboard/'
TEST_LOGOUT_REDIRECT_URL = '/test-logged-out/'

@override_settings(
    CLERK_SIGN_IN_REDIRECT_URL=TEST_CLERK_SIGN_IN_URL,
    CLERK_SIGN_UP_REDIRECT_URL=TEST_CLERK_SIGN_UP_URL,
    LOGIN_REDIRECT_URL=TEST_LOGIN_REDIRECT_URL,
    LOGOUT_REDIRECT_URL=TEST_LOGOUT_REDIRECT_URL,
    AUTHENTICATION_BACKENDS=[
        'marketplace.clerk_auth_backend.ClerkAuthBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]
)
class AuthViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        # Note: UserProfile with clerk_user_id would be needed for full backend testing,
        # but view tests often mock the authentication layer.

    def test_clerk_login_redirect_view(self):
        response = self.client.get(reverse('marketplace:clerk_login'))
        self.assertRedirects(response, TEST_CLERK_SIGN_IN_URL, fetch_redirect_response=False)

    def test_clerk_signup_redirect_view(self):
        response = self.client.get(reverse('marketplace:clerk_signup'))
        self.assertRedirects(response, TEST_CLERK_SIGN_UP_URL, fetch_redirect_response=False)

    def test_clerk_logout_view_authenticated_user(self):
        self.client.login(username='testuser', password='password') # Standard Django login for setup
        self.assertTrue('_auth_user_id' in self.client.session)

        response = self.client.get(reverse('marketplace:clerk_logout'))
        self.assertRedirects(response, TEST_LOGOUT_REDIRECT_URL, fetch_redirect_response=False)
        self.assertFalse('_auth_user_id' in self.client.session, "User should be logged out from Django session")

    def test_clerk_logout_view_unauthenticated_user(self):
        response = self.client.get(reverse('marketplace:clerk_logout'))
        self.assertRedirects(response, TEST_LOGOUT_REDIRECT_URL, fetch_redirect_response=False)
        self.assertFalse('_auth_user_id' in self.client.session)

    @patch('marketplace.views.auth.authenticate') # Mock Django's authenticate
    @patch('marketplace.views.auth.django_login')   # Mock Django's login
    def test_clerk_callback_view_success(self, mock_django_login, mock_authenticate):
        """Test successful callback and login."""
        mock_user = self.user
        mock_authenticate.return_value = mock_user # Simulate successful authentication by backend

        # Simulate token in cookie (as per current view placeholder)
        self.client.cookies['__session'] = 'fake_clerk_session_token'
        response = self.client.get(reverse('marketplace:clerk_callback'))

        mock_authenticate.assert_called_once_with(request=response.wsgi_request, token='fake_clerk_session_token')
        mock_django_login.assert_called_once_with(response.wsgi_request, mock_user)
        self.assertRedirects(response, TEST_LOGIN_REDIRECT_URL, fetch_redirect_response=False)

    @patch('marketplace.views.auth.authenticate')
    def test_clerk_callback_view_auth_failure(self, mock_authenticate):
        """Test callback when authentication fails."""
        mock_authenticate.return_value = None # Simulate authentication failure

        self.client.cookies['__session'] = 'invalid_or_expired_token'
        response = self.client.get(reverse('marketplace:clerk_callback'))

        mock_authenticate.assert_called_once_with(request=response.wsgi_request, token='invalid_or_expired_token')
        self.assertEqual(response.status_code, 200) # Assuming it renders auth_error.html
        self.assertTemplateUsed(response, 'marketplace/auth_error.html')

    def test_clerk_callback_view_no_token(self):
        """Test callback when no token is provided."""
        response = self.client.get(reverse('marketplace:clerk_callback'))
        self.assertEqual(response.status_code, 400) # HttpResponseBadRequest

    # Example of a view protected by the decorator
    # Create a dummy view in marketplace/views/core.py or similar for this test
    # from django.http import HttpResponse
    # from marketplace.decorators import clerk_login_required
    # @clerk_login_required
    # def my_protected_view(request):
    #     return HttpResponse("Protected content")
    # And add to marketplace/urls.py: path('protected/', my_protected_view, name='protected_view')

    @patch('marketplace.views.core.my_protected_view_actual_logic') # Assuming my_protected_view calls this
    def test_clerk_login_required_authenticated(self, mock_actual_logic):
        """Test @clerk_login_required for an authenticated user."""
        # Setup: Create a dummy view and URL for testing the decorator
        # This usually requires modifying urls.py for the test environment or using test-specific urls.
        # For simplicity, we'll assume 'marketplace:profile' is protected.
        # If not, we'd need a dedicated test view.

        self.client.login(username='testuser', password='password') # Standard Django login

        # Let's assume 'marketplace:profile' is protected by @clerk_login_required
        # To make this work, 'marketplace:profile' view needs the decorator.
        # For this test, it's easier to test the decorator directly if possible,
        # or ensure a view IS decorated.

        # This test assumes 'marketplace:profile' uses the decorator.
        # If it doesn't, this test won't correctly test the decorator.
        # A better way is to create a minimal view specifically for testing the decorator.
        # For now, if 'profile' redirects, it means it's not passing the auth check.

        # Let's assume we have a url named 'test_protected_view' that uses the decorator
        # and its view function is 'my_protected_view'
        # For this example, let's imagine 'marketplace:profile' is that view.
        # This requires that the actual 'profile_view' in 'marketplace.views.profile'
        # is decorated with @clerk_login_required.

        # Since directly testing a decorated view through client.get() tests the view + decorator,
        # we'll assume 'marketplace:profile' is decorated for this example.
        try:
            profile_url = reverse('marketplace:profile')
            response = self.client.get(profile_url)
            self.assertEqual(response.status_code, 200) # Or whatever the profile view returns
        except Exception as e:
            self.fail(f"Failed to test protected view, ensure 'marketplace:profile' is configured and uses decorator. Error: {e}")


    def test_clerk_login_required_unauthenticated(self):
        """Test @clerk_login_required for an unauthenticated user."""
        # Again, assuming 'marketplace:profile' is protected.
        try:
            profile_url = reverse('marketplace:profile')
            response = self.client.get(profile_url)

            expected_redirect_url = f"{TEST_CLERK_SIGN_IN_URL}"
            # If the decorator adds a 'next' param, the expected URL would include it.
            # For now, the decorator redirects to the plain login_url.
            self.assertRedirects(response, expected_redirect_url, fetch_redirect_response=False)
        except Exception as e:
            self.fail(f"Failed to test protected view redirection, ensure 'marketplace:profile' is configured. Error: {e}")

# Need to create a minimal auth_error.html template for the callback failure test
# marketplace/templates/marketplace/auth_error.html
# Placeholder content:
# <h1>Auth Error</h1><p>{{ error_message }}</p>
#
# Also, the protected view test assumes a view is decorated.
# It would be better to create a specific dummy view for testing decorators,
# e.g. in marketplace/views/__init__.py or a test_views.py:
#
# from django.http import HttpResponse
# from marketplace.decorators import clerk_login_required
#
# @clerk_login_required
# def test_protected_view_for_decorator(request):
#   return HttpResponse("Success")
#
# And add to a test-specific urls.py or the main one if careful:
# path('test-protected/', views.test_protected_view_for_decorator, name='test_protected_decorator'),
# Then test reverse('marketplace:test_protected_decorator')
