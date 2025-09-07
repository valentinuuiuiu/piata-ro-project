# import requests
# import json

# # Test the AI chat functionality
# def test_ai_chat():
#     # First, let's test the status endpoint (no auth required)
#     print("Testing AI status endpoint...")
#     response = requests.get('http://localhost:8009/ai/status/')
#     print(f"Status response: {response.status_code} - {response.json()}")
    
#     # Test the chat endpoint without auth
#     print("\nTesting chat endpoint without authentication...")
#     response = requests.post('http://localhost:8009/ai/chat/', 
#                            json={'message': 'Hello AI assistant!'})
#     print(f"Chat response (no auth): {response.status_code} - {response.json()}")
    
#     # Test MCP check endpoint without auth
#     print("\nTesting MCP check endpoint without authentication...")
#     response = requests.get('http://localhost:8009/ai/check-mcp/database/')
#     print(f"MCP check response (no auth): {response.status_code}")
    
#     print("\n=== Test completed ===")

# if __name__ == "__main__":
#     test_ai_chat()
