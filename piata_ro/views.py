from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
import os
import json
import asyncio
import httpx
import yaml
import decimal
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

# Import Django models for direct database access
from marketplace.models import Category, Listing

def home(request):
    """Home page view"""
    return HttpResponse("""
    <html>
    <head>
        <title>🛒 Piața RO - Romanian Marketplace</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .motto { font-style: italic; text-align: center; color: #7f8c8d; margin-bottom: 30px; }
            .links { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }
            .link-card { background: #3498db; color: white; padding: 20px; border-radius: 8px; text-decoration: none; text-align: center; transition: background 0.3s; }
            .link-card:hover { background: #2980b9; color: white; text-decoration: none; }
            .api-links { margin-top: 20px; }
            .api-links a { display: inline-block; margin: 5px 10px; padding: 8px 15px; background: #27ae60; color: white; border-radius: 5px; text-decoration: none; }
            .api-links a:hover { background: #219a52; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 Piața RO - Romanian Marketplace Platform</h1>
            <p class="motto">Acknowledging The Limitations of The AI is acknowledging The Limitations of Our OLD Patterns Stupid Mind, Dare to Dream and The AI will make it Real</p>
            
            <p>Welcome to the Romanian Marketplace Platform! This is a modern marketplace application built with Django.</p>
            
            <div class="links">
                <a href="/admin/" class="link-card">
                    <h3>📊 Admin Panel</h3>
                    <p>Manage the marketplace</p>
                </a>
                <a href="/api/" class="link-card">
                    <h3>🔧 API Documentation</h3>
                    <p>Explore the REST API</p>
                </a>
            </div>
            
            <div class="api-links">
                <h3>🚀 Available Endpoints:</h3>
                <a href="/api/categories/">Categories</a>
                <a href="/api/listings/">Listings</a>
                <a href="/api/users/">Users</a>
                <a href="/test_endpoint/">Test Endpoint</a>
                <a href="/mcp/process/">MCP Processor</a>
                <a href="/mcp/agents/">MCP Agents</a>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 8px;">
                <h3>🔧 Getting Started:</h3>
                <p>1. Visit <strong>/admin/</strong> to manage the application</p>
                <p>2. Explore <strong>/api/</strong> to see the REST API endpoints</p>
                <p>3. Check out the marketplace categories and listings</p>
            </div>
        </div>
    </body>
    </html>
    """)

@csrf_exempt
def test_endpoint(request):
    """Simple test endpoint"""
    return JsonResponse({
        "status": "success",
        "message": "Basic Django endpoint working",
        "received_data": request.POST.dict()
    })

async def call_mcp_agent(agent_url: str, action: str, data: Optional[dict] = None) -> dict:
    """Call MCP agent with HTTP request"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if data is not None:
                response = await client.post(f"{agent_url}/{action}", json=data)
            else:
                response = await client.get(f"{agent_url}/{action}")
            return response.json()
    except Exception as e:
        return {"error": f"Failed to call {agent_url}: {str(e)}"}

def analyze_query_intent(query: str) -> dict:
    """Analyze user query to determine intent and routing"""
    query_lower = query.lower()
    
    # Database/search queries
    if any(word in query_lower for word in ['show', 'find', 'search', 'list', 'what', 'how many']):
        if any(word in query_lower for word in ['cheap', 'price', 'expensive', 'cost']):
            return {
                'intent': 'search',
                'agent': 'django_sql',
                'filters': {'price_related': True}
            }
        elif any(word in query_lower for word in ['category', 'categories', 'type']):
            return {
                'intent': 'search',
                'agent': 'django_sql',
                'filters': {'category_related': True}
            }
        else:
            return {
                'intent': 'search',
                'agent': 'django_sql',
                'filters': {}
            }
    
    # Marketing/optimization queries
    elif any(word in query_lower for word in ['optimize', 'improve', 'marketing', 'advertise', 'promote']):
        return {
            'intent': 'marketing',
            'agent': 'advertising',
            'filters': {}
        }
    
    # Stock/inventory queries
    elif any(word in query_lower for word in ['stock', 'inventory', 'available', 'quantity']):
        return {
            'intent': 'inventory',
            'agent': 'stock',
            'filters': {}
        }
    
    # Default to search
    return {
        'intent': 'search',
        'agent': 'django_sql',
        'filters': {}
    }

def get_marketplace_context() -> dict:
    """Get current marketplace context from database"""
    try:
        # Get categories with hierarchical structure
        main_categories = Category.objects.filter(parent__isnull=True).values(
            'id', 'name', 'slug', 'icon', 'color'
        )
        
        # Get subcategories grouped by parent
        subcategories = {}
        for subcat in Category.objects.filter(parent__isnull=False).values(
            'id', 'name', 'slug', 'parent_id', 'icon', 'color'
        ):
            parent_id = subcat['parent_id']
            if parent_id not in subcategories:
                subcategories[parent_id] = []
            subcategories[parent_id].append(subcat)
        
        # Build complete category structure
        categories_structure = []
        for category in main_categories:
            cat_data = dict(category)
            cat_data['subcategories'] = subcategories.get(category['id'], [])
            cat_data['listings_count'] = Listing.objects.filter(
                category_id__in=[category['id']] + [sub['id'] for sub in cat_data['subcategories']]
            ).count()
            categories_structure.append(cat_data)
        
        # Get overall statistics
        listings_count = Listing.objects.count()
        active_listings = Listing.objects.filter(status='active').count()
        featured_count = Listing.objects.filter(is_featured=True).count()
        
        # Get recent listings for context
        recent_listings = list(Listing.objects.filter(status='active').select_related('category', 'user').values(
            'id', 'title', 'price', 'currency', 'location', 'category__name', 'created_at'
        ).order_by('-created_at')[:20])
        
        return {
            'categories': list(main_categories),  # Keep simple format for backward compatibility
            'categories_structure': categories_structure,  # Enhanced structure with subcategories
            'total_listings': listings_count,
            'active_listings': active_listings,
            'featured_listings': featured_count,
            'recent_listings': recent_listings,
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Database error: {str(e)}'}

@csrf_exempt
def process_mcp_query(request):
    """Enhanced MCP query processor with agent routing"""
    try:
        if request.method == 'GET':
            context = get_marketplace_context()
            return JsonResponse({
                "message": "Enhanced MCP Processor endpoint is ready!",
                "status": "ready",
                "marketplace_context": context,
                "available_agents": [
                    {"name": "Django SQL Agent", "port": 8002, "endpoint": "http://localhost:8002"},
                    {"name": "Advertising Agent", "port": 8001, "endpoint": "http://localhost:8001"},
                    {"name": "Stock Agent", "port": 8003, "endpoint": "http://localhost:8003"}
                ],
                "usage": "Send POST request with 'query' parameter"
            })
        
        # Get query from request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            query = data.get('query', '')
        else:
            query = request.POST.get('query', '')
            
        if not query:
            return JsonResponse({
                "error": "No query provided",
                "status": "error",
                "usage": "Please provide a 'query' parameter"
            }, status=400)
        
        # Analyze query intent
        intent_analysis = analyze_query_intent(query)
        
        # Get marketplace context
        marketplace_context = get_marketplace_context()
        
        # Route query to appropriate MCP agent based on intent analysis
        try:
            # Get relevant listings for context
            listings_data = []
            query_lower = query.lower()
            
            # Fetch relevant listings based on query
            listings = Listing.objects.select_related('category', 'user')
            
            # Apply category filters based on query
            if 'electronics' in query_lower or 'phone' in query_lower or 'iphone' in query_lower:
                listings = listings.filter(category__name__icontains='Electronics')
            elif 'car' in query_lower or 'bmw' in query_lower or 'vehicle' in query_lower:
                listings = listings.filter(category__name__icontains='Cars')
            elif 'apartment' in query_lower or 'house' in query_lower or 'real estate' in query_lower:
                listings = listings.filter(category__name__icontains='Real Estate')
            elif 'job' in query_lower or 'work' in query_lower:
                listings = listings.filter(category__name__icontains='Jobs')
            elif 'service' in query_lower:
                listings = listings.filter(category__name__icontains='Services')
            
            # Get up to 10 relevant listings for context
            listings_data = []
            for listing in listings[:10]:
                listings_data.append({
                    'id': listing.pk,
                    'title': listing.title,
                    'price': f"{listing.price} {listing.currency}",
                    'location': listing.location,
                    'category': listing.category.name if listing.category else 'N/A',
                    'description': listing.description[:100] + '...' if len(listing.description) > 100 else listing.description
                })

            # Route to appropriate MCP agent based on intent analysis
            agent_port = {
                'django_sql': 8003,
                'advertising': 8001,
                'stock': 8004
            }.get(intent_analysis['agent'], 8003)  # Default to django_sql

            try:
                # Call MCP agent (using synchronous request)
                agent_url = f"http://localhost:{agent_port}/process"
                
                # Convert context to JSON-serializable format
                serializable_context = {
                    'listings': [],
                    'marketplace': {}
                }
                
                # Convert listings data to serializable format
                for listing in listings_data:
                    serializable_listing = {}
                    for key, value in listing.items():
                        if isinstance(value, decimal.Decimal):
                            serializable_listing[key] = float(value)
                        else:
                            serializable_listing[key] = value
                    serializable_context['listings'].append(serializable_listing)
                
                # Convert marketplace context to serializable format
                def make_serializable(obj):
                    if isinstance(obj, dict):
                        return {k: make_serializable(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [make_serializable(item) for item in obj]
                    elif isinstance(obj, decimal.Decimal):
                        return float(obj)
                    else:
                        return obj
                
                serializable_context['marketplace'] = make_serializable(marketplace_context)
                
                response = requests.post(
                    agent_url,
                    json={
                        'query': query,
                        'context': serializable_context
                    },
                    timeout=30.0
                )
                result = response.json()

                return JsonResponse({
                    "result": result.get('response', 'No response from agent'),
                    "status": "success",
                    "query": query,
                    "intent_analysis": intent_analysis,
                    "marketplace_context": marketplace_context,
                    "processed_with": f"MCP Agent ({intent_analysis['agent']})",
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                return JsonResponse({
                    "error": f"Failed to call MCP agent: {str(e)}",
                    "status": "error",
                    "query": query,
                    "intent_analysis": intent_analysis,
                    "marketplace_context": marketplace_context,
                    "processed_with": f"MCP Agent Error ({intent_analysis['agent']})",
                    "timestamp": datetime.now().isoformat()
                }, status=500)
        
        except Exception as agent_error:
            # If there's an error with the agent routing, continue to fallback
            pass
        
        # Fallback: Direct database search for basic queries
        try:
            results = []
            
            if intent_analysis['intent'] == 'search':
                # Perform direct database search
                if intent_analysis['filters'].get('category_related') or 'category' in query.lower() or 'categories' in query.lower():
                    results = list(Category.objects.values('id', 'name', 'slug', 'icon', 'color'))
                else:
                    # Search listings
                    listings = Listing.objects.select_related('category', 'user')
                    
                    # Apply category filters
                    query_lower = query.lower()
                    if 'electronics' in query_lower or 'phone' in query_lower or 'iphone' in query_lower:
                        listings = listings.filter(category__name__icontains='Electronics')
                    elif 'car' in query_lower or 'bmw' in query_lower or 'vehicle' in query_lower:
                        listings = listings.filter(category__name__icontains='Cars')
                    elif 'apartment' in query_lower or 'house' in query_lower or 'real estate' in query_lower:
                        listings = listings.filter(category__name__icontains='Real Estate')
                    elif 'job' in query_lower or 'work' in query_lower:
                        listings = listings.filter(category__name__icontains='Jobs')
                    elif 'service' in query_lower:
                        listings = listings.filter(category__name__icontains='Services')
                    
                    # Apply price filters
                    price_filters = []
                    query_words = query.lower().split()
                    for i, word in enumerate(query_words):
                        if word in ['under', 'below', 'less', 'cheaper']:
                            # Look for number after "under"
                            if i + 1 < len(query_words):
                                try:
                                    price_limit = float(query_words[i + 1])
                                    listings = listings.filter(price__lt=price_limit)
                                except ValueError:
                                    pass
                        elif word in ['over', 'above', 'more', 'expensive']:
                            # Look for number after "over"
                            if i + 1 < len(query_words):
                                try:
                                    price_limit = float(query_words[i + 1])
                                    listings = listings.filter(price__gt=price_limit)
                                except ValueError:
                                    pass
                    
                    # Apply sorting based on query
                    for word in query_words:
                        if word in ['cheap', 'low', 'affordable']:
                            listings = listings.order_by('price')
                        elif word in ['expensive', 'high', 'premium']:
                            listings = listings.order_by('-price')
                        elif word in ['recent', 'new', 'latest']:
                            listings = listings.order_by('-created_at')
                    
                    # Limit results
                    listings = listings[:20]
                    
                    # Convert to dict for JSON response
                    results = []
                    for listing in listings:  # Remove [:20] since we already limited above
                        results.append({
                            'id': listing.pk,
                            'title': listing.title,
                            'price': float(listing.price) if listing.price else 0.0,
                            'location': listing.location,
                            'category': listing.category.name if listing.category else None,
                            'is_featured': listing.is_featured
                        })
            
            return JsonResponse({
                "result": f"Found {len(results)} results for your query: '{query}'",
                "data": results,
                "status": "success",
                "query": query,
                "intent_analysis": intent_analysis,
                "marketplace_context": marketplace_context,
                "processed_with": "Direct Database Query",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as db_error:
            return JsonResponse({
                "error": f"Database query error: {str(db_error)}",
                "status": "error",
                "query": query,
                "fallback_available": True
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            "error": f"General error: {str(e)}",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }, status=500)

@csrf_exempt
def interact_with_mcp_agents(request):
    """Direct interaction with MCP agents running on different ports"""
    try:
        if request.method == 'GET':
            return JsonResponse({
                "message": "MCP Agent Interaction endpoint",
                "available_agents": {
                    "django_sql": "http://localhost:8002",
                    "advertising": "http://localhost:8001", 
                    "stock": "http://localhost:8003"
                },
                "usage": "Send POST with 'agent', 'action', and optional 'data'"
            })
        
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = {
                'agent': request.POST.get('agent'),
                'action': request.POST.get('action'),
                'data': request.POST.get('data', '{}')
            }
        
        agent = data.get('agent')
        action = data.get('action')
        agent_data = data.get('data', {})
        
        if isinstance(agent_data, str):
            try:
                agent_data = json.loads(agent_data)
            except:
                agent_data = {}
        
        # Agent URL mapping
        agent_urls = {
            'django_sql': 'http://localhost:8002',
            'advertising': 'http://localhost:8001',
            'stock': 'http://localhost:8003'
        }
        
        if agent not in agent_urls:
            return JsonResponse({
                "error": f"Unknown agent: {agent}",
                "available_agents": list(agent_urls.keys())
            }, status=400)
        
        if not action:
            return JsonResponse({
                "error": "Action is required",
                "usage": "Provide 'action' parameter"
            }, status=400)
        
        # Try to call the MCP agent
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                call_mcp_agent(agent_urls[agent], action, agent_data)
            )
            loop.close()
            
            return JsonResponse({
                "result": result,
                "status": "success",
                "agent": agent,
                "action": action,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as agent_error:
            return JsonResponse({
                "error": f"Agent call failed: {str(agent_error)}",
                "status": "error",
                "agent": agent,
                "action": action,
                "suggestion": f"Make sure {agent} agent is running on {agent_urls[agent]}"
            }, status=500)
    
    except Exception as e:
        return JsonResponse({
            "error": f"General error: {str(e)}",
            "status": "error"
        }, status=500)

@csrf_exempt
def natural_language_query(request):
    """
    Natural language query endpoint that integrates with PraisonAI
    for intelligent marketplace searches
    """
    if request.method != 'POST':
        return JsonResponse({
            "error": "Only POST method allowed",
            "usage": "Send POST with 'query' parameter"
        }, status=405)
    
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            query = data.get('query', '').strip()
        else:
            query = request.POST.get('query', '').strip()
        
        if not query:
            return JsonResponse({
                "error": "Query parameter is required",
                "usage": "Provide a 'query' parameter with your search request"
            }, status=400)
        
        # Use the existing process_mcp_query logic
        # Create a mock request object for the existing function
        mock_request = type('MockRequest', (), {
            'method': 'POST',
            'content_type': 'application/json',
            'body': json.dumps({'query': query}).encode()
        })()
        
        # Call the existing MCP query processor
        return process_mcp_query(mock_request)
        
    except Exception as e:
        return JsonResponse({
            "error": f"Query processing error: {str(e)}",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }, status=500)
