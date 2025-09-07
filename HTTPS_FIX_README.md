# HTTPS Issue Fix for Django Development Server

## Problem
The Django development server was showing errors like:
```
You're accessing the development server over HTTPS, but it only supports HTTP.
code 400, message Bad request version
```

This happens when browsers, clients, or proxies try to access the HTTP-only development server using HTTPS.

## Solution Implemented

### 1. HTTPS Redirect Middleware (`https_redirect_middleware.py`)
- Detects HTTPS requests and redirects them to HTTP
- Handles SSL handshake attempts gracefully with clear error messages
- Prevents cryptic SSL errors in development

### 2. Enhanced Server Startup (`start_server.py`)
- Added better error handling for SSL-related issues
- Increased startup timeout to 5 seconds
- Added clear messaging about HTTP-only nature
- Set proper Django settings environment variable

### 3. Development Settings Update (`piata_ro/settings_dev.py`)
- Added HTTPS redirect middleware to development middleware stack

## How to Use

1. **Start the server normally:**
   ```bash
   python start_server.py
   ```

2. **Access the server correctly:**
   - Use: `http://localhost:8000` (not https)
   - The server will now handle HTTPS attempts gracefully

3. **Test the fix:**
   ```bash
   python test_https_fix.py
   ```

## What to Expect

- ✅ HTTP requests: Work normally
- 🔄 HTTPS requests: Redirected to HTTP with 301 redirect
- 🔒 SSL handshakes: Clear error message instead of cryptic errors
- 🚫 Malformed requests: Proper 400 responses

## For Production

This fix is for development only. For production:
- Use a proper web server (nginx, Apache)
- Configure SSL/TLS properly
- Use Django's `SECURE_SSL_REDIRECT` setting
- Set up HTTPS certificates

## Files Modified
- `start_server.py` - Enhanced server startup and error handling
- `https_redirect_middleware.py` - New middleware for HTTPS handling
- `piata_ro/settings_dev.py` - Added middleware to development settings
- `test_https_fix.py` - Test script to verify the fix
- `HTTPS_FIX_README.md` - This documentation

## Testing
Run the test script to verify everything works:
```bash
python test_https_fix.py
```

This should resolve the HTTPS-related errors you were seeing in the Django development server logs.
