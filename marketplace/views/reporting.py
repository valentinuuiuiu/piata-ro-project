

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import ReportForm
from ..models import Listing

@login_required
def report_listing_view(request, listing_id):
    """View for reporting inappropriate listings"""
    listing = Listing.objects.get(id=listing_id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.listing = listing
            report.save()
            messages.success(request, 'Raportul a fost trimis cu succes')
            return redirect('listing_detail', listing_id=listing_id)
    else:
        form = ReportForm()
    
    return render(request, 'marketplace/report_listing.html', {
        'form': form,
        'listing': listing
    })

