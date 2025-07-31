from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class AuctionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def handle_connection(self, websocket: WebSocket, item_id: str):
        await websocket.accept()
        self.active_connections[item_id] = websocket
        
        try:
            while True:
                bid = await websocket.receive_text()
                await self.broadcast(item_id, f"New bid: {bid}")
        except WebSocketDisconnect:
            if item_id in self.active_connections:
                del self.active_connections[item_id]

    async def broadcast(self, item_id: str, message: str):
        if item_id in self.active_connections:
            websocket = self.active_connections[item_id]
            await websocket.send_text(message)

manager = AuctionManager()
