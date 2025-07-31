#!/usr/bin/env python3
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    Resource,
    ListToolsResult,
    CallToolResult,
    ListResourcesResult,
    ReadResourceResult,
)
import pieces_os_client
from pieces_os_client.api_client import ApiClient
from pieces_os_client.configuration import Configuration

class PiecesLTMServer:
    def __init__(self):
        # Configure the Pieces OS client
        self.configuration = Configuration(
            host="http://localhost:1000"  # Default Pieces OS port
        )
        
        # Create API client
        self.api_client = ApiClient(self.configuration)
        
        # Initialize the MCP server
        self.server = Server("pieces-ltm-server")
        
        # Register handlers
        self.server.list_tools(self.list_tools)
        self.server.call_tool(self.call_tool)
        self.server.list_resources(self.list_resources)
        self.server.read_resource(self.read_resource)
        
    async def list_tools(self) -> ListToolsResult:
        """List available tools for LTM operations"""
        return ListToolsResult(
            tools=[
                Tool(
                    name="query_ltm",
                    description="Query the PiecesOS Long Term Memory for relevant information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to search for in LTM"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="store_memory",
                    description="Store information in PiecesOS Long Term Memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The content to store in LTM"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Optional metadata for the memory",
                                "properties": {
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "context": {
                                        "type": "string"
                                    }
                                }
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="list_memories",
                    description="List recent memories from PiecesOS LTM",
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
            if name == "query_ltm":
                query = arguments.get("query", "")
                # Use Pieces OS API to search LTM
                result = await self.query_pieces_ltm(query)
                return CallToolResult(
                    content=[{"type": "text", "text": json.dumps(result, indent=2)}]
                )
                
            elif name == "store_memory":
                content = arguments.get("content", "")
                metadata = arguments.get("metadata", {})
                # Store in Pieces OS LTM
                result = await self.store_pieces_memory(content, metadata)
                return CallToolResult(
                    content=[{"type": "text", "text": json.dumps(result, indent=2)}]
                )
                
            elif name == "list_memories":
                limit = arguments.get("limit", 10)
                # List memories from Pieces OS
                result = await self.list_pieces_memories(limit)
                return CallToolResult(
                    content=[{"type": "text", "text": json.dumps(result, indent=2)}]
                )
                
            else:
                return CallToolResult(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    isError=True
                )
                
        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error executing tool: {str(e)}"}],
                isError=True
            )
    
    async def list_resources(self) -> ListResourcesResult:
        """List available LTM resources"""
        return ListResourcesResult(
            resources=[
                Resource(
                    uri="ltm://recent",
                    name="Recent LTM Entries",
                    description="Recently stored memories in PiecesOS LTM",
                    mimeType="application/json"
                ),
                Resource(
                    uri="ltm://tags",
                    name="LTM Tags",
                    description="Available tags in PiecesOS LTM",
                    mimeType="application/json"
                )
            ]
        )
    
    async def read_resource(self, uri: str) -> ReadResourceResult:
        """Read LTM resources"""
        try:
            if uri == "ltm://recent":
                # Get recent memories
                memories = await self.list_pieces_memories(20)
                return ReadResourceResult(
                    contents=[{
                        "uri": uri,
                        "text": json.dumps(memories, indent=2),
                        "mimeType": "application/json"
                    }]
                )
                
            elif uri == "ltm://tags":
                # Get available tags
                tags = await self.get_pieces_tags()
                return ReadResourceResult(
                    contents=[{
                        "uri": uri,
                        "text": json.dumps(tags, indent=2),
                        "mimeType": "application/json"
                    }]
                )
                
            else:
                return ReadResourceResult(
                    contents=[{
                        "uri": uri,
                        "text": f"Unknown resource: {uri}",
                        "mimeType": "text/plain"
                    }]
                )
                
        except Exception as e:
            return ReadResourceResult(
                contents=[{
                    "uri": uri,
                    "text": f"Error reading resource: {str(e)}",
                    "mimeType": "text/plain"
                }]
            )
    
    async def query_pieces_ltm(self, query: str) -> dict:
        """Query PiecesOS LTM using the API"""
        # This is a simplified implementation
        # In a real implementation, you would use the actual Pieces OS API
        try:
            # Import the specific API classes we need
            from pieces_os_client.api.search_api import SearchApi
            from pieces_os_client.models.searched_assets import SearchedAssets
            
            # Create search API instance
            search_api = SearchApi(self.api_client)
            
            # Perform search (this is a simplified example)
            # In practice, you would need to implement the proper search logic
            result = {
                "query": query,
                "status": "connected",
                "message": "PiecesOS LTM connection established - search functionality would be implemented here"
            }
            
            return result
        except Exception as e:
            return {
                "query": query,
                "status": "error",
                "error": str(e)
            }
    
    async def store_pieces_memory(self, content: str, metadata: dict) -> dict:
        """Store memory in PiecesOS LTM"""
        try:
            # Import the assets API
            from pieces_os_client.api.assets_api import AssetsApi
            from pieces_os_client.models.seeded_asset import SeededAsset
            
            # Create assets API instance
            assets_api = AssetsApi(self.api_client)
            
            # Create a seeded asset (simplified)
            seeded_asset = SeededAsset(
                # In a real implementation, you would properly structure the asset
            )
            
            result = {
                "content": content,
                "metadata": metadata,
                "status": "stored",
                "message": "Memory would be stored in PiecesOS LTM - implementation would be completed here"
            }
            
            return result
        except Exception as e:
            return {
                "content": content,
                "status": "error",
                "error": str(e)
            }
    
    async def list_pieces_memories(self, limit: int) -> list:
        """List recent memories from PiecesOS LTM"""
        try:
            # Import the assets API
            from pieces_os_client.api.assets_api import AssetsApi
            
            # Create assets API instance
            assets_api = AssetsApi(self.api_client)
            
            # Get assets snapshot (simplified)
            # In a real implementation, you would filter and format the results properly
            memories = [
                {"id": f"memory_{i}", "content": f"Sample memory {i}", "timestamp": "2025-07-29T20:00:00Z"}
                for i in range(min(limit, 5))
            ]
            
            return memories
        except Exception as e:
            return [{"error": str(e)}]
    
    async def get_pieces_tags(self) -> list:
        """Get available tags from PiecesOS LTM"""
        try:
            # This would be implemented to fetch actual tags from PiecesOS
            tags = ["work", "development", "research", "meeting", "todo"]
            return tags
        except Exception as e:
            return [{"error": str(e)}]
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, app=self)

# Main entry point
if __name__ == "__main__":
    server = PiecesLTMServer()
    asyncio.run(server.run())
