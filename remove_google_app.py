import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from allauth.socialaccount.models import SocialApp

def remove_google_app():
    """Remove Google social app"""
    try:
        # Get Google social app
        google_apps = SocialApp.objects.filter(provider='google')
        
        if google_apps.exists():
            for app in google_apps:
                app.delete()
                print(f"Removed Google social app: {app.name}")
        else:
            print("No Google social apps found.")
            
    except Exception as e:
        print(f"Error removing Google social app: {e}")

if __name__ == "__main__":
    remove_google_app()