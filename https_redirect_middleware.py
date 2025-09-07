"""
HTTPS Redirect Middleware for Django Development Server
This middleware handles HTTPS requests and redirects them to HTTP
for development environments where SSL is not configured.
"""

import re
from django.http import HttpResponseBadRequest, HttpResponsePermanentRedirect

class HTTPSRedirectMiddleware:
    """
    Middleware to handle HTTPS requests in development environment.
    
    This middleware:
    1. Detects HTTPS requests and redirects them to HTTP
    2. Prevents SSL-related errors in development
    3. Provides clear error messages for malformed requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Pattern to detect SSL handshake attempts
        self.ssl_pattern = re.compile(r'[\x80-\xff]')
        
    def __call__(self, request):
        # Check if this looks like an SSL handshake attempt
        if request.method == 'POST' and 'CONTENT_TYPE' in request.META:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/octet-stream' in content_type or self._looks_like_ssl(request):
                return self._handle_ssl_request(request)
        
        # Check if request came via HTTPS but we're HTTP only
        if request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            return self._redirect_to_http(request)
            
        if request.META.get('wsgi.url_scheme') == 'https':
            return self._redirect_to_http(request)
        
        return self.get_response(request)
    
    def _looks_like_ssl(self, request):
        """Check if the request looks like an SSL handshake"""
        # Check first few bytes for SSL handshake pattern
        if hasattr(request, 'body') and request.body:
            body_start = request.body[:10]
            return any(byte > 127 for byte in body_start)
        return False
    
    def _handle_ssl_request(self, request):
        """Handle SSL handshake attempts gracefully"""
        return HttpResponseBadRequest(
            "SSL/TLS not configured. This is a development server running HTTP only.\n"
            "Please access the server via HTTP: http://localhost:8000\n"
            "For production HTTPS, configure nginx or use a proper web server."
        )
    
    def _redirect_to_http(self, request):
        """Redirect HTTPS requests to HTTP"""
        http_url = request.build_absolute_uri().replace('https://', 'http://', 1)
        return HttpResponsePermanentRedirect(http_url)
    
    def process_exception(self, request, exception):
        """Handle SSL-related exceptions"""
        if 'SSL' in str(exception) or 'TLS' in str(exception):
            return HttpResponseBadRequest(
                "SSL/TLS error: This development server only supports HTTP.\n"
                "Please use http://localhost:8000 instead of https://"
            )
        return None
