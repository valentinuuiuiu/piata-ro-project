import os
import json
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator
import logging

# Setup Django first
import django
from django.conf import settings

# Ensure Django is configured
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
    django.setup()

# Direct HTTP client for DeepSeek API
import httpx

# Set up LangSmith tracing from Django settings
os.environ["LANGCHAIN_TRACING_V2"] = str(getattr(settings, 'LANGCHAIN_TRACING_V2', True))
os.environ["LANGCHAIN_ENDPOINT"] = getattr(settings, 'LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
os.environ["LANGCHAIN_API_KEY"] = getattr(settings, 'LANGCHAIN_API_KEY', '')
os.environ["LANGCHAIN_PROJECT"] = getattr(settings, 'LANGCHAIN_PROJECT', 'piata-ro-mcp-orchestrator')

logger = logging.getLogger(__name__)

class MCPServerType(str, Enum):
    """Enum for MCP server types"""
    ADVERTISING = "advertising"
    DATABASE = "database"
    STOCK = "stock"

class MCPServerConfig(BaseModel):
    """Configuration for MCP servers"""
    name: str
    port: int
    url: str
    description: str
    tools: List[str]
    
    @validator('url', pre=True, always=True)
    def build_url(cls, v, values):
        if v:
            return v
        port = values.get('port', 8000)
        return f"http://localhost:{port}"

class RequestIntent(BaseModel):
    """Pydantic model for analyzing user request intent"""
    intent_type: Literal["database", "advertising", "stock", "general"] = Field(
        description="Primary intent category of the user request"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, 
        description="Confidence score for the intent classification"
    )
    required_tools: List[str] = Field(
        default_factory=list,
        description="List of specific tools needed to fulfill the request"
    )
    server_needed: Optional[MCPServerType] = Field(
        description="Which MCP server should handle this request"
    )
    reasoning: str = Field(
        description="Explanation of why this intent was chosen"
    )

class MCPToolCall(BaseModel):
    """Pydantic model for MCP tool calls"""
    server: MCPServerType
    tool: str
    params: Dict[str, Any] = Field(default_factory=dict)
    expected_result: str = Field(
        description="What we expect this tool call to return"
    )

class MCPResponse(BaseModel):
    """Pydantic model for MCP responses"""
    success: bool
    response: str
    tools_used: List[str] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    intent_analysis: Optional[RequestIntent] = None
    reasoning: str = Field(default="", description="AI reasoning for the response")

class SmartMCPOrchestrator(BaseModel):
    """
    Pydantic-based MCP Orchestrator with intelligent routing
    Uses LangSmith for tracing and debugging decision-making
    """
    
    class Config:
        arbitrary_types_allowed = True
    
    # DeepSeek API configuration
    deepseek_api_key: str = Field(default_factory=lambda: getattr(settings, 'DEEPSEEK_API_KEY', ''))
    deepseek_api_url: str = Field(default='https://api.deepseek.com/v1/chat/completions')
    mcp_servers: Dict[MCPServerType, MCPServerConfig] = Field(
        default_factory=lambda: {
            MCPServerType.ADVERTISING: MCPServerConfig(
                name="Marketing Agent",
                port=8001,
                url="http://localhost:8001",
                description="Marketing optimization, pricing strategies, content generation",
                tools=[
                    "optimize_listing_title",
                    "generate_description_template", 
                    "suggest_pricing_strategy",
                    "generate_promotional_content",
                    "analyze_competitor_pricing",
                    "suggest_best_posting_times"
                ]
            ),
            MCPServerType.DATABASE: MCPServerConfig(
                name="SQL Agent", 
                port=8002,
                url="http://localhost:8002",
                description="Database operations, user management, listing queries",
                tools=[
                    "create_user",
                    "get_user_info",
                    "authenticate_user",
                    "create_listing",
                    "search_listings", 
                    "get_database_stats",
                    "execute_custom_query"
                ]
            ),
            MCPServerType.STOCK: MCPServerConfig(
                name="Stock Agent",
                port=8003,
                url="http://localhost:8003",
                description="Inventory management, stock tracking, supply chain",
                tools=[
                    "get_inventory_summary",
                    "check_stock_levels",
                    "forecast_demand",
                    "manage_suppliers",
                    "track_shipments",
                    "generate_inventory_reports"
                ]
            )
        }
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialize DeepSeek API key
        if not self.deepseek_api_key:
            raise ValueError("DeepSeek API key not configured")
    
    async def analyze_intent(self, user_message: str) -> RequestIntent:
        """
        Analyze user intent using Pydantic model and LLM with LangSmith tracing
        This is where the smart routing decisions happen
        """
        
        try:
            # Use DeepSeek API for intent analysis
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.deepseek_api_url,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.deepseek_api_key}'
                    },
                    json={
                        'model': 'deepseek-chat',
                        'messages': [
                            {
                                'role': 'system',
                                'content': '''You are an intelligent routing agent for a marketplace platform. 
                                Analyze user requests and determine which MCP server should handle them.
                                
                                Available servers and their capabilities:
                                1. DATABASE (port 8002): User management, listings, SQL queries, database stats
                                2. ADVERTISING (port 8001): Marketing optimization, pricing, content generation  
                                3. STOCK (port 8003): Inventory management, stock tracking, supply chain
                                
                                Respond with JSON in this exact format:
                                {
                                    "intent_type": "database|advertising|stock|general",
                                    "confidence": 0.8,
                                    "required_tools": [],
                                    "server_needed": "database|advertising|stock|null",
                                    "reasoning": "explanation"
                                }'''
                            },
                            {
                                'role': 'user',
                                'content': f'User request: {user_message}'
                            }
                        ],
                        'max_tokens': 200,
                        'temperature': 0.1
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    content = result_data['choices'][0]['message']['content']
                    
                    # Parse JSON response
                    intent_data = json.loads(content)
                    
                    # Map server_needed to enum
                    server_map = {
                        'database': MCPServerType.DATABASE,
                        'advertising': MCPServerType.ADVERTISING,
                        'stock': MCPServerType.STOCK
                    }
                    
                    return RequestIntent(
                        intent_type=intent_data['intent_type'],
                        confidence=intent_data['confidence'],
                        required_tools=intent_data.get('required_tools', []),
                        server_needed=server_map.get(intent_data.get('server_needed')),
                        reasoning=intent_data['reasoning']
                    )
                else:
                    raise Exception(f"DeepSeek API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            # Fallback to simple keyword matching
            return self._fallback_intent_analysis(user_message)
    
    def _fallback_intent_analysis(self, message: str) -> RequestIntent:
        """Fallback intent analysis using keyword matching"""
        message_lower = message.lower()
        
        # Database keywords
        if any(word in message_lower for word in [
            'user', 'database', 'sql', 'query', 'listing', 'search', 'stats', 'create'
        ]):
            return RequestIntent(
                intent_type="database",
                confidence=0.7,
                server_needed=MCPServerType.DATABASE,
                reasoning="Fallback: Detected database-related keywords"
            )
        
        # Advertising keywords  
        elif any(word in message_lower for word in [
            'optimize', 'marketing', 'price', 'pricing', 'title', 'description', 'promote'
        ]):
            return RequestIntent(
                intent_type="advertising", 
                confidence=0.7,
                server_needed=MCPServerType.ADVERTISING,
                reasoning="Fallback: Detected advertising-related keywords"
            )
        
        # Stock keywords
        elif any(word in message_lower for word in [
            'inventory', 'stock', 'supply', 'forecast', 'supplier'
        ]):
            return RequestIntent(
                intent_type="stock",
                confidence=0.7, 
                server_needed=MCPServerType.STOCK,
                reasoning="Fallback: Detected stock-related keywords"
            )
        
        else:
            return RequestIntent(
                intent_type="general",
                confidence=0.5,
                server_needed=None,
                reasoning="Fallback: No specific keywords detected"
            )
    
    async def route_to_mcp_server(self, intent: RequestIntent, user_message: str) -> List[MCPToolCall]:
        """
        Route request to appropriate MCP server based on intent analysis
        Returns list of tool calls to make with intelligent tool selection
        """
        
        if not intent.server_needed:
            return []
        
        server_config = self.mcp_servers[intent.server_needed]
        
        # Enhanced tool selection based on intent and message content
        tool_calls = []
        
        # Database server tools
        if intent.server_needed == MCPServerType.DATABASE:
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['user', 'create user', 'register']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="create_user",
                    params={"query": user_message},
                    expected_result="User creation result"
                ))
            elif any(word in message_lower for word in ['search', 'find', 'listings', 'items']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="search_listings",
                    params={"query": user_message},
                    expected_result="Search results for listings"
                ))
            elif any(word in message_lower for word in ['stats', 'statistics', 'analytics']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="get_database_stats",
                    params={"query": user_message},
                    expected_result="Database statistics"
                ))
            else:
                # Default to generic query
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="execute_custom_query",
                    params={"query": user_message},
                    expected_result="Query execution result"
                ))
        
        # Advertising server tools
        elif intent.server_needed == MCPServerType.ADVERTISING:
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['title', 'optimize title']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="optimize_listing_title",
                    params={"query": user_message},
                    expected_result="Optimized title suggestions"
                ))
            elif any(word in message_lower for word in ['description', 'write description']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="generate_description_template",
                    params={"query": user_message},
                    expected_result="Generated description template"
                ))
            elif any(word in message_lower for word in ['price', 'pricing', 'cost']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="suggest_pricing_strategy",
                    params={"query": user_message},
                    expected_result="Pricing strategy suggestions"
                ))
            else:
                # Default to generic marketing optimization
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="generate_promotional_content",
                    params={"query": user_message},
                    expected_result="Promotional content generation"
                ))
        
        # Stock server tools
        elif intent.server_needed == MCPServerType.STOCK:
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['inventory', 'stock levels']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="get_inventory_summary",
                    params={"query": user_message},
                    expected_result="Inventory summary"
                ))
            elif any(word in message_lower for word in ['forecast', 'demand', 'prediction']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="forecast_demand",
                    params={"query": user_message},
                    expected_result="Demand forecast"
                ))
            elif any(word in message_lower for word in ['supplier', 'vendor']):
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="manage_suppliers",
                    params={"query": user_message},
                    expected_result="Supplier management result"
                ))
            else:
                # Default to generic stock query
                tool_calls.append(MCPToolCall(
                    server=intent.server_needed,
                    tool="get_inventory_summary",
                    params={"query": user_message},
                    expected_result="Inventory information"
                ))
        
        return tool_calls
    
    async def execute_mcp_tools(self, tool_calls: List[MCPToolCall]) -> List[Dict[str, Any]]:
        """Execute the selected MCP tools via real SSE communication"""
        results = []
        
        for tool_call in tool_calls:
            try:
                # Call the real MCP server
                result = await self._call_mcp_server(tool_call)
                results.append({
                    'tool': f"{tool_call.server}.{tool_call.tool}",
                    'result': result,
                    'success': True
                })
                logger.info(f"Successfully executed {tool_call.tool} on {tool_call.server}")
            except Exception as e:
                logger.error(f"Failed to execute {tool_call.tool} on {tool_call.server}: {e}")
                results.append({
                    'tool': f"{tool_call.server}.{tool_call.tool}",
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    async def _call_mcp_server(self, tool_call: MCPToolCall, max_retries: int = 3) -> Dict[str, Any]:
        """Make actual call to MCP server via HTTP with retry mechanism"""
        server_config = self.mcp_servers[tool_call.server]
        
        # Prepare the request payload for the MCP server (using MCP protocol format)
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_call.tool,
                "arguments": tool_call.params
            },
            "id": f"call_{tool_call.tool}_{hash(str(tool_call.params))}"
        }
        
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Call the process endpoint on the MCP server
                    response = await client.post(
                        f"{server_config.url}/process",
                        json={
                            "query": tool_call.params.get("query", ""),
                            "context": tool_call.params
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"MCP server {tool_call.server} returned: {result}")
                        
                        # Check if the result contains an error
                        if isinstance(result, dict) and result.get("error"):
                            logger.warning(f"MCP server returned error: {result['error']}")
                            last_error = result["error"]
                            retry_count += 1
                            await asyncio.sleep(1 * retry_count)  # Exponential backoff
                            continue
                        
                        # Extract the result from MCP protocol response
                        if "result" in result:
                            return result["result"]
                        else:
                            return result
                    elif response.status_code >= 500:
                        # Server error - retry
                        logger.warning(f"Server error {response.status_code}, retrying...")
                        retry_count += 1
                        await asyncio.sleep(1 * retry_count)  # Exponential backoff
                        last_error = f"Server error {response.status_code}"
                        continue
                    else:
                        # Client error - don't retry
                        logger.error(f"MCP server error {response.status_code}: {response.text}")
                        return {
                            "error": f"Server returned {response.status_code}", 
                            "details": response.text[:200]  # Limit detail length
                        }
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout calling {tool_call.server} server, retrying...")
                retry_count += 1
                await asyncio.sleep(1 * retry_count)  # Exponential backoff
                last_error = "Request timeout"
                continue
            except httpx.RequestError as e:
                logger.warning(f"Request error calling {tool_call.server}: {e}, retrying...")
                retry_count += 1
                await asyncio.sleep(1 * retry_count)  # Exponential backoff
                last_error = f"Request failed: {str(e)}"
                continue
            except Exception as e:
                logger.error(f"Unexpected error calling {tool_call.server}: {e}")
                return {"error": f"Unexpected error: {str(e)}"}
        
        # If we reached here, all retries failed
        logger.error(f"All {max_retries} retries failed for {tool_call.server}.{tool_call.tool}")
        return {
            "error": f"Failed after {max_retries} attempts",
            "last_error": last_error,
            "server": tool_call.server.value,
            "tool": tool_call.tool
        }
    
    async def process_request(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> MCPResponse:
        """
        Main orchestration method - analyzes intent and routes to appropriate MCP servers
        """
        
        # Step 1: Analyze user intent using Pydantic model
        intent = await self.analyze_intent(user_message)
        logger.info(f"Intent analysis: {intent.dict()}")
        
        # Step 2: Route to appropriate MCP server 
        tool_calls = await self.route_to_mcp_server(intent, user_message)
        logger.info(f"Generated tool calls: {[call.dict() for call in tool_calls]}")
        
        # Step 3: Execute MCP tools
        tool_results = await self.execute_mcp_tools(tool_calls)
        
        # Step 4: Generate final response using LLM
        final_response = await self._generate_final_response(
            user_message, intent, tool_results, conversation_history
        )
        
        return MCPResponse(
            success=True,
            response=final_response,
            tools_used=[result['tool'] for result in tool_results if result.get('success')],
            tool_results=tool_results,
            intent_analysis=intent,
            reasoning=f"Analyzed as {intent.intent_type} with {intent.confidence:.2f} confidence"
        )
    
    async def _generate_final_response(
        self, 
        user_message: str, 
        intent: RequestIntent, 
        tool_results: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Generate final response using DeepSeek API with tool results"""
        
        # Prepare context
        context = f"""
        User Request: "{user_message}"
        Intent Analysis: {intent.reasoning}
        Server Used: {intent.server_needed}
        
        Tool Results:
        """
        
        for result in tool_results:
            if result.get('success'):
                context += f"✅ {result['tool']}: {json.dumps(result['result'], indent=2)}\n"
            else:
                context += f"❌ {result['tool']}: {result.get('error', 'Unknown error')}\n"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.deepseek_api_url,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.deepseek_api_key}'
                    },
                    json={
                        'model': 'deepseek-chat',
                        'messages': [
                            {
                                'role': 'system',
                                'content': f'''You are an AI assistant for Piața.ro marketplace admin panel. 
                                
                                Based on the tool results provided, give a helpful, concise response to the user.
                                Be specific about the actions taken and results obtained.
                                
                                Context: {context}'''
                            },
                            {
                                'role': 'user',
                                'content': user_message
                            }
                        ],
                        'max_tokens': 500,
                        'temperature': 0.3
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    logger.info("Generated final response successfully")
                    return result_data['choices'][0]['message']['content']
                else:
                    raise Exception(f"DeepSeek API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Final response generation failed: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

# For backward compatibility
class MCPOrchestrator:
    """Wrapper class for backward compatibility"""
    
    def __init__(self):
        self.smart_orchestrator = SmartMCPOrchestrator()
    
    async def process_request(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process request using smart Pydantic orchestrator"""
        try:
            mcp_response = await self.smart_orchestrator.process_request(user_message, conversation_history)
            
            # Convert to legacy format
            return {
                'response': mcp_response.response,
                'tools_used': mcp_response.tools_used,
                'tool_results': mcp_response.tool_results
            }
        except Exception as e:
            logger.error(f"MCP Orchestrator error: {e}")
            return {
                'response': f"I apologize, but I encountered an error: {str(e)}",
                'tools_used': [],
                'tool_results': []
            }
