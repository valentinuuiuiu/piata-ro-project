"""
Production settings for Piața.ro
"""
import os
import dj_database_url
from piata_ro.settings import *

# Security settings
DEBUG = False
ALLOWED_HOSTS = ['piata.ro', 'www.piata.ro', '*.azurewebsites.net', 'localhost']

# Database
DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Static files (Azure Blob Storage)
if os.getenv('AZURE_STORAGE_ACCOUNT_NAME'):
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    AZURE_ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
    AZURE_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER', 'media')
else:
    # Fallback to local storage
    STATIC_ROOT = '/app/staticfiles'
    MEDIA_ROOT = '/app/media'

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'marketplace': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Email (Resend)
EMAIL_BACKEND = 'marketplace.email_backend.ResendEmailBackend'
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@piata.ro'
