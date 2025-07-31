#!/usr/bin/env python3
import asyncio
import json
import httpx

async def test_pieces_mcp():
    """Test connection to PiecesOS MCP server"""
    # PiecesOS MCP endpoint
    mcp_url = "http://localhost:39300/model_context_protocol/2024-11-05/messages"
    
    print(f"Testing connection to PiecesOS MCP at {mcp_url}")
    
    try:
        # Test basic connection
        async with httpx.AsyncClient() as client:
            response = await client.get(mcp_url)
            print(f"Connection status: {response.status_code}")
            if response.status_code == 200:
                print("Successfully connected to PiecesOS MCP!")
                print("Response headers:", dict(response.headers))
            else:
                print(f"Failed to connect. Status code: {response.status_code}")
                print("Response:", response.text[:200])
    except Exception as e:
        print(f"Error connecting to PiecesOS MCP: {e}")

if __name__ == "__main__":
    asyncio.run(test_pieces_mcp())
