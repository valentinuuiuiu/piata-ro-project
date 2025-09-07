
import os
2
import django
from django.conf import settings

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
    django.setup()
