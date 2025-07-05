
import pyotp
import qrcode
from io import BytesIO
from base64 import b64encode
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class MFAService:
    """Enhanced MFA service with TOTP and backup codes"""
    
    def __init__(self, user_profile):
        self.profile = user_profile
        self.cache_key = f"mfa:{user_profile.user.id}"
        
    def generate_totp(self):
        """Generate new TOTP secret and provisioning URI"""
        if not self.profile.mfa_secret:
            self.profile.mfa_secret = pyotp.random_base32()
            self.profile.save()
            
        totp = pyotp.TOTP(self.profile.mfa_secret)
        provisioning_uri = totp.provisioning_uri(
            name=self.profile.user.email,
            issuer_name=settings.SITE_NAME
        )
        
        # Generate QR code
        img = qrcode.make(provisioning_uri)
        buffer = BytesIO()
        img.save(buffer)
        qr_code = b64encode(buffer.getvalue()).decode()
        
        return {
            'secret': self.profile.mfa_secret,
            'uri': provisioning_uri,
            'qr_code': qr_code
        }
        
    def verify_otp(self, token):
        """Verify TOTP token with grace period"""
        totp = pyotp.TOTP(self.profile.mfa_secret)
        return totp.verify(token, valid_window=1)
        
    def generate_backup_codes(self):
        """Generate 10 one-time backup codes"""
        codes = [pyotp.random_base32()[:8] for _ in range(10)]
        cache.set(f"{self.cache_key}:backup_codes", codes, timeout=None)
        return codes
        
    def verify_backup_code(self, code):
        """Verify and consume backup code"""
        codes = cache.get(f"{self.cache_key}:backup_codes", [])
        if code in codes:
            codes.remove(code)
            cache.set(f"{self.cache_key}:backup_codes", codes, timeout=None)
            return True
        return False
