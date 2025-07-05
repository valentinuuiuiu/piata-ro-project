


from django.core.mail import send_mail
from django.conf import settings
from ..models import EscrowPayment

class DisputeResolutionService:
    """Handles escrow dispute resolution workflow"""
    
    def open_dispute(self, escrow_id, reason, description, evidence=None):
        """Initiate a new dispute"""
        escrow = EscrowPayment.objects.get(id=escrow_id)
        escrow.status = 'disputed'
        escrow.dispute_reason = reason
        escrow.dispute_description = description
        if evidence:
            escrow.dispute_evidence = evidence
        escrow.save()
        
        # Notify admin and counterparty
        self._send_dispute_notifications(escrow)
        return escrow
        
    def resolve_dispute(self, escrow_id, resolution, refund_buyer=False):
        """Resolve an existing dispute"""
        escrow = EscrowPayment.objects.get(id=escrow_id)
        escrow.status = 'resolved'
        escrow.dispute_resolution = resolution
        escrow.save()
        
        if refund_buyer:
            # Trigger refund through Stripe service
            from .stripe_escrow import StripeEscrowService
            StripeEscrowService().refund_funds(escrow_id)
        else:
            # Release funds to seller
            from .stripe_escrow import StripeEscrowService
            StripeEscrowService().release_funds(escrow_id)
            
        self._send_resolution_notifications(escrow)
        return escrow
        
    def _send_dispute_notifications(self, escrow):
        """Send email notifications about new dispute"""
        send_mail(
            subject=f'Dispute Opened: Escrow #{escrow.id}',
            message=f'A dispute has been opened for escrow transaction #{escrow.id}.\n\n'
                   f'Reason: {escrow.get_dispute_reason_display()}\n'
                   f'Description: {escrow.dispute_description}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[
                settings.ADMIN_EMAIL,
                escrow.buyer.email,
                escrow.seller.email
            ]
        )
        
    def _send_resolution_notifications(self, escrow):
        """Send email notifications about dispute resolution"""
        send_mail(
            subject=f'Dispute Resolved: Escrow #{escrow.id}',
            message=f'The dispute for escrow transaction #{escrow.id} has been resolved.\n\n'
                   f'Resolution: {escrow.dispute_resolution}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[
                settings.ADMIN_EMAIL,
                escrow.buyer.email,
                escrow.seller.email
            ]
        )


