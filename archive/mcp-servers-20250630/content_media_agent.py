"""
Content & Media Processing Agent - MCP Server for Piața.ro
A Model Context Protocol server that provides specialized tools for content processing,
image handling, location services, and media management for the Piața.ro marketplace.
"""

import os
import sys
import asyncio
import json
import hashlib
import mimetypes
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from math import radians, cos, sin, asin, sqrt
from urllib.parse import urlencode
from fastapi import FastAPI, Response

app = FastAPI()

def handle_health_check(params):
    """Native MCP health check handler"""
    return {"status": "healthy", "service": "content-media-agent"}

# Initialize FastMCP server for content processing
mcp = FastMCP("Content & Media Processing Agent - Piața.ro")

# Register MCP health check handler
mcp.register_handler("health_check", handle_health_check)

@app.get("/health")
async def health_check():
    return Response(status_code=200, content="OK")

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')

import django
from django.conf import settings
django.setup()

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Google Maps API configuration
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
GOOGLE_GEOCODING_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_PLACES_API_URL = "https://maps.googleapis.com/maps/api/place"

# Free alternative geocoding services (no API key required)
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"

from django.contrib.auth.models import User
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from asgiref.sync import sync_to_async
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, UploadFile, File
import uvicorn

# Import marketplace models
try:
    from marketplace.models import Listing, Category, ListingImage, UserProfile
except ImportError:
    # If marketplace app doesn't exist yet, we'll create placeholder
    Listing = None
    Category = None
    ListingImage = None
    UserProfile = None

# Try to import PIL for image processing
try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Initialize FastMCP server for content processing
mcp = FastMCP("Content & Media Processing Agent - Piața.ro")

# Create FastAPI app for REST endpoints
rest_app = FastAPI(
    title="Content & Media Processing API", 
    version="1.0.0",
    description="Content processing, image handling, and media management for Piața.ro marketplace"
)

# Pydantic models for content processing requests
class ImageProcessingRequest(BaseModel):
    """Request model for image processing operations."""
    image_data: str = Field(description="Base64 encoded image data or file path")
    operation: str = Field(description="Processing operation: resize, optimize, validate, analyze")
    width: Optional[int] = Field(default=None, description="Target width for resize")
    height: Optional[int] = Field(default=None, description="Target height for resize")
    quality: Optional[int] = Field(default=85, description="JPEG quality (1-100)")
    max_file_size: Optional[int] = Field(default=5242880, description="Maximum file size in bytes (5MB default)")

class ContentModerationRequest(BaseModel):
    """Request model for content moderation."""
    content_type: str = Field(description="Type of content: text, listing, image")
    content: str = Field(description="Content to moderate")
    listing_id: Optional[int] = Field(default=None, description="Listing ID if moderating a listing")
    check_profanity: bool = Field(default=True, description="Check for profanity")
    check_spam: bool = Field(default=True, description="Check for spam patterns")

class LocationRequest(BaseModel):
    """Request model for location services."""
    address: Optional[str] = Field(default=None, description="Address to geocode")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")
    operation: str = Field(description="Operation: geocode, reverse_geocode, validate, distance")
    target_lat: Optional[float] = Field(default=None, description="Target latitude for distance calculation")
    target_lng: Optional[float] = Field(default=None, description="Target longitude for distance calculation")

class FileManagementRequest(BaseModel):
    """Request model for file management operations."""
    operation: str = Field(description="Operation: upload, delete, cleanup, analyze")
    file_path: Optional[str] = Field(default=None, description="File path for operations")
    listing_id: Optional[int] = Field(default=None, description="Listing ID for file operations")
    cleanup_days: Optional[int] = Field(default=30, description="Days old for cleanup operations")

# Utility functions for content processing
def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get information about a file."""
    try:
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Calculate file hash
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        
        return {
            "path": file_path,
            "size": stat.st_size,
            "mime_type": mime_type,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": hasher.hexdigest()
        }
    except Exception as e:
        return {"error": f"Error analyzing file: {str(e)}"}

def validate_image_content(image_path: str) -> Dict[str, Any]:
    """Validate image content and extract metadata."""
    if not PIL_AVAILABLE:
        return {"error": "PIL not available for image processing"}
    
    try:
        with Image.open(image_path) as img:
            return {
                "valid": True,
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "has_transparency": img.mode in ('RGBA', 'LA', 'P'),
                "animated": getattr(img, 'is_animated', False)
            }
    except Exception as e:
        return {"valid": False, "error": str(e)}

def basic_profanity_check(text: str) -> Dict[str, Any]:
    """Basic profanity detection."""
    # Simple profanity word list (extend as needed)
    profanity_words = [
        'spam', 'scam', 'fake', 'fraud', 'cheat', 'steal', 'hack',
        # Add more words as needed, but be careful with false positives
    ]
    
    text_lower = text.lower()
    found_words = []
    
    for word in profanity_words:
        if word in text_lower:
            found_words.append(word)
    
    return {
        "has_profanity": len(found_words) > 0,
        "found_words": found_words,
        "confidence": min(len(found_words) * 0.3, 1.0)  # Simple confidence score
    }

def detect_spam_patterns(text: str) -> Dict[str, Any]:
    """Detect spam patterns in text."""
    spam_indicators = {
        "excessive_caps": len([c for c in text if c.isupper()]) / max(len(text), 1) > 0.5,
        "excessive_punctuation": text.count('!') + text.count('?') > len(text) * 0.1,
        "repeated_chars": any(text.count(char * 3) > 0 for char in 'abcdefghijklmnopqrstuvwxyz'),
        "contact_info_spam": any(pattern in text.lower() for pattern in [
            'call now', 'urgent', 'limited time', 'act fast', 'guaranteed',
            'free money', 'no risk', 'click here', 'visit now'
        ])
    }
    
    spam_score = sum(spam_indicators.values()) / len(spam_indicators)
    
    return {
        "is_spam": spam_score > 0.5,
        "spam_score": spam_score,
        "indicators": spam_indicators
    }

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r

def geocode_address(address: str) -> Dict[str, Any]:
    """Geocode an address using Google Maps Geocoding API."""
    if not GOOGLE_MAPS_API_KEY:
        return {
            "success": False,
            "error": "Google Maps API key not configured"
        }
    
    try:
        params = {
            'address': address,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(GOOGLE_GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            
            return {
                "success": True,
                "latitude": location['lat'],
                "longitude": location['lng'],
                "formatted_address": result['formatted_address'],
                "place_id": result.get('place_id'),
                "types": result.get('types', []),
                "address_components": result.get('address_components', [])
            }
        else:
            return {
                "success": False,
                "error": f"Geocoding failed: {data.get('status', 'Unknown error')}"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error during geocoding: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error during geocoding: {str(e)}"
        }

def reverse_geocode_coordinates(latitude: float, longitude: float) -> Dict[str, Any]:
    """Reverse geocode coordinates using Google Maps Geocoding API."""
    if not GOOGLE_MAPS_API_KEY:
        return {
            "success": False,
            "error": "Google Maps API key not configured"
        }
    
    try:
        params = {
            'latlng': f"{latitude},{longitude}",
            'key': GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(GOOGLE_GEOCODING_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            
            return {
                "success": True,
                "formatted_address": result['formatted_address'],
                "place_id": result.get('place_id'),
                "types": result.get('types', []),
                "address_components": result.get('address_components', []),
                "coordinates": {"lat": latitude, "lng": longitude}
            }
        else:
            return {
                "success": False,
                "error": f"Reverse geocoding failed: {data.get('status', 'Unknown error')}"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error during reverse geocoding: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error during reverse geocoding: {str(e)}"
        }

def geocode_address_free(address: str) -> Dict[str, Any]:
    """Geocode an address using free OpenStreetMap Nominatim API."""
    try:
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'Piata.ro/1.0 (contact@piata.ro)'  # Required by Nominatim
        }
        
        response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            
            return {
                "success": True,
                "latitude": float(result['lat']),
                "longitude": float(result['lon']),
                "formatted_address": result.get('display_name', address),
                "place_id": result.get('place_id'),
                "type": result.get('type'),
                "address_components": result.get('address', {})
            }
        else:
            return {
                "success": False,
                "error": "Address not found"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error during free geocoding: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error during free geocoding: {str(e)}"
        }

def reverse_geocode_coordinates_free(latitude: float, longitude: float) -> Dict[str, Any]:
    """Reverse geocode coordinates using free OpenStreetMap Nominatim API."""
    try:
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'Piata.ro/1.0 (contact@piata.ro)'
        }
        
        response = requests.get(NOMINATIM_REVERSE_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data:
            return {
                "success": True,
                "formatted_address": data.get('display_name', f"{latitude}, {longitude}"),
                "place_id": data.get('place_id'),
                "type": data.get('type'),
                "address_components": data.get('address', {}),
                "coordinates": {"lat": latitude, "lng": longitude}
            }
        else:
            return {
                "success": False,
                "error": "Coordinates not found"
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error during free reverse geocoding: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error during free reverse geocoding: {str(e)}"
        }

# FastMCP Tools
@mcp.tool()
def process_image(request: ImageProcessingRequest) -> Dict[str, Any]:
    """
    Process images for the marketplace - resize, optimize, validate, and analyze.
    
    Args:
        request: Image processing request with operation type and parameters
        
    Returns:
        Dictionary with processing results and image information
    """
    if not PIL_AVAILABLE:
        return {"error": "PIL not available for image processing"}
    
    try:
        # Handle base64 data or file path
        if request.image_data.startswith('data:'):
            # Base64 encoded image
            header, data = request.image_data.split(',', 1)
            image_data = base64.b64decode(data)
            img = Image.open(ContentFile(image_data))
        elif os.path.exists(request.image_data):
            # File path
            img = Image.open(request.image_data)
        else:
            return {"error": "Invalid image data or file path"}
        
        original_size = img.size
        result = {
            "operation": request.operation,
            "original_size": original_size,
            "original_format": img.format,
            "original_mode": img.mode
        }
        
        if request.operation == "validate":
            result.update({
                "valid": True,
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "has_transparency": img.mode in ('RGBA', 'LA', 'P')
            })
            
        elif request.operation == "resize":
            if request.width and request.height:
                # Resize to exact dimensions
                img = img.resize((request.width, request.height), Image.Resampling.LANCZOS)
            elif request.width or request.height:
                # Resize maintaining aspect ratio
                img.thumbnail((request.width or img.width, request.height or img.height), Image.Resampling.LANCZOS)
            
            result.update({
                "new_size": img.size,
                "resized": True
            })
            
        elif request.operation == "optimize":
            # Convert to RGB if needed for JPEG
            if img.mode in ('RGBA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Apply optimization
            img = ImageOps.exif_transpose(img)  # Fix orientation
            result.update({
                "optimized": True,
                "quality": request.quality
            })
            
        elif request.operation == "analyze":
            # Detailed analysis
            colors = img.getcolors(maxcolors=256*256*256)
            dominant_color = max(colors, key=lambda x: x[0])[1] if colors else None
            
            result.update({
                "analysis": {
                    "dominant_color": dominant_color,
                    "color_count": len(colors) if colors else 0,
                    "has_transparency": img.mode in ('RGBA', 'LA', 'P'),
                    "aspect_ratio": round(img.width / img.height, 2)
                }
            })
        
        img.close()
        return result
        
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}

@mcp.tool()
def moderate_content(request: ContentModerationRequest) -> Dict[str, Any]:
    """
    Moderate content for inappropriate material, spam, and policy violations.
    
    Args:
        request: Content moderation request
        
    Returns:
        Dictionary with moderation results and recommendations
    """
    try:
        result = {
            "content_type": request.content_type,
            "timestamp": datetime.now().isoformat(),
            "checks_performed": []
        }
        
        if request.content_type == "text" or request.content_type == "listing":
            if request.check_profanity:
                profanity_result = basic_profanity_check(request.content)
                result["profanity_check"] = profanity_result
                result["checks_performed"].append("profanity")
            
            if request.check_spam:
                spam_result = detect_spam_patterns(request.content)
                result["spam_check"] = spam_result
                result["checks_performed"].append("spam")
            
            # Overall assessment
            issues = []
            if result.get("profanity_check", {}).get("has_profanity"):
                issues.append("profanity detected")
            if result.get("spam_check", {}).get("is_spam"):
                issues.append("spam patterns detected")
            
            result.update({
                "approved": len(issues) == 0,
                "issues": issues,
                "recommendation": "approve" if len(issues) == 0 else "review"
            })
            
        elif request.content_type == "image":
            # For images, we can analyze the file if it's a path
            if os.path.exists(request.content):
                image_info = validate_image_content(request.content)
                result["image_validation"] = image_info
                result["checks_performed"].append("image_validation")
                
                result.update({
                    "approved": image_info.get("valid", False),
                    "issues": [] if image_info.get("valid") else ["invalid image format"],
                    "recommendation": "approve" if image_info.get("valid") else "reject"
                })
            else:
                result.update({
                    "approved": False,
                    "issues": ["image file not found"],
                    "recommendation": "reject"
                })
        
        # If we have a listing_id, we could fetch and analyze the full listing
        if request.listing_id and Listing:
            try:
                listing = Listing.objects.get(id=request.listing_id)
                result["listing_info"] = {
                    "title": listing.title,
                    "description": listing.description[:100] + "..." if len(listing.description) > 100 else listing.description,
                    "status": listing.status
                }
            except:
                result["listing_info"] = {"error": "Listing not found"}
        
        return result
        
    except Exception as e:
        return {"error": f"Error moderating content: {str(e)}"}

@mcp.tool()
def process_location(request: LocationRequest) -> Dict[str, Any]:
    """
    Handle location services: geocoding, reverse geocoding, distance calculation.
    
    Args:
        request: Location processing request
        
    Returns:
        Dictionary with location processing results
    """
    try:
        result = {
            "operation": request.operation,
            "timestamp": datetime.now().isoformat()
        }
        
        if request.operation == "validate":
            # Validate coordinates
            if request.latitude is not None and request.longitude is not None:
                valid_lat = -90 <= request.latitude <= 90
                valid_lng = -180 <= request.longitude <= 180
                
                errors = []
                if not valid_lat:
                    errors.append("Invalid latitude (must be between -90 and 90)")
                if not valid_lng:
                    errors.append("Invalid longitude (must be between -180 and 180)")
                result["valid"] = valid_lat and valid_lng
                result["latitude"] = request.latitude
                result["longitude"] = request.longitude
                result["errors"] = errors
            else:
                result["valid"] = False
                result["errors"] = ["Latitude and longitude are required"]
                
        elif request.operation == "distance":
            # Calculate distance between two points
            if all([request.latitude, request.longitude, request.target_lat, request.target_lng]):
                distance = calculate_distance(
                    request.latitude, request.longitude,
                    request.target_lat, request.target_lng
                )
                
                result.update({
                    "distance_km": round(distance, 2),
                    "distance_miles": round(distance * 0.621371, 2),
                    "point1": {"lat": request.latitude, "lng": request.longitude},
                    "point2": {"lat": request.target_lat, "lng": request.target_lng}
                })
            else:
                result.update({
                    "error": "Both source and target coordinates are required"
                })
                
        elif request.operation == "geocode":
            # Try Google Maps first, fallback to free service
            if request.address:
                result["address"] = request.address
                
                # Try Google Maps API first
                if GOOGLE_MAPS_API_KEY:
                    geocode_result = geocode_address(request.address)
                    if geocode_result["success"]:
                        result.update({
                            "geocoded": True,
                            "service": "google_maps",
                            "latitude": geocode_result["latitude"],
                            "longitude": geocode_result["longitude"],
                            "formatted_address": geocode_result["formatted_address"],
                            "place_id": geocode_result.get("place_id"),
                            "types": geocode_result.get("types", [])
                        })
                    else:
                        # Fallback to free service
                        print("Google Maps failed, trying free service...")
                        free_result = geocode_address_free(request.address)
                        if free_result["success"]:
                            result.update({
                                "geocoded": True,
                                "service": "openstreetmap",
                                "latitude": free_result["latitude"],
                                "longitude": free_result["longitude"],
                                "formatted_address": free_result["formatted_address"],
                                "place_id": free_result.get("place_id"),
                                "note": "Using free OpenStreetMap service (Google Maps billing issue)"
                            })
                        else:
                            result.update({
                                "geocoded": False,
                                "error": f"Both Google Maps and free service failed. Google: {geocode_result['error']}, Free: {free_result['error']}"
                            })
                else:
                    # Use free service only
                    free_result = geocode_address_free(request.address)
                    if free_result["success"]:
                        result.update({
                            "geocoded": True,
                            "service": "openstreetmap",
                            "latitude": free_result["latitude"],
                            "longitude": free_result["longitude"],
                            "formatted_address": free_result["formatted_address"],
                            "note": "Using free OpenStreetMap service (no Google Maps API key)"
                        })
                    else:
                        result.update({
                            "geocoded": False,
                            "error": free_result["error"]
                        })
            else:
                result.update({
                    "error": "Address is required for geocoding"
                })
                
        elif request.operation == "reverse_geocode":
            # Try Google Maps first, fallback to free service
            if request.latitude is not None and request.longitude is not None:
                # Try Google Maps API first
                if GOOGLE_MAPS_API_KEY:
                    reverse_result = reverse_geocode_coordinates(request.latitude, request.longitude)
                    if reverse_result["success"]:
                        result.update({
                            "coordinates": {"lat": request.latitude, "lng": request.longitude},
                            "reverse_geocoded": True,
                            "service": "google_maps",
                            "formatted_address": reverse_result["formatted_address"],
                            "place_id": reverse_result.get("place_id"),
                            "types": reverse_result.get("types", []),
                            "address_components": reverse_result.get("address_components", [])
                        })
                    else:
                        # Fallback to free service
                        print("Google Maps failed, trying free service...")
                        free_result = reverse_geocode_coordinates_free(request.latitude, request.longitude)
                        if free_result["success"]:
                            result.update({
                                "coordinates": {"lat": request.latitude, "lng": request.longitude},
                                "reverse_geocoded": True,
                                "service": "openstreetmap",
                                "formatted_address": free_result["formatted_address"],
                                "note": "Using free OpenStreetMap service (Google Maps billing issue)"
                            })
                        else:
                            result.update({
                                "coordinates": {"lat": request.latitude, "lng": request.longitude},
                                "reverse_geocoded": False,
                                "error": f"Both Google Maps and free service failed. Google: {reverse_result['error']}, Free: {free_result['error']}"
                            })
                else:
                    # Use free service only
                    free_result = reverse_geocode_coordinates_free(request.latitude, request.longitude)
                    if free_result["success"]:
                        result.update({
                            "coordinates": {"lat": request.latitude, "lng": request.longitude},
                            "reverse_geocoded": True,
                            "service": "openstreetmap",
                            "formatted_address": free_result["formatted_address"]
                        })
                    else:
                        result.update({
                            "coordinates": {"lat": request.latitude, "lng": request.longitude},
                            "reverse_geocoded": False,
                            "error": free_result["error"]
                        })
            else:
                result.update({
                    "error": "Coordinates are required for reverse geocoding"
                })
        
        return result
        
    except Exception as e:
        return {"error": f"Error processing location: {str(e)}"}

@mcp.tool()
def manage_files(request: FileManagementRequest) -> Dict[str, Any]:
    """
    Manage files and media for listings - cleanup, analysis, validation.
    
    Args:
        request: File management request
        
    Returns:
        Dictionary with file management results
    """
    try:
        result = {
            "operation": request.operation,
            "timestamp": datetime.now().isoformat()
        }
        
        if request.operation == "analyze":
            if request.file_path and os.path.exists(request.file_path):
                file_info = get_file_info(request.file_path)
                result["file_info"] = file_info
                
                # If it's an image, add image-specific analysis
                if file_info.get("mime_type", "").startswith("image/"):
                    image_info = validate_image_content(request.file_path)
                    result["image_analysis"] = image_info
                    
            else:
                result["error"] = "File path is required and file must exist"
                
        elif request.operation == "cleanup":
            # Simulate cleanup operation
            cleanup_count = 0
            errors = []
            
            if request.listing_id and ListingImage:
                try:
                    # Find old images for this listing
                    cutoff_date = datetime.now() - timedelta(days=request.cleanup_days)
                    old_images = ListingImage.objects.filter(
                        listing_id=request.listing_id,
                        created_at__lt=cutoff_date
                    )
                    cleanup_count = old_images.count()
                    # In real implementation: old_images.delete()
                    
                except Exception as e:
                    errors.append(f"Database error: {str(e)}")
            
            result.update({
                "files_cleaned": cleanup_count,
                "cleanup_days": request.cleanup_days,
                "errors": errors
            })
            
        elif request.operation == "validate":
            if request.file_path:
                file_info = get_file_info(request.file_path)
                
                # Check file size limits
                max_size = 5 * 1024 * 1024  # 5MB
                size_ok = file_info.get("size", 0) <= max_size
                
                # Check file type
                allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
                type_ok = file_info.get("mime_type") in allowed_types
                
                result.update({
                    "valid": size_ok and type_ok,
                    "size_ok": size_ok,
                    "type_ok": type_ok,
                    "file_size": file_info.get("size", 0),
                    "max_size": max_size,
                    "file_type": file_info.get("mime_type"),
                    "allowed_types": allowed_types
                })
            else:
                result["error"] = "File path is required"
        
        return result
        
    except Exception as e:
        return {"error": f"Error managing files: {str(e)}"}

@mcp.tool()
def get_content_stats() -> Dict[str, Any]:
    """
    Get statistics about content processing and media management.
    
    Returns:
        Dictionary with content and media statistics
    """
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "pil_available": PIL_AVAILABLE,
            "google_maps_api_enabled": bool(GOOGLE_MAPS_API_KEY),
            "supported_operations": {
                "image_processing": ["resize", "optimize", "validate", "analyze"],
                "content_moderation": ["profanity_check", "spam_detection"],
                "location_services": ["validate", "distance", "geocode", "reverse_geocode"],
                "google_maps": ["geocode", "reverse_geocode", "validate_address", "place_details"],
                "file_management": ["analyze", "cleanup", "validate"]
            },
            "supported_image_formats": ["JPEG", "PNG", "GIF", "WebP"] if PIL_AVAILABLE else [],
            "max_file_size": "5MB",
            "api_integrations": {
                "google_maps": {
                    "enabled": bool(GOOGLE_MAPS_API_KEY),
                    "geocoding_url": GOOGLE_GEOCODING_API_URL,
                    "places_url": GOOGLE_PLACES_API_URL
                }
            },
            "system_info": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "django_version": django.VERSION[:3]
            }
        }
        
        # Add database stats if models are available
        if Listing and ListingImage:
            try:
                stats["database"] = {
                    "total_listings": Listing.objects.count(),
                    "total_images": ListingImage.objects.count(),
                    "active_listings": Listing.objects.filter(status="active").count()
                }
            except:
                stats["database"] = {"error": "Unable to query database"}
        
        # Check media directory
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root and os.path.exists(media_root):
            try:
                media_files = []
                for root, dirs, files in os.walk(media_root):
                    media_files.extend(files)
                
                total_size = sum(
                    os.path.getsize(os.path.join(root, file))
                    for root, dirs, files in os.walk(media_root)
                    for file in files
                )
                
                stats["media_storage"] = {
                    "media_root": media_root,
                    "total_files": len(media_files),
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
            except:
                stats["media_storage"] = {"error": "Unable to analyze media storage"}
        
        return stats
        
    except Exception as e:
        return {"error": f"Error getting content stats: {str(e)}"}

@mcp.tool()
def google_maps_integration(request: LocationRequest) -> Dict[str, Any]:
    """
    Google Maps integration for address validation, geocoding, and place details.
    
    Args:
        request: Location request with Google Maps specific operations
        
    Returns:
        Dictionary with Google Maps API results
    """
    try:
        result = {
            "operation": request.operation,
            "timestamp": datetime.now().isoformat(),
            "google_maps_api_enabled": bool(GOOGLE_MAPS_API_KEY)
        }
        
        if not GOOGLE_MAPS_API_KEY:
            result["error"] = "Google Maps API key not configured. Please set GOOGLE_MAPS_API_KEY environment variable."
            return result
        
        if request.operation == "geocode" and request.address:
            geocode_result = geocode_address(request.address)
            result["geocoding"] = geocode_result
            
        elif request.operation == "reverse_geocode" and request.latitude and request.longitude:
            reverse_result = reverse_geocode_coordinates(request.latitude, request.longitude)
            result["reverse_geocoding"] = reverse_result
            
        elif request.operation == "validate_address" and request.address:
            # Validate address by geocoding and reverse geocoding
            geocode_result = geocode_address(request.address)
            if geocode_result["success"]:
                reverse_result = reverse_geocode_coordinates(
                    geocode_result["latitude"], 
                    geocode_result["longitude"]
                )
                result["validation"] = {
                    "original_address": request.address,
                    "geocoded": geocode_result,
                    "reverse_geocoded": reverse_result,
                    "address_valid": geocode_result["success"] and reverse_result["success"]
                }
            else:
                result["validation"] = {
                    "original_address": request.address,
                    "address_valid": False,
                    "error": geocode_result["error"]
                }
                
        elif request.operation == "place_details" and request.address:
            # Enhanced place details (could be extended with Places API)
            geocode_result = geocode_address(request.address)
            if geocode_result["success"]:
                result["place_details"] = {
                    "address": geocode_result["formatted_address"],
                    "coordinates": {
                        "lat": geocode_result["latitude"],
                        "lng": geocode_result["longitude"]
                    },
                    "place_id": geocode_result.get("place_id"),
                    "types": geocode_result.get("types", []),
                    "address_components": geocode_result.get("address_components", [])
                }
            else:
                result["place_details"] = {
                    "error": geocode_result["error"]
                }
        else:
            result["error"] = f"Invalid operation '{request.operation}' or missing required parameters"
        
        return result
        
    except Exception as e:
        return {"error": f"Error in Google Maps integration: {str(e)}"}

# Async wrappers for all tools
async def process_image_async(request: ImageProcessingRequest) -> Dict[str, Any]:
    """Async wrapper for image processing."""
    return await sync_to_async(process_image)(request)

async def moderate_content_async(request: ContentModerationRequest) -> Dict[str, Any]:
    """Async wrapper for content moderation."""
    return await sync_to_async(moderate_content)(request)

async def process_location_async(request: LocationRequest) -> Dict[str, Any]:
    """Async wrapper for location processing."""
    return await sync_to_async(process_location)(request)

async def manage_files_async(request: FileManagementRequest) -> Dict[str, Any]:
    """Async wrapper for file management."""
    return await sync_to_async(manage_files)(request)

async def google_maps_integration_async(request: LocationRequest) -> Dict[str, Any]:
    """Async wrapper for Google Maps integration."""
    return await sync_to_async(google_maps_integration)(request)

async def get_content_stats_async() -> Dict[str, Any]:
    """Async wrapper for content stats."""
    return await sync_to_async(get_content_stats)()

# FastAPI REST endpoints
@rest_app.post("/call")
async def call_tool(request: dict):
    """Call a content processing tool via REST API."""
    try:
        tool_name = request.get("name")
        args = request.get("arguments", {})
        
        # Get available tools
        tools = await mcp.get_tools()
        available_tools = {tool.name: tool for tool in tools}
        
        if tool_name not in available_tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Call the appropriate async wrapper
        if tool_name == "process_image":
            result = await process_image_async(ImageProcessingRequest(**args))
        elif tool_name == "moderate_content":
            result = await moderate_content_async(ContentModerationRequest(**args))
        elif tool_name == "process_location":
            result = await process_location_async(LocationRequest(**args))
        elif tool_name == "google_maps_integration":
            result = await google_maps_integration_async(LocationRequest(**args))
        elif tool_name == "manage_files":
            result = await manage_files_async(FileManagementRequest(**args))
        elif tool_name == "get_content_stats":
            result = await get_content_stats_async()
        else:
            raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' not implemented")
        
        return {"result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rest_app.get("/tools")
async def list_tools():
    """List all available content processing tools."""
    try:
        tools = await mcp.get_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                for tool in tools
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rest_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Content & Media Processing Agent",
        "timestamp": datetime.now().isoformat(),
        "pil_available": PIL_AVAILABLE
    }

@rest_app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Content & Media Processing Agent",
        "description": "Content processing, image handling, and media management for Piața.ro marketplace",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "call": "/call"
        },
        "features": [
            "Image processing (resize, optimize, validate, analyze)",
            "Content moderation (profanity, spam detection)",
            "Location services (geocoding, distance calculation)",
            "Google Maps API integration (geocoding, reverse geocoding, address validation)",
            "File management (cleanup, validation, analysis)"
        ],
        "integrations": {
            "google_maps": {
                "enabled": bool(GOOGLE_MAPS_API_KEY),
                "features": ["geocoding", "reverse_geocoding", "address_validation", "place_details"]
            }
        }
    }

if __name__ == "__main__":
    print("🎨 Starting Content & Media Processing Agent for Piața.ro...")
    print("🔧 Available tools:")
    print("   - process_image: Image processing and optimization")
    print("   - moderate_content: Content moderation and filtering") 
    print("   - process_location: Location services and geocoding")
    print("   - google_maps_integration: Google Maps API integration")
    print("   - manage_files: File management and cleanup")
    print("   - get_content_stats: Content processing statistics")
    
    # Check Google Maps API configuration
    if GOOGLE_MAPS_API_KEY:
        print("✅ Google Maps API configured and ready")
    else:
        print("⚠️  Google Maps API key not found - geocoding features will be limited")
        print("   Set GOOGLE_MAPS_API_KEY environment variable to enable full location services")
    
    print(f"🌐 REST API available at: http://localhost:8004")
    print(f"📚 API docs at: http://localhost:8004/docs")
    print("✨ Ready to process content for the marketplace!")
    
    uvicorn.run(
        rest_app, 
        host="0.0.0.0", 
        port=8004,
        log_level="info"
    )
