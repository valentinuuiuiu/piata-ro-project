import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from allauth.socialaccount.models import SocialApp

def update_github_credentials():
    """Update GitHub credentials in the database"""
    try:
        github_app = SocialApp.objects.get(provider='github')
        github_app.client_id = os.environ.get('GITHUB_CLIENT_ID', '')
        github_app.secret = os.environ.get('GITHUB_CLIENT_SECRET', '')
        github_app.save()
        print("GitHub credentials updated successfully!")
    except SocialApp.DoesNotExist:
        print("GitHub social app not found in database!")
    except Exception as e:
        print(f"Error updating GitHub credentials: {e}")

if __name__ == "__main__":
    update_github_credentials()