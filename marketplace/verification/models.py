

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class IdentityVerification(models.Model):
    """Stores user identity verification status and documents"""
    
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='identity_verification')
    status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='pending')
    verification_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    scan_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'Identity Verification'
        verbose_name_plural = 'Identity Verifications'

    def is_valid(self):
        return self.status == 'approved' and not self.is_expired()
        
    def is_expired(self):
        from django.utils import timezone
        return self.expiration_date and self.expiration_date < timezone.now()

