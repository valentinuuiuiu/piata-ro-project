#!/usr/bin/env python3
import httpx
import asyncio

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:39300/model_context_protocol/2024-11-05/sse', timeout=5.0)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Text: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
