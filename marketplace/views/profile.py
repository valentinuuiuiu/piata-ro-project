

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import ProfileForm

@login_required
def profile_view(request):
    """User profile dashboard"""
    return render(request, 'marketplace/profile.html', {
        'user': request.user
    })

@login_required
def profile_edit_view(request):
    """Edit profile information"""
    from .forms import UserUpdateForm, ProfileForm
    
    try:
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileForm(request.POST, instance=profile)
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profilul a fost actualizat cu succes!')
                return redirect('marketplace:profile')
        else:
            user_form = UserUpdateForm(instance=request.user)
            profile_form = ProfileForm(instance=profile)
        
        return render(request, 'marketplace/profile_edit.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })
    except Exception as e:
        messages.error(request, f'A apărut o eroare: {str(e)}')
        return redirect('marketplace:profile')


def public_profile_view(request, username):
    """View for public user profiles"""
    from django.shortcuts import get_object_or_404
    from ..models import User, Listing
    
    user = get_object_or_404(User, username=username)
    listings = Listing.objects.filter(
        user=user,
        status='active'
    ).order_by('-created_at')[:20]
    
    return render(request, 'marketplace/public_profile.html', {
        'profile_user': user,
        'listings': listings
    })



