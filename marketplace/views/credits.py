

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from ..models import CreditPackage, CreditTransaction

@login_required
def credits_dashboard(request):
    """View for credit purchase dashboard"""
    packages = CreditPackage.objects.filter(is_active=True)
    transactions = CreditTransaction.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    return render(request, 'marketplace/credits_dashboard.html', {
        'packages': packages,
        'transactions': transactions,
        'balance': request.user.profile.credits_balance
    })

@login_required
def purchase_credits(request, package_id):
    """View for handling credit purchases"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from ..models import CreditPackage
    
    package = get_object_or_404(CreditPackage, id=package_id)
    # Actual purchase logic would be handled by Stripe webhook
    return redirect('buy_credits')



@login_required
def process_payment_view(request):
    """View for processing credit payments"""
    from django.shortcuts import render, redirect
    from django.conf import settings
    import stripe
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    if request.method == 'POST':
        try:
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': request.POST.get('stripe_price_id'),
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/credite/succes/'),
                cancel_url=request.build_absolute_uri('/credite/'),
                metadata={
                    'user_id': request.user.id,
                    'package_id': request.POST.get('package_id')
                }
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return render(request, 'marketplace/payment_error.html', {
                'error': str(e)
            })
    
    return redirect('buy_credits')






@login_required
def payment_success(request):
    """View for successful payment confirmation"""
    from django.shortcuts import render
    from django.contrib import messages
    
    messages.success(request, "Payment completed successfully! Credits have been added to your account.")
    return render(request, 'marketplace/payment_success.html', {
        'balance': request.user.profile.credits_balance
    })





@login_required
def promote_listing_view(request, listing_id):
    """View for promoting listings using credits"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from decimal import Decimal
    from ..models import Listing
    
    listing = get_object_or_404(Listing, id=listing_id)
    
    if not request.user.profile.can_promote_listing():
        messages.error(request, "You don't have enough credits to promote this listing")
        return redirect('listing_detail', listing_id=listing_id)
    
    # Deduct credits and promote listing
    if request.user.profile.deduct_credits(Decimal('0.5')):
        listing.is_featured = True
        listing.save()
        messages.success(request, "Listing promoted successfully!")
    else:
        messages.error(request, "Failed to promote listing")
    
    return redirect('listing_detail', listing_id=listing_id)

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    from django.http import HttpResponse
    import stripe
    import json
    from ..models import CreditTransaction, UserProfile
    
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        package_id = session['metadata']['package_id']
        
        # Process payment and add credits
        profile = UserProfile.objects.get(user_id=user_id)
        package = CreditPackage.objects.get(id=package_id)
        profile.add_credits(package.credit_amount)
        
        CreditTransaction.objects.create(
            user=profile.user,
            amount=package.credit_amount,
            transaction_type='purchase'
        )
    
    return HttpResponse(status=200)



