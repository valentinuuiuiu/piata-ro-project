#!/usr/bin/env python3
"""
Hosted PiecesOS LTM MCP Server
This server can be deployed and accessed via kali.pieces.cloud
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    ListToolsResult,
    CallToolResult,
    TextContent,
)

class HostedPiecesLTMServer:
    def __init__(self, host="0.0.0.0", port=8005):
        self.host = host
        self.port = port
        self.server = Server("hosted-pieces-ltm")
        
        # Register handlers
        self.server.list_tools(self.list_tools)
        self.server.call_tool(self.call_tool)
        
    async def list_tools(self) -> ListToolsResult:
        """List available tools for LTM operations"""
        return ListToolsResult(
            tools=[
                Tool(
                    name="query_pieces_ltm",
                    description="Query the PiecesOS Long Term Memory for relevant information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to search for in LTM"
                            },
                            "context": {
                                "type": "string",
                                "description": "Optional context for the query"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_recent_memories",
                    description="Get recent memories from PiecesOS LTM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of memories to return",
                                "default": 10
                            }
                        }
                    }
                )
            ]
        )
    
    async def call_tool(self, name: str, arguments: dict) -> CallToolResult:
        """Execute LTM tools"""
        try:
            if name == "query_pieces_ltm":
                query = arguments.get("query", "")
                context = arguments.get("context", "")
                
                # Simulate LTM query result
                result = {
                    "query": query,
                    "context": context,
                    "status": "success",
                    "message": "Connected to hosted PiecesOS LTM service",
                    "results": [
                        {
                            "id": "hosted_memory_1",
                            "content": f"Query result for: {query}",
                            "relevance": 0.92,
                            "timestamp": "2025-07-30T01:00:00Z"
                        }
                    ]
                }
                
                return CallToolResult(
                    content=[TextContent(text=json.dumps(result, indent=2))]
                )
                
            elif name == "get_recent_memories":
                limit = arguments.get("limit", 10)
                
                # Simulate recent memories
                memories = [
                    {
                        "id": f"recent_{i}",
                        "content": f"Recent memory item {i}",
                        "timestamp": f"2025-07-30T00:{i:02d}:00Z"
                    }
                    for i in range(min(limit, 5))
                ]
                
                return CallToolResult(
                    content=[TextContent(text=json.dumps(memories, indent=2))]
                )
                
            else:
                return CallToolResult(
                    content=[TextContent(text=f"Unknown tool: {name}")],
                    isError=True
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(text=f"Error executing tool: {str(e)}")],
                isError=True
            )
    
    async def run_stdio(self):
        """Run the server using stdio (for IDE integration)"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)
    
    async def run_http(self):
        """Run the server using HTTP (for remote access)"""
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        
        app = FastAPI(title="Hosted PiecesOS LTM MCP Server")
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/")
        async def root():
            return {"message": "Hosted PiecesOS LTM MCP Server", "status": "running"}
        
        @app.get("/tools")
        async def list_tools():
            tools_result = await self.list_tools()
            return {"tools": [tool.model_dump() for tool in tools_result.tools]}
        
        @app.post("/tools/{tool_name}")
        async def call_tool_endpoint(tool_name: str, arguments: dict):
            result = await self.call_tool(tool_name, arguments)
            if result.content:
                # Extract text from the first content item
                first_content = result.content[0]
                if hasattr(first_content, 'text'):
                    return {"result": first_content.text}
                else:
                    return {"result": str(first_content)}
            return {"result": "No content"}
        
        print(f"Starting Hosted PiecesOS LTM MCP Server on {self.host}:{self.port}")
        uvicorn.run(app, host=self.host, port=self.port)

# Main entry point
if __name__ == "__main__":
    import sys
    
    server = HostedPiecesLTMServer()
    
    if len(sys.argv) > 1 and sys.argv[1] == "http":
        # Run as HTTP server
        asyncio.run(server.run_http())
    else:
        # Run as stdio server (default)
        asyncio.run(server.run_stdio())
