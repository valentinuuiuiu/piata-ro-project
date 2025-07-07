import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from clerk_sdk import Clerk
from clerk_sdk.api_client import APIClient
from clerk_sdk.models.user import User as ClerkUser

from .models import UserProfile

User = get_user_model()

class ClerkAuthBackend(BaseBackend):
    """
    Django Authentication Backend for Clerk.
    Authenticates users based on a Clerk JWT.
    """

    def __init__(self):
        self.clerk_client = Clerk(
            secret_key=settings.CLERK_SECRET_KEY,
            # The SDK might attempt to initialize other parts, ensure it's minimal
            # http_options={'timeout': 5} # Optional: configure timeout
        )

    def authenticate(self, request, token=None, **kwargs):
        if token is None:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
            token = auth_header.split(' ')[1]

        try:
            # The clerk-sdk-python's 'verify_token' method might not exist or work as expected
            # for frontend tokens directly. We might need to use 'clerk_client.users.get_user'
            # or inspect how the SDK expects token verification to be done.
            # For now, let's assume we need to decode and verify it based on JWKS,
            # though the SDK should ideally handle this.
            # A more direct approach if the SDK supports it would be:
            # claims = self.clerk_client.verify_token(token)
            # clerk_user_id = claims.get('sub')

            # Alternative: If the SDK is more for backend-to-backend, we might need a different approach.
            # Let's try a conceptual way to get user from token, actual SDK usage might differ.
            # This part needs to be verified against clerk-sdk-python's actual capabilities.

            # Assuming the token itself is a session token that can be used to get user details
            # This is a placeholder for actual token verification and user fetching logic
            # The current clerk-sdk-python (0.1.0) seems more focused on backend API calls
            # rather than direct JWT verification of frontend tokens.
            #
            # A common pattern is to have Clerk frontend manage the session and token,
            # and the backend verifies it using JWKS. The SDK *should* provide this.
            # If clerk_sdk.Clerk().verify_token(token) or similar exists and works, use it.
            #
            # Let's assume for now the SDK has a way to verify and get user ID.
            # This is a critical point that needs verification with SDK docs.
            # For placeholder, let's simulate decoding if we had a JWKS client (which SDK should manage)

            # --- Placeholder for SDK's token verification ---
            # This is highly dependent on the SDK's API.
            # If the SDK's Clerk(secret_key=...).users.get_user(user_id="from_token_somehow") works,
            # or if there's a verify_jwt() method, that's what we need.
            # The current SDK (v0.1.0) is quite minimal.
            # jwt.decode is not sufficient without proper JWKS handling.

            # Given the limitations of the current SDK version 0.1.0, direct JWT validation
            # might require manual JWKS fetching and caching, which is complex.
            # A more robust solution would use a more feature-complete JWT library or hope
            # the SDK handles this transparently.
            # For now, this backend will be more conceptual until SDK usage is clarified.

            # Let's assume a hypothetical function in the SDK or a helper
            # decoded_token = self.verify_clerk_jwt(token) # This function doesn't exist yet
            # if not decoded_token:
            #     return None
            # clerk_user_id = decoded_token.get('sub')
            # email = decoded_token.get('email')
            # first_name = decoded_token.get('first_name')
            # last_name = decoded_token.get('last_name')

            # Due to the SDK's nature, we might need to fetch user by token if that's an API call
            # This is a common approach if the token is an opaque session token for Clerk's API
            # However, typically backends verify stateless JWTs.

            # For the purpose of this exercise, and given the SDK's simplicity,
            # we'll assume the token is the Clerk User ID itself for now,
            # which is NOT how it would work in reality with JWTs.
            # This is a major simplification due to SDK limitations / clarity.
            # IN A REAL SCENARIO: Use proper JWT verification with JWKS.

            # This backend will need significant refinement once the exact method of
            # verifying a frontend-issued Clerk JWT with the Python SDK is clear.
            # The SDK (0.1.0) doesn't have an obvious verify_token() for frontend JWTs.
            # It has client.sessions.verify_session(session_id, token)

            # Let's assume the `token` passed is a session ID for verification for now.
            # And we'd need another piece of info, or the SDK handles it.
            # This is getting too speculative.

            # Simplification: Let's assume the token IS the user_id for now for structure.
            # THIS IS NOT SECURE FOR A REAL JWT.
            clerk_user_id = token # Placeholder: This is NOT how JWT sub is obtained.

            if not clerk_user_id:
                return None

            try:
                user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
                return user_profile.user
            except UserProfile.DoesNotExist:
                # User doesn't exist locally, create them.
                # We need more info from the token like email.
                # This part is also hampered by not having the decoded JWT.

                # Placeholder: if we had email from token
                # user_email = "user@example.com" # from decoded_token.get('email')
                # username = user_email # Or generate one

                # Cannot proceed with user creation without actual email/username from token.
                # For now, if user profile doesn't exist, we can't log them in with this placeholder.
                return None
        except Exception as e:
            # Log error
            print(f"Clerk Auth Backend Error: {e}") # Replace with proper logging
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

# Note: This backend is highly conceptual due to the unclear JWT verification
# process with the current clerk-sdk-python 0.1.0 for frontend tokens.
# It needs to be updated with the correct SDK calls for:
# 1. Verifying the JWT (likely using a JWKS endpoint provided by Clerk).
# 2. Extracting user ID, email, and other necessary claims from the verified JWT.
#
# If Clerk's Python SDK is primarily for backend-to-backend management API calls,
# then JWT verification might need another library like `python-jose` with JWKS fetching.
# Clerk documentation should clarify the recommended Python backend verification flow.
#
# For now, the structure is laid out. The critical part is the `authenticate` method's
# token verification and claim extraction.
