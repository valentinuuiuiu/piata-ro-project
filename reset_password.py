import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/shiva/piata-ro-project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

# Reset password for admin user
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.save()
    print("Password for admin reset to 'admin123'")
except User.DoesNotExist:
    # Create a new admin user
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Created new admin user with password 'admin123'")
