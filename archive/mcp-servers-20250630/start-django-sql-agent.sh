#!/bin/bash

# Start Django SQL Agent MCP Server
# This script starts the Django SQL Agent for database operations

echo "🚀 Starting Django SQL Agent MCP Server..."
echo "📍 Location: awesome-mcp-servers/django_sql_agent.py"
echo "🔗 Purpose: Database operations and SQL management for Piața RO"

# Check if virtual environment exists
if [ -d "../venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Please create one with: python -m venv venv"
    exit 1
fi

# Check if required dependencies are installed
python -c "import django, fastmcp, sqlite3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required dependencies..."
    pip install django fastmcp
fi

# Set Django settings module and Python path
export DJANGO_SETTINGS_MODULE=piata_ro.settings
export PYTHONPATH="../:$PYTHONPATH"

# Change to parent directory to access Django project
cd ..

# Start the Django SQL Agent
echo "🔥 Starting Django SQL Agent on port 8002..."
python awesome-mcp-servers/django_sql_agent.py

echo "✅ Django SQL Agent started successfully!"
echo "🔌 Available MCP tools:"
echo "   - create_listing"
echo "   - get_listings" 
echo "   - update_listing"
echo "   - delete_listing"
echo "   - create_user"
echo "   - get_users"
echo "   - search_listings"
echo "   - get_categories"
echo "   - execute_custom_query"
echo ""
echo "📝 Usage: Connect your MCP client to this server for database operations"
