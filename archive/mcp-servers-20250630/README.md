# 🚀 Awesome MCP Servers for Piața RO

This directory contains all **Model Context Protocol (MCP)** servers/agents for the Piața RO marketplace platform. Each agent is specialized for specific tasks and can be used independently or together.

## 🤖 Available Agents

### 1. 📢 Advertising Agent (`advertising_agent.py`)
**Purpose**: Marketing optimization and listing enhancement for Romanian marketplace

**Features**:
- 📝 Title optimization with SEO keywords
- 📋 Description templates for various categories
- 💰 Dynamic pricing strategy recommendations
- 📱 Social media content generation
- 📊 Market analysis and competitor insights
- ⏰ Optimal posting schedule recommendations

**Port**: 8001  
**Start**: `./start-advertising-agent.sh`

---

### 2. 🗄️ Django SQL Agent (`django_sql_agent.py`)
**Purpose**: Database operations and SQL management for Django backend

**Features**:
- 📝 Create, read, update, delete listings
- 👤 User management operations
- 🔍 Advanced search and filtering
- 📊 Category management
- 🔧 Custom SQL query execution
- 📈 Database analytics and reporting

**Port**: 8002  
**Start**: `./start-django-sql-agent.sh`

---

### 3. 📊 Stock Agent (`stock_agent.py`)
**Purpose**: Inventory and product management

**Features**:
- 📦 Stock level monitoring
- 📈 Inventory analytics
- 🔔 Low stock alerts
- 📊 Product performance tracking

**Port**: 8003  
**Start**: `python stock_agent.py`

---

### 4. 🧪 Test Advertising Agent (`test-advertising-agent.py`)
**Purpose**: Testing and development for advertising features

**Features**:
- 🧪 Test advertising algorithms
- 📊 A/B testing capabilities
- 🔧 Development and debugging tools

**Port**: 8004  
**Start**: `python test-advertising-agent.py`

## 🚀 Quick Start

### Start Individual Agents
```bash
# Start advertising agent
./start-agents.sh advertising

# Start database agent
./start-agents.sh sql

# Start stock agent
./start-agents.sh stock

# Start test agent
./start-agents.sh test
```

### Start All Agents
```bash
# Start all agents in background
./start-agents.sh all
```

### Stop All Agents
```bash
# Kill all running agents
pkill -f 'python.*agent'
```

## 📋 Agent Status Check

```bash
# Check which agents are running
ps aux | grep -E '(advertising|sql|stock).*agent'

# Check port usage
netstat -tlnp | grep -E '(8001|8002|8003|8004)'
```

## 🔧 Configuration

### Environment Variables
```bash
# Set Django settings for SQL agent
export DJANGO_SETTINGS_MODULE=piata_ro.settings

# Set database path
export DATABASE_PATH=../db.sqlite3
```

### Dependencies
All agents require:
- `fastmcp` - MCP protocol implementation
- `django` - Web framework (for SQL agent)
- `praisonai` - AI agent framework
- `httpx` - HTTP client
- `python-dotenv` - Environment management

## 🔌 MCP Client Integration

### Connect to Agents
```python
# Example: Connect to advertising agent
from mcp_client import MCPClient

client = MCPClient("http://localhost:8001")
response = client.call_tool("optimize_title", {
    "title": "Laptop de vanzare",
    "category": "Electronics",
    "location": "Bucuresti"
})
```

### Available Tools per Agent

#### Advertising Agent Tools:
- `optimize_title` - Improve listing titles
- `generate_description` - Create descriptions
- `suggest_price` - Price recommendations  
- `create_social_post` - Social media content
- `analyze_market` - Market analysis

#### Django SQL Agent Tools:
- `create_listing` - Add new listings
- `get_listings` - Retrieve listings
- `update_listing` - Modify listings
- `delete_listing` - Remove listings
- `create_user` - Add users
- `search_listings` - Search functionality

#### Stock Agent Tools:
- `check_stock` - Check inventory levels
- `update_stock` - Update quantities
- `get_low_stock` - Find low inventory items

## 📊 Monitoring & Logs

### Log Files
- `advertising_agent.log` - Advertising agent logs
- `django_sql_agent.log` - Database agent logs  
- `stock_agent.log` - Stock agent logs

### Health Checks
```bash
# Check agent health
curl http://localhost:8001/health  # Advertising
curl http://localhost:8002/health  # SQL Agent
curl http://localhost:8003/health  # Stock
```

## 🤝 Integration with Main Application

### Django Integration
The SQL agent integrates directly with the Django models:
```python
# In Django views
from awesome_mcp_servers.django_sql_agent import MCPDatabaseTools

db_tools = MCPDatabaseTools()
listings = db_tools.get_listings(category="Electronics")
```

### Frontend Integration
Use agents through API calls:
```javascript
// Call advertising agent from frontend
fetch('/api/optimize-listing/', {
    method: 'POST',
    body: JSON.stringify({
        title: "Masina de vanzare",
        category: "Auto"
    })
})
```

## 🔧 Development

### Adding New Agents
1. Create new agent file in this directory
2. Implement MCP protocol using FastMCP
3. Add start script
4. Update `start-agents.sh`
5. Document in this README

### Testing Agents
```bash
# Test individual agent
python test-advertising-agent.py

# Run integration tests
python -m pytest tests/test_mcp_agents.py
```

## 📝 Notes

- All agents run independently and can be scaled separately
- Use environment variables for configuration
- Each agent has its own port to avoid conflicts
- Logs are stored in the main project directory
- Agents can communicate with each other through MCP protocol

---

**🇷🇴 Built for Piața RO** - Romanian Marketplace Platform  
*Powered by MCP (Model Context Protocol) and AI Agents* 🤖
