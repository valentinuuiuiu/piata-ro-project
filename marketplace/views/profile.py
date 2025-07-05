

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
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'marketplace/profile_edit.html', {
        'form': form
    })


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



