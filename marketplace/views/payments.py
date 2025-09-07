from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
from ..forms import PromoteListingForm
from ..models import (
    Listing,
    UserProfile,
    CreditTransaction,
    ListingBoost,
    CreditPackage,
    Payment
)
from datetime import timedelta
import json
import logging
from django.db import transaction
from django.utils import timezone

# Optional Stripe import
try:
    import stripe
    stripe_available = True
except ImportError:
    stripe = None
    stripe_available = False

logger = logging.getLogger(__name__)

# Stripe integration (optional)
try:
    import stripe
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
except ImportError:
    stripe = None

@login_required
def credits_dashboard(request):
    """Credits dashboard showing balance and purchase options"""
    user_profile = request.user.profile
    credit_packages = CreditPackage.objects.filter(is_active=True).order_by('base_credits')
    recent_transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]

    context = {
        'user_profile': user_profile,
        'credit_packages': credit_packages,
        'recent_transactions': recent_transactions,
        'promotion_cost': Decimal('0.50'),  # Cost to promote a listing
    }
    return render(request, 'marketplace/credits_cart.html', context)

@login_required
def payment_success(request):
    """Handle successful payment and add credits to user"""
    session_id = request.GET.get('session_id')

    if session_id:
        try:
            if stripe:
                stripe.api_key = settings.STRIPE_SECRET_KEY

                # Retrieve the checkout session
                session = stripe.checkout.Session.retrieve(session_id)

                if session.payment_status == 'paid':
                    # Get metadata from session
                    user_id = session.metadata.get('user_id')
                    total_credits = int(session.metadata.get('total_credits', 0))
                    cart_data = json.loads(session.metadata.get('cart_data', '[]'))
                    currency = session.metadata.get('currency', 'ron')

                    # Verify user
                    if str(request.user.id) != user_id:
                        messages.error(request, "Sesiunea de plată nu corespunde cu utilizatorul curent.")
                        return redirect('marketplace:buy_credits')

                    # Add credits to user profile
                    user_profile = request.user.profile
                    user_profile.credits_balance += Decimal(str(total_credits))
                    user_profile.save()

                    # Create transaction records for each item in cart
                    for item in cart_data:
                        credits = item['credits']
                        quantity = item['quantity']
                        price = item['priceEur'] if currency == 'eur' else item['priceRon']

                        for i in range(quantity):
                            CreditTransaction.objects.create(
                                user=request.user,
                                transaction_type='purchase',
                                amount=credits,
                                description=f"Achiziție {credits} credite ({price} {currency.upper()})",
                                reference=session_id
                            )

                    messages.success(request, f"🎉 Felicitări! Ai primit {total_credits} credite în cont. Plata a fost procesată cu succes!")
                    return render(request, 'marketplace/payment_success.html', {
                        'total_credits': total_credits,
                        'session_id': session_id,
                        'cart_data': cart_data,
                        'currency': currency.upper()
                    })

        except Exception as e:
            messages.error(request, f"A apărut o eroare la procesarea plății: {str(e)}")
            logger.error(f"Payment success error: {e}")

    messages.error(request, "Sesiunea de plată nu a fost găsită sau este invalidă.")
    return redirect('marketplace:buy_credits')

@login_required
def credits_history(request):
    """View credit transaction history"""
    transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'transactions': transactions,
        'user_profile': request.user.profile
    }
    return render(request, 'marketplace/credits_history.html', context)

@login_required
def process_payment_view(request):
    """Process Stripe payment for credits from shopping cart."""
    if request.method == 'POST':
        try:
            # Get cart data from the form
            cart_data = json.loads(request.POST.get('cart_data', '[]'))
            currency = request.POST.get('currency', 'ron')

            if not cart_data:
                messages.error(request, 'Coșul este gol.')
                return redirect('marketplace:buy_credits')

            if not stripe:
                messages.error(request, 'Sistemul de plată nu este configurat.')
                return redirect('marketplace:buy_credits')

            # Calculate totals and prepare line items
            line_items = []
            total_credits = 0

            for item in cart_data:
                credits = item['credits']
                quantity = item['quantity']
                price = item['priceEur'] if currency == 'eur' else item['priceRon']

                total_credits += credits * quantity

                line_items.append({
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f'{credits} Credite Piata.ro',
                            'description': f'Pachet cu {credits} credite pentru promovarea anunțurilor',
                        },
                        'unit_amount': int(price * 100),  # Convert to cents
                    },
                    'quantity': quantity,
                })

            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('marketplace:payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('marketplace:home')),
                metadata={
                    'user_id': str(request.user.id),
                    'total_credits': str(total_credits),
                    'cart_data': json.dumps(cart_data),
                    'currency': currency,
                }
            )

            return redirect(checkout_session.url)

        except Exception as e:
            messages.error(request, f'Eroare la procesarea plății: {str(e)}')
            logger.error(f"Payment processing error: {e}")
            return redirect('marketplace:home')

    return redirect('marketplace:home')

@login_required
def promote_listing_view(request, listing_id):
    """Promote a listing to first page with atomic transaction handling."""
    try:
        listing = Listing.objects.get(id=listing_id, user=request.user)
    except Listing.DoesNotExist:
        messages.error(request, 'Anunțul nu a fost găsit sau nu îți aparține.')
        return redirect('marketplace:profile')

    # Check if listing is already featured
    if listing.is_featured:
        messages.info(request, 'Acest anunț este deja promovat.')
        return redirect('marketplace:listing_detail', listing_id=listing.id)

    # Determine the target category
    target_category = listing.category
    category_name = target_category.name

    if request.method == 'POST':
        form = PromoteListingForm(request.POST)

        if form.is_valid():
            duration_days = int(form.cleaned_data['duration_days'])
            credits_needed = Decimal(str(duration_days * 0.5))
            auto_repost_interval = request.POST.get('auto_repost_interval', 'none')

            user_profile = request.user.profile

            # Check if user has enough credits
            if user_profile.credits_balance < credits_needed:
                messages.error(request, f'Nu ai suficiente credite. Ai nevoie de {credits_needed} credite pentru promovare.')
                return redirect('marketplace:credits_dashboard')

            # Use atomic transaction to ensure data consistency
            try:
                with transaction.atomic():
                    # Lock user profile to prevent race conditions
                    user_profile = UserProfile.objects.select_for_update().get(user=request.user)

                    # Double-check credits after locking
                    if user_profile.credits_balance < credits_needed:
                        messages.error(request, 'Nu ai suficiente credite. Încearcă din nou.')
                        return redirect('marketplace:credits_dashboard')

                    # Deduct credits safely
                    user_profile.deduct_credits(credits_needed)

                    # Calculate expiration time
                    expires_at = timezone.now() + timedelta(days=duration_days)

                    # Create ListingBoost record
                    boost = ListingBoost.objects.create(
                        listing=listing,
                        boost_type='featured',
                        credits_cost=int(credits_needed * 2),  # Store as integer
                        duration_days=duration_days,
                        starts_at=timezone.now(),
                        expires_at=expires_at,
                        is_active=True
                    )

                    # Mark listing as featured
                    listing.is_featured = True
                    listing.save()

                    # Create transaction record
                    CreditTransaction.objects.create(
                        user=request.user,
                        transaction_type='spent',
                        amount=credits_needed,
                        description=f"Promovare {duration_days} zile în categoria '{category_name}': {listing.title}",
                        listing=listing
                    )

                    # Handle auto-repost if selected
                    if auto_repost_interval != 'none':
                        try:
                            from ..tasks import auto_repost_listing
                            from celery.task.control import add_periodic_task

                            # Convert minutes to seconds for Celery
                            interval_seconds = int(auto_repost_interval) * 60

                            # Schedule the periodic task
                            add_periodic_task(
                                interval_seconds,
                                auto_repost_listing.s(listing.id, auto_repost_interval),
                                name=f'auto-repost-{listing.id}'
                            )

                            # Update boost record with auto-repost flag
                            boost.auto_repost = True
                            boost.save(update_fields=['auto_repost'])

                            messages.success(request, f'Repromovarea automată a fost activată - anunțul va fi repostat la fiecare {auto_repost_interval} minute.')
                        except ImportError:
                            messages.warning(request, 'Sistemul de repromovare nu este disponibil.')

                    messages.success(
                        request,
                        f'Anunțul "{listing.title}" a fost promovat pentru {duration_days} zile! '
                        f'Acum apare primul în categoria "{category_name}" până pe {expires_at.strftime("%d.%m.%Y")}.'
                    )

                    return redirect('marketplace:listing_detail', listing_id=listing.id)

            except Exception as e:
                messages.error(request, 'A apărut o eroare la procesarea promovării. Te rugăm să încerci din nou.')
                logger.error(f"Promote listing error for user {request.user.id}, listing {listing_id}: {str(e)}")
                return redirect('marketplace:promote_listing', listing_id=listing_id)
        else:
            messages.error(request, 'Formularul conține erori. Te rugăm să verifici datele introduse.')
    else:
        # GET request - show form
        form = PromoteListingForm(initial={'listing_id': listing_id})

    context = {
        'form': form,
        'listing': listing,
        'target_category': category_name,
        'promotion_cost': Decimal('0.5'),
        'user_credits': request.user.profile.credits_balance,
        'existing_boosts': listing.boosts.filter(is_active=True)
    }

    return render(request, 'marketplace/promote_listing.html', context)

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    if not stripe:
        return JsonResponse({'error': 'Stripe not configured'}, status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the checkout.session.completed event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        payment_intent_id = session.get('payment_intent')

        if not payment_intent_id:
            return JsonResponse({'error': 'Payment Intent ID missing'}, status=400)

        try:
            # Retrieve the pending Payment record
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)

            if payment.status == 'succeeded':
                return JsonResponse({'status': 'already processed'}, status=200)

            if payment.status == 'pending' and session.payment_status == 'paid':
                # Fulfill the purchase
                user = payment.user
                user_profile = user.profile

                metadata = session.get('metadata', {})
                total_credits = int(metadata.get('total_credits', '0'))
                cart_data = json.loads(metadata.get('cart_data', '[]'))

                # Add credits to user profile
                user_profile.credits_balance += Decimal(str(total_credits))
                user_profile.save()

                # Create transaction records
                for item in cart_data:
                    credits = int(item.get('credits', 0))
                    quantity = int(item.get('quantity', 0))
                    price = item.get('priceEur') if payment.currency.upper() == 'EUR' else item.get('priceRon')

                    for _ in range(quantity):
                        CreditTransaction.objects.create(
                            user=user,
                            transaction_type='purchase',
                            amount=credits,
                            description=f"Achiziție {credits} credite ({price} {payment.currency.upper()}) via webhook",
                            payment_intent_id=payment_intent_id
                        )

                # Update Payment status
                payment.status = 'succeeded'
                payment.save()

                return JsonResponse({'status': 'success'}, status=200)
            else:
                payment.status = 'failed'
                payment.save()
                return JsonResponse({'status': 'payment not successful'}, status=200)

        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for intent {payment_intent_id}")
            return JsonResponse({'error': 'Payment record not found'}, status=404)
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return JsonResponse({'error': 'Processing error'}, status=500)

    return JsonResponse({'status': 'unhandled event type'}, status=200)
