#!/usr/bin/env python3
import asyncio
import json
import httpx

async def connect_to_pieces_mcp():
    """Connect to PiecesOS MCP server and list available tools"""
    
    print("Attempting to connect to PiecesOS MCP...")
    print("PiecesOS MCP SSE endpoint: http://localhost:39300/model_context_protocol/2024-11-05/sse")
    print("Messages endpoint: http://localhost:39300/model_context_protocol/2024-11-05/messages")
    
    # Test connection to the SSE endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:39300/model_context_protocol/2024-11-05/sse")
            print(f"SSE endpoint status: {response.status_code}")
            if response.status_code == 200:
                print("Successfully connected to PiecesOS MCP SSE endpoint!")
                # Read a small portion of the response
                content = response.text[:200]
                print(f"Response preview: {content}")
            else:
                print(f"Failed to connect to SSE endpoint. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error connecting to PiecesOS MCP SSE endpoint: {e}")
    
    print("\nTo properly use PiecesOS LTM with MCP, you would:")
    print("1. Connect to the MCP server using the proper MCP client library")
    print("2. Use the 'ask_pieces_ltm' tool to query your long-term memory")
    print("3. The LTM engine would search your context and return relevant results")
    
    # Example of what the LTM query might look like:
    print("\nExample LTM query (conceptual):")
    print('Tool: "ask_pieces_ltm"')
    print('Arguments: {"query": "What did I work on yesterday?", "context": "development"}')
    print('Expected result: Relevant memories from your PiecesOS LTM')
    
    return True

if __name__ == "__main__":
    asyncio.run(connect_to_pieces_mcp())
