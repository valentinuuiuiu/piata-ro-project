# Clerk Authentication Integration for Piata.ro

This document outlines the integration of Clerk for user authentication in the Piata.ro Django project, replacing the previous Django AllAuth system.

## Overview

User authentication (signup, signin, session management, user profiles) is handled by [Clerk](https://clerk.com/). Django integrates with Clerk by:
1.  Redirecting users to Clerk's hosted UI or using ClerkJS components for authentication.
2.  Verifying JWTs issued by Clerk upon successful authentication.
3.  Creating and managing a local Django user record linked to the Clerk user via a `clerk_user_id`.
4.  Using a custom Django authentication backend (`ClerkAuthBackend`) to handle Clerk tokens.

## Setup

### Environment Variables

The following environment variables must be set in your `.env` file for Clerk authentication to function:

-   `CLERK_PUBLISHABLE_KEY`: Your Clerk instance's publishable key (for frontend).
-   `CLERK_SECRET_KEY`: Your Clerk instance's secret key (for backend).
-   `DJANGO_SECRET_KEY`: Django's own secret key (ensure this is set, renamed from `SECRET_KEY` in some contexts if needed, or ensure `.env` uses `SECRET_KEY` as expected by `settings.py`).

Additionally, during the setup process, it was found that these keys are necessary for running Django management commands (like migrations) due to how services are initialized:
-   `DEEPSEEK_API_KEY`: Required by the chat service. A temporary modification was made to `marketplace/services/chat_service.py` to allow running without it during development/migrations, but it should be set for full functionality.

### Django Settings

Clerk keys are configured in `piata_ro/settings.py`:
```python
CLERK_PUBLISHABLE_KEY = os.getenv('CLERK_PUBLISHABLE_KEY')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
```

The custom authentication backend is added to `AUTHENTICATION_BACKENDS`:
```python
AUTHENTICATION_BACKENDS = [
    'marketplace.clerk_auth_backend.ClerkAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

## Authentication Flow (High-Level)

1.  **Frontend Initiation:** The user initiates a sign-in or sign-up action. This is typically handled by:
    *   ClerkJS components (`<SignIn />`, `<SignUp />`, `<UserProfile />`) embedded in the Django templates/frontend framework.
    *   Redirects from Django views (e.g., `marketplace:clerk_login`, `marketplace:clerk_signup`) to Clerk's hosted pages.
2.  **Clerk Authentication:** Clerk handles the actual authentication process (credentials, social logins, MFA, etc.).
3.  **Callback to Django:** Upon successful authentication with Clerk:
    *   ClerkJS will typically provide a session token (JWT) to the frontend.
    *   The frontend can then make authenticated requests to the Django backend by including this token in the `Authorization: Bearer <token>` header.
    *   Alternatively, for flows involving redirects from Clerk's hosted pages, Clerk might redirect to a specific callback URL in the Django application (e.g., `/auth/clerk/callback/`). This callback view is responsible for obtaining the token.
4.  **Backend Token Verification:**
    *   The `ClerkAuthBackend` (specifically its `authenticate` method) is responsible for verifying the received Clerk JWT.
    *   **IMPORTANT:** The current implementation of JWT verification in `ClerkAuthBackend` is a **placeholder**. It needs to be fully implemented to fetch Clerk's JWKS, verify the token signature, and validate claims.
5.  **Django Session Management:**
    *   If token verification is successful, the `ClerkAuthBackend` retrieves an existing Django `User` linked by `UserProfile.clerk_user_id` or creates a new Django `User` and `UserProfile`.
    *   The `clerk_callback_view` (or any view handling the first authenticated request) then logs the user into the Django session using `django.contrib.auth.login`.
6.  **Authenticated Requests:** Subsequent requests from the authenticated user will have a valid Django session. For API requests, the Clerk token in the `Authorization` header can also be used for stateless authentication per request.
7.  **View Protection:** Django views are protected using the `@clerk_login_required` decorator, which checks `request.user.is_authenticated`.

## Key Components

-   **`marketplace.models.UserProfile.clerk_user_id`**: A field added to store the unique Clerk User ID and link it to the local Django user.
-   **`marketplace.clerk_auth_backend.ClerkAuthBackend`**: Custom Django authentication backend. Handles token verification (currently placeholder) and Django user retrieval/creation.
-   **`marketplace.views.auth`**:
    -   `clerk_login_redirect_view`: Redirects to Clerk sign-in.
    -   `clerk_signup_redirect_view`: Redirects to Clerk sign-up.
    -   `clerk_logout_view`: Logs out the Django user. Frontend handles Clerk session termination.
    -   `clerk_callback_view`: Placeholder for handling callbacks from Clerk, authenticating the user, and logging them into Django.
-   **`marketplace.decorators.clerk_login_required`**: Decorator to protect views, ensuring only authenticated users (via Clerk) can access them.
-   **URLs**: New URLs under `/auth/clerk/` in `marketplace.urls` map to the new authentication views.

## Frontend Integration Notes (High-Level)

-   The frontend (JavaScript) needs to be configured with the `CLERK_PUBLISHABLE_KEY`.
-   Use `@clerk/clerk-js` or a framework-specific Clerk library (e.g., `@clerk/clerk-react`) to:
    -   Render Clerk components (`<SignIn/>`, `<SignUp/>`, `<UserProfile/>`, `<UserButton/>`).
    -   Manage user sessions on the frontend.
    -   Retrieve the session token (`session.getToken()`).
-   When making authenticated API calls to the Django backend, include the Clerk token in the `Authorization` header: `Authorization: Bearer <JWT>`.
-   The Django `clerk_callback_view` expects to receive the token to establish the Django session, potentially from a cookie set by ClerkJS or passed explicitly by the frontend after Clerk authentication. The exact mechanism needs to be aligned with the frontend implementation.

## Important Considerations & TODOs

-   **[CRITICAL] Implement Full JWT Verification:** The JWT verification logic in `ClerkAuthBackend.authenticate()` is currently a placeholder. It **must** be updated to:
    -   Fetch Clerk's JSON Web Key Set (JWKS) from the URL provided in your Clerk Dashboard.
    -   Cache the JWKS appropriately.
    -   Verify the signature of incoming JWTs against these keys.
    -   Validate standard JWT claims (issuer, audience, expiration, etc.).
    -   Securely extract user information (Clerk User ID, email, names) from the verified token.
    -   The `clerk-sdk-python==0.1.0` is minimal. Consider using a dedicated JWT library like `python-jose` for robust verification if the SDK doesn't provide a clear mechanism for frontend token validation.
-   **User Creation Logic:** Fully implement user creation in `ClerkAuthBackend` based on verified claims from the JWT (e.g., email, first name, last name). Ensure usernames are handled correctly (e.g., derive from email or use Clerk user ID if unique usernames are required by Django).
-   **Clerk SDK Version:** The integration relies on `clerk-sdk-python==0.1.0`. Monitor for newer versions that might offer better support for backend JWT verification. The current version required downgrading `fastapi` and `pydantic`.
-   **Error Handling:** Enhance error handling in authentication views and backend.
-   **CSRF Protection:** Ensure CSRF protection is correctly handled, especially for the callback view if it processes POST requests or modifies state.
-   **Revert Temporary Fixes:** The temporary modification in `marketplace/services/chat_service.py` (regarding `DEEPSEEK_API_KEY`) should be reverted or properly handled for production environments.
-   **Thorough Testing:** Conduct thorough testing of all authentication flows, including edge cases and error conditions, once the JWT verification is fully implemented.
```
