#!/usr/bin/env python3
"""
Google OAuth Test Script for Piata.ro

This script helps you test your Google OAuth configuration.
Run this after setting up your Google Cloud credentials.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings

def test_google_oauth_setup():
    """Test Google OAuth configuration"""
    print("🔍 Testing Google OAuth Setup for Piata.ro")
    print("=" * 50)
    
    # Check if google is in SOCIALACCOUNT_PROVIDERS
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    if 'google' not in providers:
        print("❌ Google provider not found in SOCIALACCOUNT_PROVIDERS")
        return False
    else:
        print("✅ Google provider configured in settings")
    
    # Check environment variables
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if google_client_id and google_client_secret:
        print("✅ Google credentials found in environment variables")
        print(f"   Client ID: {google_client_id[:20]}...")
    else:
        print("⚠️  Google credentials not found in environment variables")
        print("   You can still configure them via Django admin")
    
    # Check SocialApp in database
    try:
        social_apps = SocialApp.objects.filter(provider='google')
        if social_apps.exists():
            app = social_apps.first()
            print(f"✅ Google Social Application found in database")
            print(f"   Name: {app.name}")
            print(f"   Client ID: {app.client_id[:20]}...")
            
            # Check if it's associated with a site
            sites = app.sites.all()
            if sites:
                print(f"   Associated with sites: {[site.domain for site in sites]}")
            else:
                print("⚠️  Social Application not associated with any sites")
                print("   Go to Django admin and add it to a site")
        else:
            print("⚠️  No Google Social Application found in database")
            print("   Create one in Django admin or use environment variables")
    except Exception as e:
        print(f"❌ Error checking Social Applications: {e}")
    
    # Check site configuration
    try:
        current_site = Site.objects.get_current()
        print(f"✅ Current site: {current_site.domain}")
        
        if current_site.domain == 'example.com':
            print("⚠️  Site domain is still 'example.com'")
            print("   Consider updating it to 'localhost:8000' for development")
    except Exception as e:
        print(f"❌ Error checking site configuration: {e}")
    
    print("\n" + "=" * 50)
    print("📝 Next Steps:")
    print("1. Follow GOOGLE_OAUTH_SETUP.md to get Google credentials")
    print("2. Either:")
    print("   a) Add credentials to .env file, or")
    print("   b) Create Social Application in Django admin")
    print("3. Start Django server: python manage.py runserver")
    print("4. Test login at: http://localhost:8000/accounts/login/")
    
    return True

if __name__ == '__main__':
    test_google_oauth_setup()
