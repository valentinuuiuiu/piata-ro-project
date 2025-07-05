

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import EscrowPayment
from .services.dispute_resolution import DisputeResolutionService

dispute_service = DisputeResolutionService()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def open_dispute(request, escrow_id):
    """Open a dispute for escrow transaction"""
    try:
        escrow = EscrowPayment.objects.get(id=escrow_id, buyer=request.user)
        dispute = dispute_service.open_dispute(
            escrow_id=escrow_id,
            reason=request.data.get('reason'),
            description=request.data.get('description'),
            evidence=request.FILES.get('evidence')
        )
        return Response({'status': 'disputed'})
    except EscrowPayment.DoesNotExist:
        return Response(
            {'error': 'Escrow not found or not owned by user'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_dispute(request, escrow_id):
    """Resolve a dispute (admin only)"""
    if not request.user.is_staff:
        return Response(
            {'error': 'Only admins can resolve disputes'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        dispute = dispute_service.resolve_dispute(
            escrow_id=escrow_id,
            resolution=request.data.get('resolution'),
            refund_buyer=request.data.get('refund_buyer', False)
        )
        return Response({'status': 'resolved'})
    except EscrowPayment.DoesNotExist:
        return Response(
            {'error': 'Escrow not found'},
            status=status.HTTP_404_NOT_FOUND
        )

