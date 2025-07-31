from fastapi import FastAPI, WebSocket
from .sql_agent import SQLAgent
from .inventory import InventorySystem
from marketplace.ai_search.core import router as ai_router
from marketplace.auctions import manager as auction_manager
import httpx

app = FastAPI()
app.include_router(ai_router, prefix="/ai")
sql_agent = SQLAgent()
inventory = InventorySystem()

@app.websocket("/ws/auctions/{item_id}")
async def websocket_auction(websocket: WebSocket, item_id: str):
    await auction_manager.handle_connection(websocket, item_id)

@app.post("/mcp")
async def handle_command(cmd: dict):
    """Unified MCP command handler"""
    action = cmd.get("action")
    
    # Database commands
    if action == "sql_query":
        return await sql_agent.execute(cmd["query"])
    
    # Inventory commands    
    elif action == "inventory_update":
        return inventory.update(cmd["item_id"], cmd["data"])
    
    # Moderation commands
    elif action == "ban_user":
        return {"status": f"Banned {cmd['user_id']}"}
    
    # System commands    
    elif action == "restart_service":
        return {"status": f"Restarted {cmd['service']}"}

    # AI Search commands
    elif action == "ai_search":
        # For now, we'll return a simple response since we can't directly call the route handler
        # In a real implementation, you might want to restructure this
        return {"status": "AI search command received", "query": cmd["query"]}

    # Auction commands
    elif action == "auction_broadcast":
        await auction_manager.broadcast(cmd["item_id"], cmd["message"])
        return {"status": "Broadcast sent"}
        
    return {"error": "Unknown action"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
