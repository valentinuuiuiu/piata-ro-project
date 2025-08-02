import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',  # GitHub provider
    'mcp_admin',
    'ai_assistant',
    'marketplace',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'piata_ro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'marketplace', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
        },
    },
]

WSGI_APPLICATION = 'piata_ro.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

# MCP Configuration
MCP_ORCHESTRATOR_ENDPOINT = 'http://localhost:8000'
MCP_API_KEY = 'your_api_key_here'  # Replace with actual API key
MCP_SERVERS = {
    'advertising': {
        'url': 'http://localhost:8001',
        'description': 'Marketing optimization, pricing strategies, content generation'
    },
    'database': {
        'url': 'http://localhost:8002',
        'description': 'Database operations, user management, listing queries'
    },
    'stock': {
        'url': 'http://localhost:8003',
        'description': 'Inventory management, stock tracking, supply chain'
    }
}

# Stripe Configuration
STRIPE_SECRET_KEY = 'your_stripe_secret_key_here'
STRIPE_PUBLISHABLE_KEY = 'your_stripe_publishable_key_here'

# DeepSeek API Configuration
DEEPSEEK_API_KEY = 'your_deepseek_api_key_here'

# LangSmith Configuration
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = 'https://api.smith.langchain.com'
LANGCHAIN_API_KEY = 'your_langchain_api_key_here'
LANGCHAIN_PROJECT = 'piata-ro-mcp-orchestrator'

# Email Configuration (Resend)
EMAIL_BACKEND = 'marketplace.email_backend.ResendEmailBackend'
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@piata.ro'

# Django Allauth Configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
LOGIN_URL = 'marketplace:login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Social account settings
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': [
            'user',
            'user:email',
        ],
        'APP': {
            'client_id': os.environ.get('GITHUB_CLIENT_ID'),
            'secret': os.environ.get('GITHUB_CLIENT_SECRET'),
        }
    }
}
