

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from marketplace.models import Listing
from .services.stripe_escrow import StripeEscrowService
from .services.dispute_resolution import DisputeResolutionService
from .models import EscrowPayment

User = get_user_model()
escrow_service = StripeEscrowService()
dispute_service = DisputeResolutionService()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_escrow(request, listing_id):
    """Create new escrow payment"""
    try:
        listing = Listing.objects.get(pk=listing_id)
        seller = listing.user
        
        escrow = escrow_service.create_escrow(
            listing=listing,
            buyer=request.user,
            seller=seller,
            amount=listing.price
        )
        
        return Response({
            'escrow_id': escrow.id,
            'payment_intent': escrow.payment_intent_id,
            'amount': escrow.amount
        })
        
    except Listing.DoesNotExist:
        return Response(
            {'error': 'Listing not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def release_escrow(request, escrow_id):
    """Release escrow funds to seller"""
    try:
        success = escrow_service.release_funds(escrow_id)
        if success:
            return Response({'status': 'released'})
        return Response(
            {'error': 'Failed to release funds'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except EscrowPayment.DoesNotExist:
        return Response(
            {'error': 'Escrow not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_escrow(request, escrow_id):
    """Refund escrow funds to buyer"""
    try:
        success = escrow_service.refund_funds(escrow_id)
        if success:
            return Response({'status': 'refunded'})
        return Response(
            {'error': 'Failed to process refund'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except EscrowPayment.DoesNotExist:
        return Response(
            {'error': 'Escrow not found'},
            status=status.HTTP_404_NOT_FOUND
        )

