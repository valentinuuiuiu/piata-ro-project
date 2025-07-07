from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

def clerk_login_required(view_func):
    """
    Decorator for views that checks that the user is logged in via Clerk.
    Redirects to the Clerk sign-in page if the user is not authenticated.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # User is authenticated, proceed with the view
            return view_func(request, *args, **kwargs)
        else:
            # User is not authenticated.
            # Redirect to Clerk sign-in.
            # This assumes CLERK_SIGN_IN_URL is defined in settings or can be reversed.
            # For a more robust solution, this might involve constructing the URL
            # with a redirect_url_complete parameter if Clerk supports it.

            # Option 1: Use a named URL route if we create one for the redirect view
            try:
                login_url = reverse('marketplace:clerk_login')
            except:
                # Fallback if the named URL isn't available or configured yet
                # This should point to where ClerkJS is initialized or Clerk's hosted UI.
                # This is a placeholder and should be configured properly.
                login_url = getattr(settings, 'CLERK_SIGN_IN_REDIRECT_URL', '/auth/clerk/login/') # Default fallback

            # You might want to add a 'next' parameter to redirect back after login
            # current_path = request.build_absolute_uri()
            # return redirect(f'{login_url}?next={current_path}')
            return redirect(login_url)

    return _wrapped_view

def clerk_session_required(view_func):
    """
    Decorator to ensure a user has an active Clerk session.
    This is a more specific version that might eventually involve directly
    interacting with Clerk's session verification if different from Django's auth.
    For now, it can behave similarly to clerk_login_required.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # This is a placeholder. Actual Clerk session verification might involve:
        # 1. Getting a token (__session cookie or Authorization header).
        # 2. Verifying it using the Clerk SDK (if it provides such a method for frontend tokens)
        #    or a direct call to Clerk's /userinfo or /verify endpoints.
        # 3. If verified, proceed. If not, redirect to login.

        # For now, we rely on Django's authentication system, assuming our
        # ClerkAuthBackend correctly populates request.user upon successful
        # token verification during the callback or subsequent requests.
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to Clerk sign-in page
            # Similar to clerk_login_required, this URL should be robustly determined.
            try:
                login_url = reverse('marketplace:clerk_login')
            except:
                login_url = getattr(settings, 'CLERK_SIGN_IN_REDIRECT_URL', '/auth/clerk/login/')

            return redirect(login_url)

    return _wrapped_view
