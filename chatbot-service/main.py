
"""
Unified Chatbot Service v2.0
Integrates all MCP agents (8001-8003) with:
- Automatic routing
- Failover handling
- Request batching
"""

import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import httpx
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot")

app = FastAPI(
    title="Piata.ro Unified Chatbot Service",
    description="API documentation for the integrated chatbot service",
    version="2.0",
    contact={
        "name": "Technical Support",
        "email": "support@piata.ro"
    },
    openapi_tags=[
        {
            "name": "chat",
            "description": "Real-time WebSocket chat operations"
        },
        {
            "name": "health",
            "description": "Service health monitoring"
        }
    ]
)

@dataclass
class MCPAgent:
    port: int
    health_endpoint: str = "/health"
    timeout: float = 5.0

AGENTS = {
    "advertising": MCPAgent(8001),
    "database": MCPAgent(8002),
    "inventory": MCPAgent(8003)
}

class ChatbotManager:
    def __init__(self):
        self.clients = set()
        self.http = httpx.AsyncClient(timeout=10.0)
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)
        
    async def broadcast(self, message: dict):
        for connection in self.clients:
            await connection.send_json(message)
            
    async def route_to_agent(self, intent: str, payload: dict) -> dict:
        """Route request to appropriate MCP agent with failover"""
        agent = self._map_intent_to_agent(intent)
        
        try:
            # First check agent health
            health_url = f"http://localhost:{agent.port}{agent.health_endpoint}"
            health_check = await self.http.get(health_url, timeout=agent.timeout)
            
            if health_check.status_code == 200:
                endpoint = self._get_endpoint(intent)
                url = f"http://localhost:{agent.port}{endpoint}"
                response = await self.http.post(url, json=payload)
                return response.json()
            raise ConnectionError("Agent unhealthy")
            
        except Exception as e:
            logger.warning(f"Failed to reach {agent}: {str(e)}")
            return {"error": f"{intent} service unavailable", "code": 503}
            
    def _map_intent_to_agent(self, intent: str) -> MCPAgent:
        """Determine which agent should handle this intent"""
        routing = {
            "title_optimize": AGENTS["advertising"],
            "create_listing": AGENTS["advertising"],
            "product_query": AGENTS["database"],
            "stock_check": AGENTS["inventory"]
        }
        return routing.get(intent, AGENTS["advertising"])  # Default
    
    def _get_endpoint(self, intent: str) -> str:
        """Get endpoint path for each intent"""
        return {
            "title_optimize": "/optimize",
            "create_listing": "/listings",
            "product_query": "/query",
            "stock_check": "/inventory"
        }.get(intent, "/chatbot")

manager = ChatbotManager()

@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            response = await manager.route_to_agent(
                data.get("intent", ""),
                data
            )
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        manager.clients.remove(websocket)
    except json.JSONDecodeError:
        await websocket.send_json({"error": "Invalid JSON format"})
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        await websocket.send_json({"error": "Internal server error"})

@app.get("/health")
async def health_check():
    """Service health endpoint"""
    return JSONResponse({"status": "healthy", "services": list(AGENTS.keys())})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
