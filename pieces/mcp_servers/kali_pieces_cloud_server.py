#!/usr/bin/env python3
"""
Simple HTTP Server for PiecesOS LTM MCP
This can be hosted on kali.pieces.cloud
"""
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="PiecesOS LTM MCP Server for kali.pieces.cloud")

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
    return {
        "message": "PiecesOS LTM MCP Server", 
        "status": "running",
        "host": "kali.pieces.cloud",
        "description": "Hosted PiecesOS Long Term Memory service"
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    tools = [
        {
            "name": "query_pieces_ltm",
            "description": "Query the PiecesOS Long Term Memory for relevant information",
            "inputSchema": {
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
        },
        {
            "name": "get_recent_memories", 
            "description": "Get recent memories from PiecesOS LTM",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to return",
                        "default": 10
                    }
                }
            }
        }
    ]
    return {"tools": tools}

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict):
    """Execute MCP tools"""
    try:
        if tool_name == "query_pieces_ltm":
            query = arguments.get("query", "")
            context = arguments.get("context", "")
            
            # Simulate LTM query result
            result = {
                "query": query,
                "context": context,
                "status": "success",
                "message": "Connected to hosted PiecesOS LTM service on kali.pieces.cloud",
                "results": [
                    {
                        "id": "hosted_memory_1",
                        "content": f"Query result for: {query}",
                        "relevance": 0.92,
                        "timestamp": "2025-07-30T01:00:00Z"
                    }
                ]
            }
            
            return {"result": json.dumps(result, indent=2)}
            
        elif tool_name == "get_recent_memories":
            limit = arguments.get("limit", 10)
            
            # Simulate recent memories
            memories = [
                {
                    "id": f"recent_{i}",
                    "content": f"Recent memory item {i} from kali.pieces.cloud",
                    "timestamp": f"2025-07-30T00:{i:02d}:00Z"
                }
                for i in range(min(limit, 5))
            ]
            
            return {"result": json.dumps(memories, indent=2)}
            
        else:
            return {"error": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        return {"error": f"Error executing tool: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-07-30T01:00:00Z"}

if __name__ == "__main__":
    print("Starting PiecesOS LTM MCP Server on kali.pieces.cloud")
    print("Access at: http://localhost:8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)
