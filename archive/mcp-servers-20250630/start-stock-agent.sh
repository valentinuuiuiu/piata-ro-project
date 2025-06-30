#!/bin/bash

# Start script for Stock Agent

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR") # Assumes awesome-mcp-servers is one level down from project root

echo "🚀 Starting Stock Agent..."

# Activate virtual environment
# Adjust the path to your virtual environment if it's different
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "🐍 Activating virtual environment from $PROJECT_ROOT/.venv..."
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -d "$PROJECT_ROOT/venv" ]; then # Common alternative
    echo "🐍 Activating virtual environment from $PROJECT_ROOT/venv..."
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo "⚠️ Virtual environment not found at $PROJECT_ROOT/.venv or $PROJECT_ROOT/venv. Please ensure it is created and activated."
    # exit 1 # Optionally exit if venv is critical
fi

# Navigate to the directory where the agent script is located
cd "$SCRIPT_DIR"

# Run the Stock Agent on port 8003
# Ensure stock_agent.py is executable or called with python
python stock_agent.py --port 8003

echo "✅ Stock Agent started/attempted to start."
