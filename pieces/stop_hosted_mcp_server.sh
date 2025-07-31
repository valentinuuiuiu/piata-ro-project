#!/bin/bash
# Stop the hosted PiecesOS LTM MCP Server

# Check if PID file exists
if [ ! -f "mcp_server.pid" ]; then
    echo "PID file not found. Checking for running processes..."
    
    # Check if server is running
    if pgrep -f "kali_pieces_cloud_server.py" > /dev/null; then
        echo "Server is running. Stopping it..."
        pkill -f "kali_pieces_cloud_server.py"
        echo "Server stopped."
    else
        echo "Server is not running."
    fi
    exit 0
fi

# Read PID from file
SERVER_PID=$(cat mcp_server.pid)

# Check if process is still running
if ps -p $SERVER_PID > /dev/null; then
    echo "Stopping PiecesOS LTM MCP Server (PID: $SERVER_PID)..."
    kill $SERVER_PID
    
    # Wait a moment for graceful shutdown
    sleep 2
    
    # Check if it's still running
    if ps -p $SERVER_PID > /dev/null; then
        echo "Server didn't stop gracefully. Forcing termination..."
        kill -9 $SERVER_PID
    fi
    
    echo "Server stopped."
else
    echo "Server process (PID: $SERVER_PID) is not running."
fi

# Remove PID file
rm -f mcp_server.pid
echo "PID file removed."
