#!/usr/bin/env python3
"""
Pieces LTM (Long-Term Memory) MCP Server
Provides persistent memory storage and retrieval capabilities for AI agents
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'pieces_ltm.db')

class PiecesLTMServer:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
        
    def init_database(self):
        """Initialize the SQLite database for long-term memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        ''')
        
        # Create tags table for categorization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER,
                tag TEXT NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES memories (id)
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag)')
        
        conn.commit()
        conn.close()
    
    def store_memory(self, key: str, value: str, metadata: Dict[str, Any] = None, tags: List[str] = None) -> bool:
        """Store a memory with optional metadata and tags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO memories (key, value, metadata, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, metadata_json))
            
            memory_id = cursor.lastrowid
            
            # Store tags if provided
            if tags:
                cursor.execute('DELETE FROM tags WHERE memory_id = ?', (memory_id,))
                for tag in tags:
                    cursor.execute('INSERT INTO tags (memory_id, tag) VALUES (?, ?)', (memory_id, tag))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False
    
    def retrieve_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory by key"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, key, value, metadata, created_at, updated_at, access_count
                FROM memories WHERE key = ?
            ''', (key,))
            
            row = cursor.fetchone()
            if row:
                # Update access count
                cursor.execute('UPDATE memories SET access_count = access_count + 1 WHERE id = ?', (row[0],))
                conn.commit()
                
                # Get tags
                cursor.execute('SELECT tag FROM tags WHERE memory_id = ?', (row[0],))
                tags = [tag[0] for tag in cursor.fetchall()]
                
                conn.close()
                
                return {
                    'id': row[0],
                    'key': row[1],
                    'value': row[2],
                    'metadata': json.loads(row[3]) if row[3] else None,
                    'created_at': row[4],
                    'updated_at': row[5],
                    'access_count': row[6] + 1,
                    'tags': tags
                }
            
            conn.close()
            return None
        except Exception as e:
            print(f"Error retrieving memory: {e}")
            return None
    
    def search_memories(self, query: str, tags: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by content or tags"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            sql = '''
                SELECT DISTINCT m.id, m.key, m.value, m.metadata, m.created_at, m.updated_at, m.access_count
                FROM memories m
            '''
            params = []
            
            conditions = []
            if query:
                conditions.append('(m.key LIKE ? OR m.value LIKE ?)')
                params.extend([f'%{query}%', f'%{query}%'])
            
            if tags:
                sql += ' JOIN tags t ON m.id = t.memory_id'
                tag_conditions = ' OR '.join(['t.tag = ?' for _ in tags])
                conditions.append(f'({tag_conditions})')
                params.extend(tags)
            
            if conditions:
                sql += ' WHERE ' + ' AND '.join(conditions)
            
            sql += ' ORDER BY m.updated_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Get tags for each memory
                cursor.execute('SELECT tag FROM tags WHERE memory_id = ?', (row[0],))
                memory_tags = [tag[0] for tag in cursor.fetchall()]
                
                results.append({
                    'id': row[0],
                    'key': row[1],
                    'value': row[2],
                    'metadata': json.loads(row[3]) if row[3] else None,
                    'created_at': row[4],
                    'updated_at': row[5],
                    'access_count': row[6],
                    'tags': memory_tags
                })
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    def delete_memory(self, key: str) -> bool:
        """Delete a memory by key"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM memories WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                memory_id = row[0]
                cursor.execute('DELETE FROM tags WHERE memory_id = ?', (memory_id,))
                cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
                conn.commit()
            
            conn.close()
            return row is not None
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False
    
    def list_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all memories with pagination"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, key, value, metadata, created_at, updated_at, access_count
                FROM memories
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Get tags for each memory
                cursor.execute('SELECT tag FROM tags WHERE memory_id = ?', (row[0],))
                tags = [tag[0] for tag in cursor.fetchall()]
                
                results.append({
                    'id': row[0],
                    'key': row[1],
                    'value': row[2][:100] + '...' if len(row[2]) > 100 else row[2],
                    'metadata': json.loads(row[3]) if row[3] else None,
                    'created_at': row[4],
                    'updated_at': row[5],
                    'access_count': row[6],
                    'tags': tags
                })
            
            conn.close()
            return results
        except Exception as e:
            print(f"Error listing memories: {e}")
            return []

# Initialize the server
ltm_server = PiecesLTMServer()
server = Server("pieces-ltm")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for the Pieces LTM server"""
    return [
        Tool(
            name="store_memory",
            description="Store a memory with a key, value, and optional metadata/tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Unique identifier for the memory"},
                    "value": {"type": "string", "description": "The content to store"},
                    "metadata": {"type": "object", "description": "Additional metadata as JSON object"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                },
                "required": ["key", "value"]
            }
        ),
        Tool(
            name="retrieve_memory",
            description="Retrieve a memory by its key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key of the memory to retrieve"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="search_memories",
            description="Search memories by content or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for memory content"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
                }
            }
        ),
        Tool(
            name="delete_memory",
            description="Delete a memory by its key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "The key of the memory to delete"}
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="list_memories",
            description="List all memories with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50}
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for the Pieces LTM server"""
    
    if name == "store_memory":
        key = arguments.get("key")
        value = arguments.get("value")
        metadata = arguments.get("metadata")
        tags = arguments.get("tags", [])
        
        success = ltm_server.store_memory(key, value, metadata, tags)
        
        if success:
            return [types.TextContent(type="text", text=f"Memory stored successfully with key: {key}")]
        else:
            return [types.TextContent(type="text", text=f"Failed to store memory with key: {key}")]
    
    elif name == "retrieve_memory":
        key = arguments.get("key")
        memory = ltm_server.retrieve_memory(key)
        
        if memory:
            return [types.TextContent(type="text", text=json.dumps(memory, indent=2, default=str))]
        else:
            return [types.TextContent(type="text", text=f"No memory found with key: {key}")]
    
    elif name == "search_memories":
        query = arguments.get("query", "")
        tags = arguments.get("tags", [])
        limit = arguments.get("limit", 10)
        
        memories = ltm_server.search_memories(query, tags, limit)
        
        if memories:
            return [types.TextContent(type="text", text=json.dumps(memories, indent=2, default=str))]
        else:
            return [types.TextContent(type="text", text="No memories found matching the criteria")]
    
    elif name == "delete_memory":
        key = arguments.get("key")
        deleted = ltm_server.delete_memory(key)
        
        if deleted:
            return [types.TextContent(type="text", text=f"Memory deleted successfully: {key}")]
        else:
            return [types.TextContent(type="text", text=f"No memory found with key: {key}")]
    
    elif name == "list_memories":
        limit = arguments.get("limit", 50)
        memories = ltm_server.list_memories(limit)
        
        if memories:
            return [types.TextContent(type="text", text=json.dumps(memories, indent=2, default=str))]
        else:
            return [types.TextContent(type="text", text="No memories found")]
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Main entry point for the Pieces LTM server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="pieces-ltm",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
