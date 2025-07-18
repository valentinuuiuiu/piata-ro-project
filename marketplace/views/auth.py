from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import pyotp

from ..models import UserProfile

def login_view(request):
    """
    Custom login view that handles both standard login and redirects to MFA if needed
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if MFA is enabled for this user
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.mfa_enabled and profile.mfa_secret:
                    # Store user ID in session for MFA verification
                    request.session['mfa_user_id'] = user.id
                    return redirect('marketplace:verify_mfa')
                else:
                    # No MFA, proceed with login
                    login(request, user)
                    return redirect('marketplace:home')
            except UserProfile.DoesNotExist:
                # No profile, proceed with login
                login(request, user)
                return redirect('marketplace:home')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'registration/login.html')

def verify_mfa(request):
    """
    Verify MFA token for users with MFA enabled
    """
    user_id = request.session.get('mfa_user_id')
    
    if not user_id:
        return redirect('marketplace:login')
    
    if request.method == 'POST':
        token = request.POST.get('token')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user)
            
            # Verify token
            totp = pyotp.TOTP(profile.mfa_secret)
            if totp.verify(token):
                # Token is valid, log in the user
                login(request, user)
                # Clean up session
                del request.session['mfa_user_id']
                return redirect('marketplace:home')
            else:
                messages.error(request, 'Invalid MFA token')
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            messages.error(request, 'User not found')
            return redirect('marketplace:login')
    
    return render(request, 'mfa_verify.html')