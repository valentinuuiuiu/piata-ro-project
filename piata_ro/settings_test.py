from .settings import *

# Use a file-based SQLite database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': 'test_db.sqlite3',
    }
}

# Speed up tests by using a less secure password hasher
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

SPATIALITE_LIBRARY_PATH = '/usr/lib/x86_64-linux-gnu/libspatialite.so'

# Disable logging to the console during tests
import logging
logging.disable(logging.CRITICAL)
