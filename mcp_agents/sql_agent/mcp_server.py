#!/usr/bin/env python3
"""
MCP Server for SQL Agent
Provides database query capabilities through MCP protocol
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
import django
django.setup()

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from marketplace.models import Listing, Category, UserProfile
from django.db import connection
from django.db.models import Count, Avg, Sum

class SQLAgentMCPServer:
    def __init__(self):
        self.name = "sql-agent"
        self.version = "1.0.0"

    async def run(self):
        server = Server(self.name)

        @server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available SQL tools."""
            return [
                types.Tool(
                    name="execute_sql_query",
                    description="Execute a raw SQL query on the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_listing_stats",
                    description="Get marketplace listing statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Category name to filter by (optional)"
                            },
                            "status": {
                                "type": "string",
                                "description": "Listing status (active, sold, expired)",
                                "enum": ["active", "sold", "expired"]
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_user_analytics",
                    description="Get user analytics and statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID to get analytics for (optional)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_category_summary",
                    description="Get summary of all categories with listing counts",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any] | None
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool calls."""
            if name == "execute_sql_query":
                return await self.execute_sql_query(arguments or {})
            elif name == "get_listing_stats":
                return await self.get_listing_stats(arguments or {})
            elif name == "get_user_analytics":
                return await self.get_user_analytics(arguments or {})
            elif name == "get_category_summary":
                return await self.get_category_summary(arguments or {})
            else:
                raise ValueError(f"Unknown tool: {name}")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=self.name,
                    server_version=self.version,
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    async def execute_sql_query(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute a raw SQL query."""
        query = arguments.get("query", "")
        if not query:
            return [types.TextContent(type="text", text="Error: No query provided")]

        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                
                if query.strip().upper().startswith("SELECT"):
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    result = {
                        "columns": columns,
                        "rows": [list(row) for row in rows],
                        "count": len(rows)
                    }
                else:
                    result = {
                        "affected_rows": cursor.rowcount,
                        "message": "Query executed successfully"
                    }
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error executing query: {str(e)}")]

    async def get_listing_stats(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get marketplace listing statistics."""
        category = arguments.get("category")
        status = arguments.get("status")
        
        try:
            queryset = Listing.objects.all()
            
            if category:
                queryset = queryset.filter(category__name__icontains=category)
            
            if status:
                queryset = queryset.filter(status=status)
            
            stats = queryset.aggregate(
                total_listings=Count('id'),
                avg_price=Avg('price'),
                total_value=Sum('price')
            )
            
            result = {
                "total_listings": stats["total_listings"] or 0,
                "average_price": float(stats["avg_price"]) if stats["avg_price"] else 0,
                "total_value": float(stats["total_value"]) if stats["total_value"] else 0,
                "filters": {
                    "category": category,
                    "status": status
                }
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting listing stats: {str(e)}")]

    async def get_user_analytics(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get user analytics and statistics."""
        user_id = arguments.get("user_id")
        
        try:
            if user_id:
                user = UserProfile.objects.get(id=user_id)
                listings = Listing.objects.filter(seller=user)
                
                result = {
                    "user_id": user_id,
                    "username": user.user.username,
                    "total_listings": listings.count(),
                    "active_listings": listings.filter(status='active').count(),
                    "sold_listings": listings.filter(status='sold').count(),
                    "total_sales": listings.filter(status='sold').aggregate(
                        total=Sum('price')
                    )['total'] or 0
                }
            else:
                total_users = UserProfile.objects.count()
                users_with_listings = UserProfile.objects.filter(
                    listing__isnull=False
                ).distinct().count()
                
                result = {
                    "total_users": total_users,
                    "users_with_listings": users_with_listings,
                    "users_without_listings": total_users - users_with_listings
                }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting user analytics: {str(e)}")]

    async def get_category_summary(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get summary of all categories with listing counts."""
        try:
            categories = Category.objects.annotate(
                listing_count=Count('listing')
            ).values('name', 'listing_count', 'description')
            
            result = {
                "categories": list(categories),
                "total_categories": len(categories),
                "categories_with_listings": len([c for c in categories if c['listing_count'] > 0])
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error getting category summary: {str(e)}")]


async def main():
    """Main entry point for the SQL agent MCP server."""
    server = SQLAgentMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
