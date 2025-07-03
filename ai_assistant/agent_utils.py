
"""
Shared utilities for MCP agents
"""
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from circuitbreaker import circuit

class AgentHTTPClient:
    """Shared HTTP client with retries and circuit breaking"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )

    @circuit(failure_threshold=3, recovery_timeout=60)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def request(self, method: str, url: str, **kwargs) -> Optional[dict]:
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Request failed: {e}")
            return None

def register_agent(agent_type: str, config: dict):
    """Standard agent registration"""
    # Implementation here
    pass

def health_check():
    """Standard health check endpoint"""
    # Implementation here  
    return {"status": "healthy"}
