from django.contrib.auth import login as django_login, logout as django_logout
from django.shortcuts import redirect, render
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect
# Import the User model and UserProfile, and potentially the ClerkAuthBackend if direct interaction is needed here
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

# It's generally better if CLERK_FRONTEND_API_URL is defined in settings if it's constant
# For dynamic parts like redirect URLs, they should be constructed carefully.
# CLERK_SIGN_IN_URL = f"{settings.CLERK_FRONTEND_API_URL}/sign-in" # Example
# CLERK_SIGN_UP_URL = f"{settings.CLERK_FRONTEND_API_URL}/sign-up" # Example
# These might not be needed if ClerkJS handles the UI entirely.

def clerk_login_redirect_view(request):
    """
    Redirects to Clerk's hosted sign-in page or the page where ClerkJS is initialized.
    This view might not be strictly necessary if your frontend directly links to Clerk sign-in.
    """
    # This URL should be your Clerk Frontend API URL's sign-in path,
    # or simply the path in your app that hosts the Clerk <SignIn /> component.
    # For Clerk hosted pages:
    # login_url = f"https://{settings.CLERK_FRONTEND_API_URL}/sign-in" # This is an example, get from Clerk Dashboard
    # A common pattern is to redirect to a page in your app that has the Clerk <SignIn/> component
    # e.g., return redirect(reverse('my_app_login_page_with_clerk_component'))
    # For now, let's assume there's a setting for the sign-in URL.
    if hasattr(settings, 'CLERK_SIGN_IN_REDIRECT_URL'):
        return redirect(settings.CLERK_SIGN_IN_REDIRECT_URL)
    # Fallback or error if not configured
    return HttpResponseBadRequest("Clerk sign-in URL not configured.")

def clerk_signup_redirect_view(request):
    """
    Redirects to Clerk's hosted sign-up page or the page where ClerkJS is initialized.
    """
    if hasattr(settings, 'CLERK_SIGN_UP_REDIRECT_URL'):
        return redirect(settings.CLERK_SIGN_UP_REDIRECT_URL)
    return HttpResponseBadRequest("Clerk sign-up URL not configured.")


def clerk_logout_view(request):
    """
    Logs the user out of the Django session.
    The actual Clerk session logout is typically handled by ClerkJS on the frontend.
    This view ensures the Django session is cleared.
    """
    django_logout(request)
    # Redirect to a page that tells the user they've been logged out,
    # or to the Clerk-defined post_logout_redirect_url if applicable.
    # For ClerkJS, it handles its own session termination.
    # This backend logout ensures Django's session is also terminated.
    return redirect(getattr(settings, 'LOGOUT_REDIRECT_URL', '/'))


def clerk_callback_view(request):
    """
    Handles the callback from Clerk after successful authentication.
    This view will receive a token from Clerk (typically via ClerkJS setting a cookie
    or providing it to the frontend, which then sends it to this backend endpoint).
    
    The exact mechanism depends on how Clerk is configured (e.g., if using ClerkJS
    with `navigate` for SPA or backend-driven flow with redirects).

    This view needs to:
    1. Get the token (e.g., from request body, headers, or a cookie ClerkJS might set if configured for backend).
    2. Use the ClerkAuthBackend to authenticate this token.
    3. If authentication is successful, log the user into the Django session.
    4. Redirect to the appropriate page (e.g., dashboard or original destination).
    """
    # How the token is passed to this callback is crucial.
    # If ClerkJS handles sign-in and then navigates, the frontend might make an API call
    # to this backend with the token in the Authorization header.
    # If Clerk redirects here directly from its hosted pages, the token mechanism needs checking.
    # For now, let's assume the token is passed in a way that our backend can access it.

    # This is a placeholder. The real token would come from the request,
    # e.g., request.COOKIES.get('__session') or request.headers.get('Authorization').split(' ')[1]
    clerk_token = request.COOKIES.get('__session') # Example: if Clerk sets a __session cookie

    if not clerk_token:
        # Or, if expecting it in Authorization header for an API-style callback
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            clerk_token = auth_header.split(' ')[1]
        else: # Handle other ways token might be passed or error
            return HttpResponseBadRequest("Clerk token not found in request.")

    # Authenticate using the backend
    # The backend's authenticate method needs to be robust.
    user = authenticate(request, token=clerk_token)

    if user:
        django_login(request, user)
        # Redirect to LOGIN_REDIRECT_URL or a more specific destination
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        # Authentication failed
        # Render an error page or redirect to login with an error message
        # For security, don't give too much detail about why it failed.
        return render(request, 'marketplace/auth_error.html', {'error_message': 'Authentication failed.'})

# A simple template for auth errors, create this file if it doesn't exist:
# marketplace/templates/marketplace/auth_error.html
# <!DOCTYPE html>
# <html>
# <head><title>Authentication Error</title></head>
# <body>
#   <h1>Authentication Error</h1>
#   <p>{{ error_message }}</p>
#   <p><a href="/">Go to homepage</a></p>
# </body>
# </html>


def register_view(request):
    from django.shortcuts import render
    return render(request, 'registration/register.html')
