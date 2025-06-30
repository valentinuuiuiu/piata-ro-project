#!/bin/bash

# Master MCP Agents Launcher for Piața RO
# This script helps you start individual or all MCP agents

echo "🚀 Piața RO - MCP Agents Control Center"
echo "========================================"
echo ""

show_help() {
    echo "Available MCP Agents:"
    echo "1. 📢 Advertising Agent - Marketing and listing optimization"
    echo "2. 📊 Stock Agent - Inventory and product management"  
    echo "3. 🗄️  Django SQL Agent - Database operations"
    echo "4. 🧪 Test Advertising Agent - Testing and development"
    echo ""
    echo "Usage:"
    echo "  $0 [agent_name|all|help]"
    echo ""
    echo "Examples:"
    echo "  $0 advertising    # Start advertising agent"
    echo "  $0 sql           # Start Django SQL agent"
    echo "  $0 stock         # Start stock agent"
    echo "  $0 test          # Start test advertising agent"
    echo "  $0 all           # Start all agents (in background)"
    echo "  $0 help          # Show this help"
    echo ""
}

start_advertising_agent() {
    echo "🚀 Starting Advertising Agent..."
    ./start-advertising-agent.sh
}

start_sql_agent() {
    echo "🚀 Starting Django SQL Agent..."
    ./start-django-sql-agent.sh
}

start_stock_agent() {
    echo "🚀 Starting Stock Agent..."
    ./start-stock-agent.sh
}

start_test_agent() {
    echo "🚀 Starting Test Advertising Agent..."
    python test-advertising-agent.py
}

start_all_agents() {
    echo "🚀 Starting All MCP Agents..."
    echo "📢 Starting Advertising Agent (Port 8001)..."
    ./start-advertising-agent.sh &
    sleep 2
    
    echo "🗄️  Starting Django SQL Agent (Port 8002)..."
    ./start-django-sql-agent.sh &
    sleep 2
    
    echo "📊 Starting Stock Agent (Port 8003)..."
    python stock_agent.py &
    sleep 2
    
    echo ""
    echo "✅ All agents started in background!"
    echo "📊 Agent Status:"
    echo "   - Advertising Agent: http://localhost:8001"
    echo "   - Django SQL Agent: http://localhost:8002" 
    echo "   - Stock Agent: http://localhost:8003"
    echo ""
    echo "🛑 To stop all agents: pkill -f 'python.*agent'"
}

# Main logic
case "$1" in
    "advertising"|"ad"|"ads")
        start_advertising_agent
        ;;
    "sql"|"database"|"db")
        start_sql_agent
        ;;
    "stock"|"inventory")
        start_stock_agent
        ;;
    "test"|"testing")
        start_test_agent
        ;;
    "all"|"start-all")
        start_all_agents
        ;;
    "help"|"-h"|"--help"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown agent: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
