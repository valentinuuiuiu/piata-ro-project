#!/usr/bin/env python3
"""
Simple HTTP server for MCP agents with health endpoints
This provides HTTP endpoints that your Django app can call
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/python_script_output.log'),
        logging.StreamHandler()
    ]
)
from asgiref.sync import sync_to_async

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Verify the piata_ro package exists
piata_ro_path = os.path.join(project_root, 'piata_ro')
if not os.path.exists(piata_ro_path):
    raise ImportError(f"Cannot find piata_ro package at: {piata_ro_path}")

# Verify Django can find the settings
print(f"Python path: {sys.path}")
print(f"Looking for settings in: {project_root}/piata_ro/settings.py")

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
import django
try:
    django.setup()
    print("Django setup completed successfully")
except Exception as e:
    print(f"Django setup failed: {e}")
    raise

from marketplace.models import Category, Listing
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepseekRequest(BaseModel):
    query: str
    api_key: str
    context: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

class ResponseModel(BaseModel):
    response: str
    status: str = "success"
    timestamp: Optional[str] = None

# Advertising Agent Functions
def optimize_listing_title(title: str, category: str = "") -> str:
    """Optimize a listing title for better visibility"""
    optimized = title.strip()
    
    # Add category-specific optimizations
    if 'electronics' in category.lower():
        if 'phone' in title.lower() and 'iphone' not in title.lower():
            optimized = f"📱 {optimized}"
    elif 'cars' in category.lower():
        optimized = f"🚗 {optimized}"
    elif 'real estate' in category.lower():
        optimized = f"🏠 {optimized}"
    
    # Ensure title is not too long
    if len(optimized) > 80:
        optimized = optimized[:77] + "..."
    
    return optimized

def validate_deepseek_key(api_key: str) -> bool:
    """Validate Deepseek API key"""
    # TODO: Implement actual validation
    return len(api_key) > 10  # Basic length check for now

async def process_deepseek_query(query: str, context: Dict[str, Any]) -> str:
    """Process query using Deepseek API"""
    # TODO: Implement actual API call
    return f"Processed Deepseek query: {query}"

def suggest_pricing_strategy(title: str, category: str = "") -> Dict[str, Any]:
    """Suggest pricing strategy based on market analysis"""
    try:
        # Get similar listings from database
        listings = Listing.objects.filter(category__name__icontains=category)[:5]
        prices = [float(listing.price) for listing in listings if listing.price]
        
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            return {
                "suggested_price": round(avg_price * 0.95, 2),  # Slightly below average
                "market_average": round(avg_price, 2),
                "price_range": {"min": min_price, "max": max_price},
                "strategy": "Price 5% below market average for competitive advantage"
            }
    except Exception as e:
        logger.error(f"Error in pricing strategy: {e}")
    
    return {
        "suggested_price": 0,
        "market_average": 0,
        "price_range": {"min": 0, "max": 0},
        "strategy": "Unable to analyze market - please research comparable listings"
    }

# Stock Agent Functions
@sync_to_async
def get_inventory_summary(category: str = "") -> Dict[str, Any]:
    """Get inventory summary for a category"""
    from django.db.models import Q
    try:
        if category:
            # Filter by category name containing the search term
            listings = Listing.objects.filter(
                Q(category__name__icontains=category) | 
                Q(title__icontains=category)
            )
        else:
            listings = Listing.objects.all()
        
        total_items = listings.count()
        active_items = listings.filter(status='active').count()
        featured_items = listings.filter(is_featured=True).count()
        
        # Get sample listings for the category
        sample_listings = []
        for listing in listings.filter(status='active')[:5]:
            sample_listings.append({
                "id": str(listing.pk),  # Use pk instead of id to avoid type issues
                "title": listing.title,
                "price": float(listing.price) if listing.price else 0,
                "category": listing.category.name if listing.category else "N/A",
                "location": listing.location
            })
        
        return {
            "category_filter": category if category else "all",
            "total_items": total_items,
            "active_items": active_items,
            "featured_items": featured_items,
            "sample_listings": sample_listings,
            "total_categories": Category.objects.count()
        }
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        return {"error": str(e)}

# Django SQL Agent Functions
@sync_to_async
def search_database(query: str) -> Dict[str, Any]:
    """Search the database based on query"""
    try:
        results = []
        query_lower = query.lower()
        
        # Search categories
        if 'categor' in query_lower:
            categories = Category.objects.all()[:10]
            results = [{"type": "category", "name": cat.name, "id": cat.pk} for cat in categories]
        
        # Search listings
        else:
            listings = Listing.objects.select_related('category')
            
            # Apply filters based on query
            if 'cheap' in query_lower or 'price' in query_lower:
                listings = listings.order_by('price')
            elif 'recent' in query_lower:
                listings = listings.order_by('-created_at')
            
            listings = listings[:10]
            results = []
            for listing in listings:
                results.append({
                    "type": "listing",
                    "id": listing.pk,
                    "title": listing.title,
                    "price": float(listing.price) if listing.price else 0,
                    "category": listing.category.name if listing.category else "N/A",
                    "location": listing.location
                })
        
        return {
            "results": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        logger.error(f"Database search error: {e}")
        return {"error": str(e), "results": []}

# Create FastAPI apps for each agent
advertising_app = FastAPI(title="Advertising Agent", version="1.0.0")
stock_app = FastAPI(title="Stock Agent", version="1.0.0")
django_sql_app = FastAPI(title="Django SQL Agent", version="1.0.0")

# Advertising Agent Endpoints
@advertising_app.post("/process")
async def process_advertising_query(request: QueryRequest):
    """Process advertising-related queries"""
    try:
        query = request.query.lower()
        context = request.context
        
        if 'optimize' in query and 'title' in query:
            # Extract title from context or query
            title = context.get('title', 'Sample Product')
            category = context.get('category', '')
            result = optimize_listing_title(title, category)
            response = f"Optimized title: {result}"
            
        elif 'price' in query or 'pricing' in query:
            title = context.get('title', '')
            category = context.get('category', '')
            result = suggest_pricing_strategy(title, category)
            response = f"Pricing Strategy: {json.dumps(result, indent=2)}"
            
        else:
            response = "I can help with listing optimization, pricing strategies, and marketing advice. Try asking about optimizing titles or pricing strategies."
        
        return ResponseModel(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@advertising_app.get("/status")
async def advertising_status():
    return {"status": "running", "agent": "advertising", "port": 8004}

@advertising_app.get("/health")
async def advertising_health():
    return {"status": "healthy", "agent": "advertising", "port": 8004, "timestamp": datetime.now().isoformat()}

@advertising_app.post("/deepseek/query")
async def deepseek_query(request: DeepseekRequest):
    """Handle Deepseek API queries"""
    # Validate API key
    if not validate_deepseek_key(request.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Process query
        result = await process_deepseek_query(request.query, request.context)
        return ResponseModel(
            response=result,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Shared Deepseek Functions - already defined above
# Removed duplicate declarations

# Stock Agent Endpoints
@stock_app.post("/deepseek/query")
async def stock_deepseek_query(request: DeepseekRequest):
    """Handle Deepseek API queries for stock agent"""
    if not validate_deepseek_key(request.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        result = await process_deepseek_query(request.query, request.context)
        return ResponseModel(
            response=result,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stock_app.post("/process")
async def process_stock_query(request: QueryRequest):
    """Process stock/inventory-related queries"""
    try:
        query = request.query.lower()
        context = request.context
        
        if 'inventory' in query or 'stock' in query:
            category = context.get('category', '')
            result = await get_inventory_summary(category)
            response = f"Inventory Summary for '{category if category else 'all categories'}': {json.dumps(result, indent=2)}"
        else:
            response = "I can help with inventory management, stock levels, and product availability. Try asking about inventory levels."
        
        return ResponseModel(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@stock_app.get("/status")
async def stock_status():
    return {"status": "running", "agent": "stock", "port": 8006}

@stock_app.get("/health")
async def stock_health():
    return {"status": "healthy", "agent": "stock", "port": 8006, "timestamp": datetime.now().isoformat()}

# Django SQL Agent Endpoints
@django_sql_app.post("/deepseek/query")
async def sql_deepseek_query(request: DeepseekRequest):
    """Handle Deepseek API queries for SQL agent"""
    if not validate_deepseek_key(request.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        result = await process_deepseek_query(request.query, request.context)
        return ResponseModel(
            response=result,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@django_sql_app.post("/process")
async def process_sql_query(request: QueryRequest):
    """Process database queries"""
    try:
        query = request.query
        result = await search_database(query)
        response = f"Database Search Results: {json.dumps(result, indent=2)}"
        
        return ResponseModel(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@django_sql_app.get("/status")
async def sql_status():
    return {"status": "running", "agent": "django_sql", "port": 8005}

@django_sql_app.get("/health")
async def sql_health():
    return {"status": "healthy", "agent": "django_sql", "port": 8005, "timestamp": datetime.now().isoformat()}

# Main function to run all agents
async def run_agent(app, port):
    """Run a single agent on specified port"""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Run all agents concurrently"""
    logger.info("🚀 Starting all MCP agents...")
    
    # Create tasks for each agent
    tasks = [
        asyncio.create_task(run_agent(advertising_app, 8004)),
        asyncio.create_task(run_agent(django_sql_app, 8005)),
        asyncio.create_task(run_agent(stock_app, 8006))
    ]
    
    logger.info("📢 Advertising Agent starting on port 8004")
    logger.info("🗄️  Django SQL Agent starting on port 8005") 
    logger.info("📊 Stock Agent starting on port 8006")
    logger.info("🏥 Health endpoints available at /health on all agents")
    
    # Wait for all tasks
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down agents...")
