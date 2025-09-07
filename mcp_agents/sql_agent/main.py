
"""
SQL Agent Server - Handles database operations for the marketplace
Runs on port 8002 as specified in the smart_mcp_orchestrator.py
"""

import os
import json
import logging
import time
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sql_agent")

# Setup Django first
import django
from django.conf import settings

# Ensure Django is configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
    django.setup()

# Import Django models after setup
from marketplace.models import User, Listing, Category

app = FastAPI(title="SQL Agent Server", description="Handles database operations for the marketplace")

# Middleware for logging and error handling
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = f"req_{int(time.time() * 1000)}"
    
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Request {request_id} completed in {process_time:.3f}s - Status: {response.status_code}")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request {request_id} failed in {process_time:.3f}s - Error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "request_id": request_id}
        )

class ProcessRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

@app.post("/process")
async def process(request: ProcessRequest):
    """
    Main endpoint for handling database operations
    The orchestrator will send requests here
    """
    try:
        # Extract operation from query
        query_lower = request.query.lower()
        
        if 'create_user' in query_lower:
            return handle_create_user(request.context)
        elif 'get_user_info' in query_lower:
            return handle_get_user_info(request.context)
        elif 'authenticate_user' in query_lower:
            return handle_authenticate_user(request.context)
        elif 'create_listing' in query_lower:
            return handle_create_listing(request.context)
        elif 'search_listings' in query_lower:
            return handle_search_listings(request.context)
        elif 'get_database_stats' in query_lower:
            return handle_get_database_stats()
        elif 'execute_custom_query' in query_lower:
            return handle_execute_custom_query(request.context)
        else:
            return {
                "error": "Unknown operation",
                "supported_operations": [
                    "create_user", "get_user_info", "authenticate_user",
                    "create_listing", "search_listings", "get_database_stats",
                    "execute_custom_query"
                ]
            }
            
    except Exception as e:
        return {"error": str(e)}

def handle_create_user(context: Dict[str, Any]):
    """Handle user creation"""
    try:
        user = User.objects.create_user(
            username=context.get('username'),
            email=context.get('email'),
            password=context.get('password')
        )
        return {"success": True, "user_id": user.id, "message": "User created successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_get_user_info(context: Dict[str, Any]):
    """Handle getting user information"""
    try:
        user_id = context.get('user_id')
        username = context.get('username')
        
        if user_id:
            user = User.objects.get(id=user_id)
        elif username:
            user = User.objects.get(username=username)
        else:
            return {"error": "Either user_id or username is required"}
            
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "date_joined": user.date_joined.isoformat()
        }
    except User.DoesNotExist:
        return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}

def handle_authenticate_user(context: Dict[str, Any]):
    """Handle user authentication"""
    try:
        username = context.get('username')
        password = context.get('password')
        
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        
        if user is not None:
            return {"authenticated": True, "user_id": user.id}
        else:
            return {"authenticated": False, "error": "Invalid credentials"}
            
    except Exception as e:
        return {"authenticated": False, "error": str(e)}

def handle_create_listing(context: Dict[str, Any]):
    """Handle listing creation"""
    try:
        category_name = context.get('category')
        category = Category.objects.get(name=category_name)
        
        listing = Listing.objects.create(
            title=context.get('title'),
            description=context.get('description'),
            price=context.get('price'),
            category=category,
            seller_id=context.get('seller_id'),
            status='active'
        )
        
        return {"success": True, "listing_id": listing.id, "message": "Listing created successfully"}
        
    except Category.DoesNotExist:
        return {"error": f"Category '{context.get('category')}' not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_search_listings(context: Dict[str, Any]):
    """Handle listing search"""
    try:
        query = context.get('query', '')
        category = context.get('category')
        min_price = context.get('min_price')
        max_price = context.get('max_price')
        
        listings = Listing.objects.filter(status='active')
        
        if query:
            listings = listings.filter(title__icontains=query)
        if category:
            listings = listings.filter(category__name=category)
        if min_price:
            listings = listings.filter(price__gte=min_price)
        if max_price:
            listings = listings.filter(price__lte=max_price)
            
        results = []
        for listing in listings:
            results.append({
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": float(listing.price),
                "category": listing.category.name,
                "seller_id": listing.seller_id,
                "created_at": listing.created_at.isoformat()
            })
            
        return {"count": len(results), "results": results}
        
    except Exception as e:
        return {"error": str(e)}

def handle_get_database_stats():
    """Handle getting database statistics"""
    try:
        total_users = User.objects.count()
        total_listings = Listing.objects.count()
        active_listings = Listing.objects.filter(status='active').count()
        total_categories = Category.objects.count()
        
        return {
            "total_users": total_users,
            "total_listings": total_listings,
            "active_listings": active_listings,
            "total_categories": total_categories,
            "listing_status_distribution": {
                "active": active_listings,
                "inactive": total_listings - active_listings
            }
        }
    except Exception as e:
        return {"error": str(e)}

def handle_execute_custom_query(context: Dict[str, Any]):
    """Handle executing custom queries (limited to safe operations)"""
    # This is a simplified version - in production, you'd want more security
    try:
        model = context.get('model')
        operation = context.get('operation', 'filter')
        filters = context.get('filters', {})
        
        if model == 'User':
            queryset = User.objects
        elif model == 'Listing':
            queryset = Listing.objects
        elif model == 'Category':
            queryset = Category.objects
        else:
            return {"error": f"Model '{model}' not supported"}
            
        if operation == 'count':
            result = queryset.count()
        elif operation == 'filter':
            result = list(queryset.filter(**filters).values())
        else:
            return {"error": f"Operation '{operation}' not supported"}
            
        return {"result": result}
        
    except Exception as e:
        return {"error": str(e)}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        from marketplace.models import User
        user_count = User.objects.count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "user_count": user_count,
            "service": "sql_agent",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Ready endpoint for load balancers
@app.get("/ready")
async def readiness_check():
    """Readiness check for load balancers"""
    return {"status": "ready", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Run the server on port 8002 as specified in the orchestrator
    logger.info("Starting SQL Agent Server on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_config=None)
