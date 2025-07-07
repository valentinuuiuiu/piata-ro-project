from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings
from unittest.mock import patch, MagicMock

from marketplace.models import UserProfile
from marketplace.clerk_auth_backend import ClerkAuthBackend

User = get_user_model()

class ClerkAuthBackendTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.backend = ClerkAuthBackend()

        # Ensure CLERK_SECRET_KEY is set for backend initialization
        # If it's not already in the test settings, you might need to override settings
        if not hasattr(settings, 'CLERK_SECRET_KEY') or not settings.CLERK_SECRET_KEY:
            settings.CLERK_SECRET_KEY = 'test_clerk_secret_key'

    @patch('marketplace.clerk_auth_backend.Clerk') # Mock the Clerk SDK client initialization
    def test_authenticate_no_token_provided(self, MockClerk):
        """Test authenticate returns None if no token is provided in request or args."""
        request = self.factory.get('/some-path')
        self.assertIsNone(self.backend.authenticate(request))

        request_with_empty_auth = self.factory.get('/some-path', HTTP_AUTHORIZATION='')
        self.assertIsNone(self.backend.authenticate(request_with_empty_auth))

        request_with_invalid_bearer = self.factory.get('/some-path', HTTP_AUTHORIZATION='Invalid token')
        self.assertIsNone(self.backend.authenticate(request_with_invalid_bearer))

    # --- IMPORTANT NOTE ---
    # The following tests are based on the *placeholder* logic in ClerkAuthBackend.
    # Specifically, it assumes `token` IS the `clerk_user_id` and does not
    # perform real JWT verification. These tests will need significant updates
    # once real JWT verification is implemented in the backend.
    # For now, they test the backend's current placeholder structure.

    @patch.object(ClerkAuthBackend, 'authenticate') # More direct patch if __init__ is complex
    def test_authenticate_valid_token_existing_user(self, mock_authenticate_method):
        """
        Test authenticate with a valid token (placeholder: clerk_user_id) for an existing user.
        This test currently relies on the placeholder logic where token IS clerk_user_id.
        """
        clerk_user_id = "user_clerk_test_existing"
        expected_user = User.objects.create_user(username='existinguser', email='existing@example.com')
        UserProfile.objects.create(user=expected_user, clerk_user_id=clerk_user_id)

        request = self.factory.get('/') # Dummy request

        # Configure the mock for the placeholder logic
        # This bypasses the actual token verification and simulates finding a user by clerk_user_id
        def side_effect_placeholder_auth(request_arg, token=None, **kwargs):
            if token == clerk_user_id:
                try:
                    profile = UserProfile.objects.get(clerk_user_id=token)
                    return profile.user
                except UserProfile.DoesNotExist:
                    return None
            return None

        # We are testing the structure, so we mock the token processing part
        # and assume it successfully extracts clerk_user_id.
        # The actual self.backend.authenticate will be called.
        # This test is a bit tricky because the backend's authenticate itself is a placeholder.

        # Let's refine the backend to make it more testable for its current placeholder state.
        # For now, this test might be more of an integration test of the placeholder.

        # Re-evaluating how to test the placeholder:
        # The current backend.authenticate directly uses the token as clerk_user_id.
        auth_user = self.backend.authenticate(request, token=clerk_user_id)
        self.assertEqual(auth_user, expected_user)

    @patch.object(ClerkAuthBackend, 'authenticate')
    def test_authenticate_valid_token_new_user(self, mock_authenticate_method):
        """
        Test authenticate with a valid token (placeholder: clerk_user_id) for a new user.
        This currently tests that if the placeholder logic for user creation was implemented,
        it would be called. Since it's not, it should return None.
        """
        clerk_user_id = "user_clerk_test_new"
        # Placeholder: if user creation was implemented, it would use these:
        # user_email = "newuser@example.com"
        # first_name = "New"
        # last_name = "User"

        request = self.factory.get('/')

        # Based on current placeholder (no user creation, just lookup):
        auth_user = self.backend.authenticate(request, token=clerk_user_id)
        self.assertIsNone(auth_user, "User creation is not implemented in placeholder, should return None.")

        # If user creation were implemented in the backend:
        # mock_clerk_api_user = MagicMock(spec=ClerkUser) # from clerk_sdk.models.user
        # mock_clerk_api_user.id = clerk_user_id
        # mock_clerk_api_user.email_addresses = [MagicMock(email_address=user_email, id="em_1")]
        # mock_clerk_api_user.first_name = first_name
        # mock_clerk_api_user.last_name = last_name
        #
        # # Mock the (currently non-existent) part of the backend that would fetch user details from Clerk
        # with patch.object(self.backend.clerk_client.users, 'get_user', return_value=mock_clerk_api_user):
        #     authenticated_user = self.backend.authenticate(request, token="valid_jwt_for_new_user")
        #     self.assertIsNotNone(authenticated_user)
        #     self.assertEqual(authenticated_user.email, user_email)
        #     self.assertEqual(authenticated_user.profile.clerk_user_id, clerk_user_id)
        #     self.assertTrue(User.objects.filter(email=user_email).exists())

    @patch.object(ClerkAuthBackend, 'authenticate')
    def test_authenticate_invalid_token(self, mock_authenticate_method):
        """Test authenticate with an invalid token (placeholder: non-existent clerk_user_id)."""
        request = self.factory.get('/')
        # Based on current placeholder:
        auth_user = self.backend.authenticate(request, token="invalid_clerk_user_id_or_token")
        self.assertIsNone(auth_user)

    def test_get_user_existing(self):
        """Test get_user for an existing user."""
        user = User.objects.create_user(username='testuser_get', email='get@example.com')
        retrieved_user = self.backend.get_user(user.pk)
        self.assertEqual(retrieved_user, user)

    def test_get_user_non_existent(self):
        """Test get_user for a non-existent user."""
        retrieved_user = self.backend.get_user(99999) # Non-existent PK
        self.assertIsNone(retrieved_user)

    # Additional tests needed once JWT verification is implemented:
    # - Test with expired token
    # - Test with token from wrong issuer/audience
    # - Test token signature verification failure
    # - Test successful creation of User and UserProfile with data from JWT claims (email, name, etc.)
    # - Test edge cases for username generation if not directly in token.

    def tearDown(self):
        # Clean up settings if overridden
        if hasattr(settings, 'CLERK_SECRET_KEY') and settings.CLERK_SECRET_KEY == 'test_clerk_secret_key':
            delattr(settings, 'CLERK_SECRET_KEY') # Be careful with delattr on settings
            # Or reset to original if you stored it, safer:
            # settings.CLERK_SECRET_KEY = self.original_clerk_secret_key

        # Clean up any created users/profiles if necessary, though Django's test runner handles this for TestCase
        pass
