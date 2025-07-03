
from django.conf import settings
from PIL import Image
import os
import uuid

def process_uploaded_image(uploaded_image):
    """Process and save uploaded image with thumbnail generation"""
    try:
        img = Image.open(uploaded_image)
        
        # Resize if exceeds max dimensions
        if img.size[0] > settings.IMAGE_MAX_SIZE[0] or img.size[1] > settings.IMAGE_MAX_SIZE[1]:
            img.thumbnail(settings.IMAGE_MAX_SIZE)
            
        # Generate unique filename
        ext = os.path.splitext(uploaded_image.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(settings.MEDIA_ROOT, 'listings', filename)
        
        # Save original
        img.save(filepath, quality=settings.IMAGE_QUALITY)
        
        # Create thumbnail
        thumb = img.copy()
        thumb.thumbnail(settings.THUMBNAIL_SIZE)
        thumb_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails', filename)
        thumb.save(thumb_path, quality=settings.IMAGE_QUALITY)
        
        return {
            'original': os.path.join('listings', filename),
            'thumbnail': os.path.join('thumbnails', filename)
        }
    except Exception as e:
        raise ValueError(f"Image processing failed: {str(e)}")
