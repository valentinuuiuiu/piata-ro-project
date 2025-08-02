import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')
    print("Superuser 'admin' created successfully!")
else:
    print("Superuser 'admin' already exists!")