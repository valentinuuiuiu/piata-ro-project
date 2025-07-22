
#!/usr/bin/env python
"""
Simple SQL Agent for Piata.ro using Pydantic v1
This agent provides basic database operations for the marketplace
"""

import os
import sys
from typing import Optional, List, Dict, Any
import json

# Add the project root directory to Python path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")
else:
    print(f"{project_root} already in Python path")

# Verify the piata_ro module can be found
piata_ro_path = os.path.join(project_root, 'piata_ro')
if os.path.exists(piata_ro_path):
    print(f"Found piata_ro module at {piata_ro_path}")
else:
    print(f"piata_ro module not found at {piata_ro_path}")

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
import django
django.setup()

# Import Django models after setup
from marketplace.models import Listing, Category, User
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from pydantic import BaseModel, Field
from datetime import datetime

class UserCreateData(BaseModel):
    """Data model for creating a new user"""
    username: str = Field(..., description="Username for the new user")
    email: str = Field(..., description="Email address for the new user")
    password: str = Field(..., description="Password for the new user")
    first_name: Optional[str] = Field("", description="First name of the user")
    last_name: Optional[str] = Field("", description="Last name of the user")

class ListingCreateData(BaseModel):
    """Data model for creating a new listing"""
    title: str = Field(..., description="Title of the listing")
    description: str = Field(..., description="Description of the listing")
    price: float = Field(..., description="Price of the listing")
    category_id: int = Field(..., description="ID of the category for the listing")
    seller_id: int = Field(..., description="ID of the seller user")

class ListingUpdateData(BaseModel):
    """Data model for updating a listing"""
    title: Optional[str] = Field(None, description="Updated title of the listing")
    description: Optional[str] = Field(None, description="Updated description of the listing")
    price: Optional[float] = Field(None, description="Updated price of the listing")
    category_id: Optional[int] = Field(None, description="Updated category ID for the listing")

def create_user(data: dict) -> dict:
    """Create a new user in the database"""
    try:
        user_data = UserCreateData(**data)
        
        # Check if user already exists
        if User.objects.filter(username=user_data.username).exists():
            return {"error": f"User with username '{user_data.username}' already exists"}
        
        if User.objects.filter(email=user_data.email).exists():
            return {"error": f"User with email '{user_data.email}' already exists"}
        
        # Create the user
        user = User.objects.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        return {
            "success": True,
            "user_id": user.id,
            "message": f"User '{user.username}' created successfully"
        }
    except Exception as e:
        return {"error": f"Failed to create user: {str(e)}"}

def get_user_info(user_id: int) -> dict:
    """Retrieve information about a user"""
    try:
        user = User.objects.get(id=user_id)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
            "is_active": user.is_active
        }
    except ObjectDoesNotExist:
        return {"error": f"User with ID {user_id} not found"}
    except Exception as e:
        return {"error": f"Failed to retrieve user info: {str(e)}"}

def authenticate_user(username: str, password: str) -> dict:
    """Authenticate a user with username and password"""
    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            return {
                "success": True,
                "user_id": user.id,
                "message": "Authentication successful"
            }
        else:
            return {"error": "Invalid password"}
    except ObjectDoesNotExist:
        return {"error": "User not found"}
    except Exception as e:
        return {"error": f"Authentication failed: {str(e)}"}

def create_listing(data: dict) -> dict:
    """Create a new marketplace listing"""
    try:
        listing_data = ListingCreateData(**data)
        
        # Verify the seller exists
        try:
            seller = User.objects.get(id=listing_data.seller_id)
        except ObjectDoesNotExist:
            return {"error": f"Seller with ID {listing_data.seller_id} not found"}
        
        # Verify the category exists
        try:
            category = Category.objects.get(id=listing_data.category_id)
        except ObjectDoesNotExist:
            return {"error": f"Category with ID {listing_data.category_id} not found"}
        
        # Create the listing
        listing = Listing.objects.create(
            title=listing_data.title,
            description=listing_data.description,
            price=listing_data.price,
            category=category,
            seller=seller
        )
        
        return {
            "success": True,
            "listing_id": listing.id,
            "message": f"Listing '{listing.title}' created successfully"
        }
    except Exception as e:
        return {"error": f"Failed to create listing: {str(e)}"}

def search_listings(query: str, category_id: Optional[int] = None) -> dict:
    """Search for listings by title or description"""
    try:
        listings = Listing.objects.filter(
            title__icontains=query
        ) | Listing.objects.filter(
            description__icontains=query
        )
        
        if category_id:
            listings = listings.filter(category_id=category_id)
        
        results = []
        for listing in listings:
            results.append({
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": listing.price,
                "category": listing.category.name,
                "seller": listing.seller.username,
                "created_at": listing.created_at.isoformat()
            })
        
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": f"Failed to search listings: {str(e)}"}

def get_listings(limit: int = 10, offset: int = 0) -> dict:
    """Get a list of listings with pagination"""
    try:
        listings = Listing.objects.all()[offset:offset + limit]
        
        results = []
        for listing in listings:
            results.append({
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": listing.price,
                "category": listing.category.name,
                "seller": listing.seller.username,
                "created_at": listing.created_at.isoformat()
            })
        
        return {
            "count": Listing.objects.count(),
            "offset": offset,
            "limit": limit,
            "results": results
        }
    except Exception as e:
        return {"error": f"Failed to retrieve listings: {str(e)}"}

def get_database_stats() -> dict:
    """Get basic database statistics"""
    try:
        return {
            "users_count": User.objects.count(),
            "listings_count": Listing.objects.count(),
            "categories_count": Category.objects.count(),
            "active_listings_count": Listing.objects.filter(is_active=True).count(),
            "total_revenue_potential": sum(listing.price for listing in Listing.objects.filter(is_active=True))
        }
    except Exception as e:
        return {"error": f"Failed to get database stats: {str(e)}"}

def execute_custom_query(query: str) -> dict:
    """Execute a custom SELECT query (read-only)"""
    # This is a very basic implementation - in production, you'd want to use a proper query builder
    # and have much more robust security measures
    query = query.strip().lower()
    
    if not query.startswith('select'):
        return {"error": "Only SELECT queries are allowed"}
    
    # Simple protection against dangerous queries
    if any(keyword in query for keyword in ['insert', 'update', 'delete', 'drop', 'alter', 'create']):
        return {"error": "Only SELECT queries are allowed"}
    
    try:
        # This is a very simplified approach - in reality, you'd want to use Django's ORM
        # or a proper database connection with parameterized queries
        if 'from marketplace_listing' in query or 'from listings' in query:
            # Handle listing queries
            listings = Listing.objects.all()[:100]  # Limit results
            results = []
            for listing in listings:
                results.append({
                    "id": listing.id,
                    "title": listing.title,
                    "price": listing.price,
                    "category": listing.category.name,
                    "seller": listing.seller.username
                })
            return {"results": results}
        else:
            return {"error": "Query not supported in this simple agent"}
    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}

def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Simple SQL Agent for Piata.ro"
    }

# Import MCP framework
try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool
except ImportError:
    print("❌ MCP framework not found. Please install it with: pip install mcp-server[fastmcp]")
    sys.exit(1)

def main():
    """Main function to run the agent"""
    print("🚀 Starting Simple SQL Agent for Piata.ro...")
    
    # Create MCP server
    server = FastMCP(
        name="Simple SQL Agent for Piata.ro",
        description="A simple SQL agent for Piata.ro marketplace operations"
    )
    
    # Define tools using the correct MCP API
    @server.tool(
        name="create_user",
        description="Create a new user in the database",
        parameters=UserCreateData.model_json_schema()  # Use model_json_schema instead of schema
    )
    def create_user_tool(data: dict) -> dict:
        return create_user(data)
    
    @server.tool(
        name="get_user_info",
        description="Retrieve information about a user",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID of the user to retrieve"}
            },
            "required": ["user_id"]
        }
    )
    def get_user_info_tool(user_id: int) -> dict:
        return get_user_info(user_id)
    
    @server.tool(
        name="authenticate_user",
        description="Authenticate a user with username and password",
        parameters={
            "type": "object",
            "properties": {
                "username": {"type": "string", "description": "Username of the user"},
                "password": {"type": "string", "description": "Password of the user"}
            },
            "required": ["username", "password"]
        }
    )
    def authenticate_user_tool(username: str, password: str) -> dict:
        return authenticate_user(username, password)
    
    @server.tool(
        name="create_listing",
        description="Create a new marketplace listing",
        parameters=ListingCreateData.model_json_schema()  # Use model_json_schema instead of schema
    )
    def create_listing_tool(data: dict) -> dict:
        return create_listing(data)
    
    @server.tool(
        name="search_listings",
        description="Search for listings by title or description",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "category_id": {"type": "integer", "description": "Optional category ID to filter by"}
            },
            "required": ["query"]
        }
    )
    def search_listings_tool(query: str, category_id: Optional[int] = None) -> dict:
        return search_listings(query, category_id)
    
    @server.tool(
        name="get_listings",
        description="Get a list of listings with pagination",
        parameters={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of listings to return (default: 10)"},
                "offset": {"type": "integer", "description": "Number of listings to skip (default: 0)"}
            }
        }
    )
    def get_listings_tool(limit: int = 10, offset: int = 0) -> dict:
        return get_listings(limit, offset)
    
    @server.tool(
        name="get_database_stats",
        description="Get basic database statistics",
        parameters={}
    )
    def get_database_stats_tool() -> dict:
        return get_database_stats()
    
    @server.tool(
        name="execute_custom_query",
        description="Execute a custom SELECT query (read-only)",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL SELECT query to execute"}
            },
            "required": ["query"]
        }
    )
    def execute_custom_query_tool(query: str) -> dict:
        return execute_custom_query(query)
    
    # Add health check endpoint
    @server.app.get("/health")
    def health():
        return health_check()
    
    # Start the server
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8002, help="Port to bind the server to")
    args = parser.parse_args()
    
    print("\n🎯 Simple SQL Agent ready for Piata.ro database operations!")
    print(f"🌐 Server starting on {args.host}:{args.port}")
    server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
