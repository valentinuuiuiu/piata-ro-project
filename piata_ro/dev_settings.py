from .settings import *

# Use development settings with SQLite database
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# You can override additional settings here for local development if needed
