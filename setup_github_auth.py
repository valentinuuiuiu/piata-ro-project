import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Get or create the site
try:
    site = Site.objects.get(domain='localhost:8000')
    print("Site 'localhost:8000' already exists!")
except Site.DoesNotExist:
    site = Site.objects.create(domain='localhost:8000', name='localhost:8000')
    print("Site 'localhost:8000' created successfully!")

# Get GitHub client ID and secret from environment variables
github_client_id = os.environ.get('GITHUB_CLIENT_ID')
github_client_secret = os.environ.get('GITHUB_CLIENT_SECRET')

if github_client_id and github_client_secret:
    # Create or update the GitHub social app
    github_app, created = SocialApp.objects.get_or_create(
        provider='github',
        defaults={
            'name': 'GitHub',
            'client_id': github_client_id,
            'secret': github_client_secret,
        }
    )
    
    # Associate with the site
    if site not in github_app.sites.all():
        github_app.sites.add(site)
        github_app.save()
        print("GitHub social app associated with site!")
    
    if created:
        print("GitHub social app created successfully!")
    else:
        # Update existing app if needed
        if github_app.client_id != github_client_id or github_app.secret != github_client_secret:
            github_app.client_id = github_client_id
            github_app.secret = github_client_secret
            github_app.save()
            print("GitHub social app updated with new credentials!")
        else:
            print("GitHub social app already exists with correct credentials!")
else:
    print("GitHub client ID or secret not found in environment variables!")