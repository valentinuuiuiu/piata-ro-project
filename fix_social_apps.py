import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def fix_social_apps():
    """Fix duplicate social app entries"""
    try:
        # Get all GitHub social apps
        github_apps = SocialApp.objects.filter(provider='github')
        
        if github_apps.count() > 1:
            print(f"Found {github_apps.count()} GitHub social apps. Keeping only the first one.")
            # Keep the first one and delete the rest
            for app in github_apps[1:]:
                app.delete()
            print("Duplicate GitHub social apps removed.")
        elif github_apps.count() == 1:
            print("Only one GitHub social app found. No duplicates to remove.")
        else:
            print("No GitHub social apps found.")
            
        # Ensure the app is associated with the site
        if github_apps.exists():
            github_app = github_apps.first()
            site = Site.objects.get(domain='localhost:8000')
            if site not in github_app.sites.all():
                github_app.sites.add(site)
                print("GitHub social app associated with site.")
                
    except Site.DoesNotExist:
        print("Site 'localhost:8000' does not exist.")
    except Exception as e:
        print(f"Error fixing social apps: {e}")

if __name__ == "__main__":
    fix_social_apps()