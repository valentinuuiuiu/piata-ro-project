from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django_ratelimit.decorators import ratelimit
import re
import pyotp
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class PasswordValidator:
    """Enhanced password validation"""
    @staticmethod
    def validate(password, user=None):
        if len(password) < 12:
            raise ValidationError("Password must be at least 12 characters long")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one digit")
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError("Password must contain at least one special character")

class MFAService:
    """Multi-Factor Authentication service"""
    def __init__(self, user):
        self.user = user
        self.secret = pyotp.random_base32()
        
    def generate_otp(self):
        totp = pyotp.TOTP(self.secret, interval=300)
        return totp.now()
    
    def verify_otp(self, token):
        totp = pyotp.TOTP(self.secret, interval=300)
        return totp.verify(token)

@ratelimit(key='ip', rate='5/m', block=True)
def login_rate_limited(request, *args, **kwargs):
    """Rate-limited login view wrapper"""
    from django.contrib.auth import login as auth_login
    return auth_login(request, *args, **kwargs)

def check_concurrent_sessions(user, session_key):
    """Prevent concurrent sessions"""
    if getattr(settings, 'PREVENT_CONCURRENT_SESSIONS', False):
        from django.contrib.sessions.models import Session
        sessions = Session.objects.filter(
            expire_date__gte=timezone.now(),
            session_data__contains=str(user.pk)
        ).exclude(session_key=session_key)
        sessions.delete()
