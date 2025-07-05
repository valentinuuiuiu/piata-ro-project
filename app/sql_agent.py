


from sqlalchemy import create_engine, text
from typing import Dict, List

class SQLAgent:
    def __init__(self):
        self.engine = create_engine("sqlite:///mcp.db")
        
    async def execute(self, query: str) -> Dict[str, List]:
        """Execute SQL query and return JSON-friendly results"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                return {
                    "success": True,
                    "data": [dict(row._mapping) for row in result]
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


