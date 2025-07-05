from django.contrib.auth import authenticate, login
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render, redirect
from django.conf import settings
from ..auth import PasswordValidator, MFAService
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

@ratelimit(key='ip', rate='5/m', block=True)
def register_view(request):
    """User registration view with rate limiting"""
    from django.contrib.auth.forms import UserCreationForm
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                PasswordValidator.validate(form.cleaned_data['password1'])
                user = form.save()
                login(request, user)
                return redirect('marketplace:home')  # Changed to use marketplace namespace
            except ValidationError as e:
                form.add_error('password1', e)
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            PasswordValidator.validate(password)
        except ValidationError as e:
            return render(request, 'registration/login.html', {'error': str(e)})

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.profile.mfa_enabled:
                request.session['mfa_user'] = user.id
                mfa_service = MFAService(user.profile)
                return render(request, 'mfa_verify.html')
                
            login(request, user)
            return redirect('marketplace:home')  # Changed to use marketplace namespace
            
    return render(request, 'registration/login.html')

def verify_mfa(request):
    if 'mfa_user' not in request.session:
        return redirect('login')
        
    if request.method == 'POST':
        user = User.objects.get(id=request.session['mfa_user'])
        mfa_service = MFAService(user.profile)
        
        if mfa_service.verify_otp(request.POST.get('token')):
            login(request, user)
            return redirect('dashboard')
            
    return render(request, 'mfa_verify.html')
