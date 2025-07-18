from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

def clerk_login_required(view_func):
    """
    Decorator for views that checks that the user is logged in via django-allauth.
    Redirects to the login page if the user is not authenticated.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # User is authenticated, proceed with the view
            return view_func(request, *args, **kwargs)
        else:
            # User is not authenticated, redirect to login
            try:
                login_url = reverse('account_login')
            except:
                # Fallback if the named URL isn't available
                login_url = '/accounts/login/'

            # Add 'next' parameter to redirect back after login
            current_path = request.get_full_path()
            return redirect(f'{login_url}?next={current_path}')

    return _wrapped_view

def clerk_session_required(view_func):
    """
    Decorator to ensure a user has an active session.
    Uses django-allauth for authentication.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # We rely on Django's authentication system
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            # Redirect to login page
            try:
                login_url = reverse('account_login')
            except:
                login_url = '/accounts/login/'
                
            # Add 'next' parameter to redirect back after login
            current_path = request.get_full_path()
            return redirect(f'{login_url}?next={current_path}')


    return _wrapped_view
