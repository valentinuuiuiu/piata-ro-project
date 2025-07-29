
#!/bin/bash

# Script to start MCP agents
echo "Starting MCP agents..."

# Add the project directory to Python path
export PYTHONPATH="/workspace/piata-ro-project:$PYTHONPATH"

# Start SQL agent in background
echo "Starting SQL Agent on port 8002..."
cd /workspace/piata-ro-project/mcp_agents/sql_agent && python3 main.py > sql_agent.log 2>&1 &

# Start Marketing agent in background
echo "Starting Marketing Agent on port 8001..."
cd /workspace/piata-ro-project/mcp_agents/marketing_agent && python3 main.py > marketing_agent.log 2>&1 &

echo "MCP agents started. Check logs for details."
echo "SQL Agent log: /workspace/piata-ro-project/mcp_agents/sql_agent/sql_agent.log"
echo "Marketing Agent log: /workspace/piata-ro-project/mcp_agents/marketing_agent/marketing_agent.log"

# Wait for a moment to allow servers to start
sleep 5

# Check if servers are running
echo "Checking if servers are running..."
ps aux | grep main.py

