


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from .services.jumio_integration import JumioVerification

User = get_user_model()

@api_view(['POST'])
def start_verification(request):
    """Initiate ID verification process"""
    if not request.user.is_authenticated:
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    jumio = JumioVerification()
    redirect_url = jumio.initiate_verification(
        request.user,
        settings.JUMIO_CALLBACK_URL
    )
    
    if not redirect_url:
        return Response(
            {"error": "Failed to initiate verification"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    return Response({"redirect_url": redirect_url})

@api_view(['GET'])
def verification_status(request):
    """Check current verification status"""
    verification = getattr(request.user, 'identity_verification', None)
    if not verification:
        return Response({"status": "not_started"})
        
    return Response({
        "status": verification.status,
        "is_valid": verification.is_valid()
    })


