

from fastapi import FastAPI
from FASTmcp.app.sql_agent import SQLAgent
from FASTmcp.app.inventory import InventorySystem

app = FastAPI()
sql_agent = SQLAgent()
inventory = InventorySystem()

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
        
    return {"error": "Unknown action"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

