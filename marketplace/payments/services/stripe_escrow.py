


import stripe
from django.conf import settings
from ..models import EscrowPayment

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeEscrowService:
    """Handles escrow payments using Stripe"""
    
    def create_payment_intent(self, amount, currency='ron'):
        """Create a new escrow payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                payment_method_types=['card'],
                capture_method='manual',
                metadata={'payment_type': 'escrow'}
            )
            return intent
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def create_escrow(self, listing, buyer, seller, amount):
        """Create new escrow transaction"""
        intent = self.create_payment_intent(amount)
        
        escrow = EscrowPayment.objects.create(
            listing=listing,
            buyer=buyer,
            seller=seller,
            amount=amount,
            payment_intent_id=intent.id,
            status='created'
        )
        return escrow
    
    def release_funds(self, escrow_id):
        """Release funds to seller"""
        escrow = EscrowPayment.objects.get(id=escrow_id)
        try:
            intent = stripe.PaymentIntent.capture(escrow.payment_intent_id)
            escrow.status = 'released'
            escrow.save()
            return True
        except stripe.error.StripeError:
            return False
    
    def refund_funds(self, escrow_id):
        """Refund funds to buyer"""
        escrow = EscrowPayment.objects.get(id=escrow_id)
        try:
            stripe.Refund.create(payment_intent=escrow.payment_intent_id)
            escrow.status = 'refunded'
            escrow.save()
            return True
        except stripe.error.StripeError:
            return False


