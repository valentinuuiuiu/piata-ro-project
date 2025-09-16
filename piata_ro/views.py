from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_ratelimit.decorators import ratelimit
import os
import json
import asyncio
import httpx
import yaml
import decimal
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
from django.utils import timezone
from typing import Optional

# Import Django models for direct database access
from marketplace.models import Category, Listing

# Import the smart MCP orchestrator
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_assistant.smart_mcp_orchestrator import SmartMCPOrchestrator

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
            .stats { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center; }
            .stat-item { display: inline-block; margin: 0 15px; }
            .stat-number { font-size: 24px; font-weight: bold; color: #3498db; }
            .stat-label { font-size: 14px; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 Piața RO - Romanian Marketplace Platform</h1>
            <p class="motto">Your Modern Romanian Marketplace - Buy & Sell Everything!</p>
            
            <p>Welcome to <strong>Piața RO</strong>, the modern Romanian marketplace platform! 
            Built with cutting-edge technology and powered by AI to help you find exactly what you need.</p>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">11</div>
                    <div class="stat-label">Main Categories</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">107</div>
                    <div class="stat-label">Total Categories</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">AI</div>
                    <div class="stat-label">Powered Search</div>
                </div>
            </div>
            
            <div class="links">
                <a href="/admin/" class="link-card">
                    <h3>📊 Admin Panel</h3>
                    <p>Manage your marketplace</p>
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
                <p>4. Try the AI-powered search with <strong>/mcp/process/</strong></p>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                <h4>✨ Features:</h4>
                <ul style="margin: 10px 0;">
                    <li>🤖 AI-powered search and recommendations</li>
                    <li>📱 Modern responsive design</li>
                    <li>🔒 Secure user authentication</li>
                    <li>💬 Real-time messaging</li>
                    <li>📍 Location-based search</li>
                    <li>⭐ Featured listings</li>
                </ul>
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
    
    # Stock/inventory queries - check first
    if any(word in query_lower for word in ['stock', 'inventory', 'available', 'quantity', 'summary']):
        return {
            'intent': 'inventory',
            'agent': 'stock',
            'filters': {}
        }
    
    # Marketing/optimization queries
    elif any(word in query_lower for word in ['optimize', 'improve', 'marketing', 'advertise', 'promote', 'price', 'pricing']):
        return {
            'intent': 'marketing',
            'agent': 'advertising',
            'filters': {}
        }
    
    # Database/search queries
    elif any(word in query_lower for word in ['show', 'find', 'search', 'list', 'what', 'how many']):
        if any(word in query_lower for word in ['cheap', 'expensive', 'cost']):
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
    
    # Default to search
    return {
        'intent': 'search',
        'agent': 'django_sql',
        'filters': {}
    }

def get_marketplace_context() -> dict:
    """Get current marketplace context from database with clean hierarchical structure"""
    try:
        # Get all main categories (clean structure, duplicates already removed)
        main_categories = Category.objects.filter(
            parent__isnull=True
        ).values('id', 'name', 'slug', 'icon', 'color').order_by('name')
        
        # Get subcategories grouped by parent
        subcategories = {}
        for subcat in Category.objects.filter(parent__isnull=False).values(
            'id', 'name', 'slug', 'parent_id', 'icon', 'color'
        ).order_by('name'):
            parent_id = subcat['parent_id']
            if parent_id not in subcategories:
                subcategories[parent_id] = []
            subcategories[parent_id].append(subcat)
        
        # Build complete category structure
        categories_structure = []
        for category in main_categories:
            cat_data = dict(category)
            cat_subcategories = subcategories.get(category['id'], [])
            cat_data['subcategories'] = cat_subcategories
            
            # Calculate listings count for category and all its subcategories
            category_ids = [category['id']] + [sub['id'] for sub in cat_subcategories]
            cat_data['listings_count'] = Listing.objects.filter(
                category_id__in=category_ids
            ).count()
            
            categories_structure.append(cat_data)
        
        # Get overall statistics
        listings_count = Listing.objects.count()
        active_listings = Listing.objects.filter(status='active').count()
        featured_count = Listing.objects.filter(is_featured=True).count()
        
        # Get recent listings for context
        recent_listings = []
        for listing in Listing.objects.filter(status='active').select_related('category', 'user').order_by('-created_at')[:20]:
            recent_listings.append({
                'id': listing.pk,
                'title': listing.title,
                'price': str(listing.price) if listing.price else None,
                'currency': listing.currency,
                'location': listing.location,
                'category__name': listing.category.name if listing.category else None,
                'created_at': listing.created_at.isoformat() if listing.created_at else None
            })
        
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
    """Enhanced MCP query processor using Smart MCP Orchestrator"""
    try:
        if request.method == 'GET':
            context = get_marketplace_context()
            return JsonResponse({
                "message": "Enhanced MCP Processor endpoint is ready!",
                "status": "ready",
                "marketplace_context": context,
                "available_agents": [
                    {"name": "Django SQL Agent", "endpoint": "/ai/chat/"},
                    {"name": "Advertising Agent", "endpoint": "/ai/chat/"},
                    {"name": "Stock Agent", "endpoint": "/ai/chat/"}
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
        
        # Use Smart MCP Orchestrator instead of separate agent ports
        try:
            # Initialize the orchestrator with error handling
            try:
                orchestrator = SmartMCPOrchestrator()
                
                # Process query using orchestrator
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    mcp_response = loop.run_until_complete(
                        orchestrator.process_request(query)
                    )
                    result = {
                        'response': mcp_response.response,
                        'tools_used': mcp_response.tools_used,
                        'tool_results': mcp_response.tool_results
                    }
                finally:
                    loop.close()
                
                return JsonResponse({
                    "result": result.get('response', 'No response from orchestrator'),
                    "status": "success",
                    "query": query,
                    "intent_analysis": intent_analysis,
                    "marketplace_context": marketplace_context,
                    "processed_with": f"Smart MCP Orchestrator ({intent_analysis['agent']})",
                    "timestamp": datetime.now().isoformat()
                })

            except ValueError as ve:
                # Handle missing API key or configuration issues
                if "DeepSeek API key" in str(ve):
                    return JsonResponse({
                        "warning": "Smart MCP Orchestrator requires DEEPSEEK_API_KEY environment variable",
                        "status": "fallback",
                        "query": query,
                        "intent_analysis": intent_analysis,
                        "marketplace_context": marketplace_context,
                        "processed_with": "Direct Database Query (Orchestrator unavailable)",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    raise ve

        except Exception as e:
            return JsonResponse({
                "warning": f"Orchestrator unavailable: {str(e)}",
                "status": "fallback",
                "query": query,
                "intent_analysis": intent_analysis,
                "marketplace_context": marketplace_context,
                "processed_with": f"Direct Database Query (Orchestrator Error)",
                "timestamp": datetime.now().isoformat()
            })
        
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
                    "django_sql": "http://localhost:8005",
                    "advertising": "http://localhost:8004", 
                    "stock": "http://localhost:8006"
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
            'django_sql': 'http://localhost:8005',
            'advertising': 'http://localhost:8004',
            'stock': 'http://localhost:8006'
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



def openai_models_endpoint(request):
    """Temporary placeholder for OpenAI models endpoint"""
    return JsonResponse({
        "object": "list",
        "data": [{
            "id": "gpt-3.5-turbo",
            "object": "model", 
            "ready": True
        }]
    })


@csrf_exempt
def openai_chat_completions(request):
    """Temporary placeholder for OpenAI chat completions endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            return JsonResponse({
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "gpt-3.5-turbo",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a simulated response from the OpenAI API"
                    },
                    "finish_reason": "stop"
                }]
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@ratelimit(key='ip', rate='100/h', block=True)
def rate_limit_exceeded(request):
    """
    View for handling rate limit exceeded requests
    """
    return JsonResponse({
        'error': 'Rate limit exceeded',
        'message': 'You have made too many requests. Please try again later.',
        'retry_after': 3600  # 1 hour
    }, status=429)


@cache_page(60 * 5)  # Cache for 5 minutes
@vary_on_headers('User-Agent')
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })
