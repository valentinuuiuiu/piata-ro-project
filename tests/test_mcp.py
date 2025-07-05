

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from FASTmcp.app.main import app
from FASTmcp.app.sql_agent import SQLAgent
from FASTmcp.app.inventory import InventorySystem

client = TestClient(app)

def test_mcp_commands():
    # Test inventory system
    response = client.post("/mcp", json={
        "action": "inventory_update",
        "item_id": "test123",
        "data": {"name": "Test Item", "stock": 100}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Test SQL agent (mock test)
    response = client.post("/mcp", json={
        "action": "sql_query",
        "query": "SELECT 1"
    })
    assert response.status_code == 200
    assert "data" in response.json()

    # Test ban command
    response = client.post("/mcp", json={
        "action": "ban_user",
        "user_id": "user123"
    })
    assert response.status_code == 200
    assert "Banned user123" in response.json()["status"]

