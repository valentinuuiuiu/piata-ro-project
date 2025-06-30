#!/bin/bash

# Start Piața.ro Advertising Helper Agent
# This script starts the MCP server for advertising assistance

echo "🚀 Starting Piața.ro Advertising Helper Agent..."

# Change to project directory
cd /home/shiva/Desktop/piata-ro-project

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Creating basic .env file..."
    echo "DATABASE_PATH=db.sqlite3" > .env
fi

# Change to MCP servers directory
cd awesome-mcp-servers

# Start the MCP server
echo "🎯 Advertising Helper Agent is now running on Port 8001!"
echo "📈 Available tools:"
echo "   • optimize_listing_title - Optimize titles for better visibility"
echo "   • generate_description_template - Create professional descriptions"
echo "   • suggest_pricing_strategy - Get optimal pricing recommendations"
echo "   • generate_promotional_content - Create social media content"
echo "   • analyze_competitor_pricing - Market analysis and insights"
echo "   • suggest_best_posting_times - Optimal posting schedule"
echo ""
echo "📚 Resources available:"
echo "   • advertising://templates - Advertising templates & best practices"
echo "   • advertising://analytics - Performance analytics & insights"
echo ""
echo "Press Ctrl+C to stop the agent"
echo "----------------------------------------"

python advertising-agent.py --port 8001
