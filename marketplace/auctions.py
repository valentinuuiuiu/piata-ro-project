

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class AuctionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def broadcast(self, item_id: str, message: str):
        if ws := self.active_connections.get(item_id):
            await ws.send_text(message)

manager = AuctionManager()

@app.websocket("/auctions/{item_id}")
async def auction_endpoint(websocket: WebSocket, item_id: str):
    await websocket.accept()
    manager.active_connections[item_id] = websocket
    
    try:
        while True:
            bid = await websocket.receive_text()
            await manager.broadcast(item_id, f"New bid: {bid}")
    except WebSocketDisconnect:
        del manager.active_connections[item_id]

