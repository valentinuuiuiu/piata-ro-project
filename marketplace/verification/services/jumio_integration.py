


import requests
from django.conf import settings
from ..models import IdentityVerification

class JumioVerification:
    """Handles integration with Jumio's ID verification API"""
    
    BASE_URL = "https://netverify.com/api/v4"
    
    def __init__(self):
        self.api_token = settings.JUMIO_API_TOKEN
        self.api_secret = settings.JUMIO_API_SECRET
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
    def initiate_verification(self, user, callback_url):
        """Start new verification process"""
        payload = {
            "customerInternalReference": str(user.id),
            "userReference": user.email,
            "successUrl": f"{callback_url}?status=success",
            "errorUrl": f"{callback_url}?status=error",
            "workflowId": settings.JUMIO_WORKFLOW_ID
        }
        
        response = requests.post(
            f"{self.BASE_URL}/initiate",
            json=payload,
            headers=self.headers,
            auth=(self.api_token, self.api_secret)
        )
        
        if response.status_code == 201:
            data = response.json()
            IdentityVerification.objects.update_or_create(
                user=user,
                defaults={
                    'scan_reference': data['scanReference'],
                    'status': 'pending'
                })
            return data['redirectUrl']
        return None
        
    def check_verification_status(self, scan_reference):
        """Check current verification status"""
        response = requests.get(
            f"{self.BASE_URL}/scans/{scan_reference}",
            headers=self.headers,
            auth=(self.api_token, self.api_secret))
            
        if response.status_code == 200:
            data = response.json()
            return data['verification']['status']
        return None


