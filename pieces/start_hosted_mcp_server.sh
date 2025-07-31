#!/bin/bash
# Start the hosted PiecesOS LTM MCP Server

# Check if we're in the right directory
if [ ! -f "mcp_servers/kali_pieces_cloud_server.py" ]; then
    echo "Error: mcp_servers/kali_pieces_cloud_server.py not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if the server is already running
if pgrep -f "kali_pieces_cloud_server.py" > /dev/null; then
    echo "PiecesOS LTM MCP Server is already running."
    echo "Use 'pkill -f kali_pieces_cloud_server.py' to stop it first."
    exit 1
fi

# Start the server
echo "Starting PiecesOS LTM MCP Server on kali.pieces.cloud..."
echo "Server will be available at http://localhost:8005"
echo "Press Ctrl+C to stop the server"

# Run in background and save PID
nohup python mcp_servers/kali_pieces_cloud_server.py > mcp_server.log 2>&1 &
SERVER_PID=$!

# Save PID to file
echo $SERVER_PID > mcp_server.pid

echo "Server started with PID: $SERVER_PID"
echo "Logs are being written to mcp_server.log"
echo "PID saved to mcp_server.pid"
