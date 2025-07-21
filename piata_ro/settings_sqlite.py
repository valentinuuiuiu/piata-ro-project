# Temporary SQLite settings for data export during migration
from .settings import *

# Override database to use SQLite for data export
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Remove problematic apps for SQLite migration
INSTALLED_APPS = [app for app in INSTALLED_APPS if 'pgvector' not in app.lower()]

# Disable Redis for this check
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
