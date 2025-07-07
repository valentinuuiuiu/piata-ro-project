import jwt
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings

from jose import jwt as jose_jwt
from jose.exceptions import JWTError
import requests

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
            # Initialize JWKS client
            jwks_url = f"https://{settings.CLERK_PUBLISHABLE_KEY}.clerk.accounts.dev/.well-known/jwks.json"
            jwks_client = jose_jwt.PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Verify JWT using python-jose
            claims = jose_jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.CLERK_PUBLISHABLE_KEY,
                issuer=f"https://{settings.CLERK_PUBLISHABLE_KEY}.clerk.accounts.dev"
            )

            clerk_user_id = claims.get('sub')
            email = claims.get('email')

            if not clerk_user_id:
                return None

            try:
                user_profile = UserProfile.objects.get(clerk_user_id=clerk_user_id)
                return user_profile.user
            except UserProfile.DoesNotExist:
                if not email:
                    return None
                
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=claims.get('given_name', ''),
                    last_name=claims.get('family_name', '')
                )
                UserProfile.objects.create(user=user, clerk_user_id=clerk_user_id)
                return user

        except JWTError as e:
            print(f"JWT Verification Error: {e}")
            return None
        except Exception as e:
            print(f"Clerk Auth Backend Error: {e}")
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
