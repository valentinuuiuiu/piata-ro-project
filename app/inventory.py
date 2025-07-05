


from typing import Dict, Any
from pydantic import BaseModel

class ItemModel(BaseModel):
    item_id: str
    name: str
    stock: int
    metadata: Dict[str, Any] = {}

class InventorySystem:
    def __init__(self):
        self.items: Dict[str, ItemModel] = {}
        
    def update(self, item_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Update or create inventory item"""
        if item_id in self.items:
            self.items[item_id] = ItemModel(**{**self.items[item_id].dict(), **data})
        else:
            self.items[item_id] = ItemModel(item_id=item_id, **data)
        return {"status": "success", "item_id": item_id}
    
    def get(self, item_id: str) -> Dict[str, Any]:
        """Retrieve item data"""
        if item_id in self.items:
            return self.items[item_id].dict()
        return {"error": "Item not found"}


