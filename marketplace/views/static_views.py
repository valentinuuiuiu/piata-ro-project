from django.contrib.staticfiles.views import serve
from django.http import HttpResponse
from django.conf import settings
import mimetypes
import os

def serve_static_file(request, path):
    """Serve static files with proper MIME types"""
    # Set the correct MIME type for CSS files
    if path.endswith('.css'):
        content_type = 'text/css'
    else:
        content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    
    # Get the file path
    file_path = os.path.join(settings.STATIC_ROOT, path)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        return HttpResponse(f"File not found: {path}", status=404)
    
    # Read the file content
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Return the file content with the correct MIME type
    response = HttpResponse(file_content, content_type=content_type)
    return response