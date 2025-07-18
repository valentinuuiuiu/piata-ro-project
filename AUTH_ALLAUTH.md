# Django AllAuth Authentication for Piata.ro

This document outlines the authentication setup for Piata.ro using Django AllAuth.

## Overview

User authentication (signup, signin, session management, user profiles) is handled by [Django AllAuth](https://django-allauth.readthedocs.io/). This provides:

1. Local user authentication with email and username
2. Social authentication (Google)
3. Email verification
4. Password reset functionality
5. Account management

## Setup

### Environment Variables

The following environment variables should be set in your `.env` file:

- `GOOGLE_OAUTH2_CLIENT_ID`: Your Google OAuth2 client ID
- `GOOGLE_OAUTH2_CLIENT_SECRET`: Your Google OAuth2 client secret
- `DJANGO_SECRET_KEY`: Django's secret key

### Django Settings

AllAuth is configured in `piata_ro/settings.py`:

```python
# Django AllAuth Configuration
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m',
}

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_LOGIN_ON_GET = True

# Google OAuth2 settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}
```

The authentication backends are configured as:

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

### URLs

AllAuth URLs are included in the main `urls.py`:

```python
urlpatterns = [
    # ...
    path('accounts/', include('allauth.urls')),
    # ...
]
```

## Authentication Flow

1. **User Registration**: Users can register using the `/accounts/signup/` URL provided by AllAuth.
2. **Login**: Users can log in using the `/accounts/login/` URL.
3. **Social Login**: Users can log in with Google using the social login buttons on the login page.
4. **Password Reset**: Users can reset their password using the `/accounts/password/reset/` URL.
5. **Email Verification**: If enabled, users will receive an email verification link.
6. **MFA (Multi-Factor Authentication)**: Custom MFA is implemented for additional security.

## MFA Implementation

The project includes a custom MFA implementation using TOTP (Time-based One-Time Password):

1. MFA is handled by the `verify_mfa` view in `marketplace/views/auth.py`.
2. The `UserProfile` model includes MFA-related fields:
   - `mfa_enabled`: Boolean indicating if MFA is enabled
   - `mfa_secret`: Secret key for TOTP generation
   - `mfa_backup_codes`: Backup codes for account recovery
   - `last_mfa_used`: Timestamp of last MFA usage

## Templates

AllAuth templates are customized and located in:

- `templates/account/` - For AllAuth account management
- `templates/socialaccount/` - For social authentication
- `templates/registration/` - For login and registration

## Google OAuth Setup

To set up Google OAuth:

1. Create a project in the [Google Developer Console](https://console.developers.google.com/)
2. Enable the Google+ API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs: `http://yourdomain.com/accounts/google/login/callback/`
5. Add the client ID and secret to your `.env` file
6. Configure the social application in the Django admin

## Security Considerations

- CSRF protection is enabled by default
- Rate limiting is configured to prevent brute force attacks
- Password validation is enforced according to Django's default settings
- MFA provides an additional layer of security
- Sessions are secured with appropriate cookie settings in production