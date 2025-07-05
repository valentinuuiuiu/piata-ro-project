
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from ..forms import ListingForm

@login_required
def add_listing_view(request):
    """View for creating new listings"""
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.save()
            return redirect('listing_detail', slug=listing.slug)
    else:
        form = ListingForm()
    
    return render(request, 'marketplace/add_listing.html', {'form': form})
