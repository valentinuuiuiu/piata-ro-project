# Complete PiecesOS MCP Integration Documentation

## Overview

This document provides a comprehensive overview of the PiecesOS MCP (Model Context Protocol) integration that has been implemented for the piata-ro-project. The integration includes local LTM (Long Term Memory) capabilities, cloud hosting, and full deployment infrastructure.

## Table of Contents

1. [PiecesOS Local Integration](#piecesos-local-integration)
2. [Hosted MCP Server](#hosted-mcp-server)
3. [Nginx Proxy Configuration](#nginx-proxy-configuration)
4. [Deployment Infrastructure](#deployment-infrastructure)
5. [Management Scripts](#management-scripts)
6. [Testing and Verification](#testing-and-verification)
7. [File Structure](#file-structure)

## PiecesOS Local Integration

### Status
✅ **PiecesOS is running** on `localhost:39300` with MCP capabilities enabled.

### Verification
```bash
curl -m 5 http://localhost:39300/model_context_protocol/2024-11-05/sse
```

Response:
```
event: endpoint
data: /model_context_protocol/2024-11-05/messages
```

### Integration Methods
1. **IDE Integration** (Recommended)
   - Connect your IDE (Cursor, VSCode) to `http://localhost:39300`
   - Use the `ask_pieces_ltm` tool for context-rich queries

2. **Direct API Access**
   - Connect to the MCP messages endpoint
   - Use the MCP protocol to communicate with PiecesOS

3. **Pieces Desktop App**
   - Use the Pieces Desktop Application for UI-based LTM management

## Hosted MCP Server

### Server Details
- **File**: `mcp_servers/kali_pieces_cloud_server.py`
- **Local Port**: 8005
- **Host**: `kali.pieces.cloud`
- **Status**: ✅ Running and accessible

### Available MCP Tools
1. **query_pieces_ltm**
   - Query the PiecesOS Long Term Memory for relevant information
   - Parameters: `query` (required), `context` (optional)

2. **get_recent_memories**
   - Get recent memories from PiecesOS LTM
   - Parameters: `limit` (optional, default: 10)

### Endpoints
- `GET /` - Server info and health check
- `GET /tools` - List available MCP tools
- `POST /tools/{tool_name}` - Execute MCP tools
- `GET /health` - Health check endpoint

## Nginx Proxy Configuration

### Configuration
The Nginx proxy forwards requests from port 80 to the MCP server on port 8005.

### Features
- ✅ HTTP proxy (port 80 → 8005)
- ✅ Health check endpoints
- ✅ WebSocket support
- ✅ Error page handling
- ✅ Timeout configurations

### Docker Setup
- **Image**: nginx:alpine
- **Ports**: 80:80, 443:443
- **Volumes**: Configuration and logs
- **Network**: Bridge network

## Deployment Infrastructure

### Components
1. **MCP Server**
   - Python FastAPI application
   - Running on port 8005
   - Background process with PID management

2. **Nginx Proxy**
   - Docker container
   - Port forwarding and load balancing
   - Access logging

3. **Management Scripts**
   - Start/stop scripts for both components
   - Log management
   - Process monitoring

### File Structure
```
pieces/
├── mcp_servers/
│   ├── kali_pieces_cloud_server.py
│   ├── hosted_pieces_ltm.py
│   ├── pieces_mcp_client.py
│   ├── pieces_mcp_config.json
│   ├── simple_pieces_query.py
│   ├── test_connection.py
│   ├── test_pieces_mcp.py
│   └── pieces_ltm/
│       └── server.py
├── nginx-mcp-proxy.conf
├── docker-compose-nginx.yml
├── start-nginx-proxy.sh
├── stop-nginx-proxy.sh
├── start_hosted_mcp_server.sh
├── stop_hosted_mcp_server.sh
├── mcp_server.pid
├── mcp_server.log
├── nginx-logs/
├── MCP_PIECESOS_LTM_INTEGRATION.md
├── DEPLOYMENT_KALI_PIECES_CLOUD.md
└── PIECES_MCP_COMPLETE_DOCUMENTATION.md
```

## Management Scripts

### MCP Server Management
```bash
# Start the MCP server
./pieces/start_hosted_mcp_server.sh

# Stop the MCP server
./pieces/stop_hosted_mcp_server.sh
```

### Nginx Proxy Management
```bash
# Start Nginx proxy
./pieces/start-nginx-proxy.sh

# Stop Nginx proxy
./pieces/stop-nginx-proxy.sh
```

### Process Monitoring
- **PID File**: `pieces/mcp_server.pid`
- **Server Logs**: `pieces/mcp_server.log`
- **Nginx Logs**: `pieces/nginx-logs/`

## Testing and Verification

### Local Access (Port 8005)
```bash
# Server info
curl http://localhost:8005/

# List tools
curl http://localhost:8005/tools

# Query LTM
curl -X POST http://localhost:8005/tools/query_pieces_ltm \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

### Proxy Access (Port 80)
```bash
# Server info through proxy
curl http://localhost/

# List tools through proxy
curl http://localhost/tools

# Query LTM through proxy
curl -X POST http://localhost/tools/query_pieces_ltm \
  -H "Content-Type: application/json" \
  -d '{"query": "test through proxy"}'
```

### All Endpoints Verified
✅ `GET /` - Server info
✅ `GET /health` - Health check
✅ `GET /tools` - Tools listing
✅ `POST /tools/query_pieces_ltm` - LTM queries
✅ `POST /tools/get_recent_memories` - Memory retrieval

## Next Steps for Production

### DNS Configuration
1. Point `kali.pieces.cloud` to your server IP
2. Configure A records in your DNS provider

### SSL/TLS Setup
1. Obtain SSL certificates (Let's Encrypt recommended)
2. Configure Nginx for HTTPS (port 443)
3. Set up automatic certificate renewal

### Systemd Services
1. Create systemd service files for automatic startup
2. Configure user permissions
3. Set up logging and monitoring

### Security Hardening
1. Configure firewall rules
2. Restrict CORS origins
3. Add authentication if needed
4. Implement rate limiting

## Troubleshooting

### Common Issues
1. **Port Conflicts**
   - Check if ports 80, 443, or 8005 are in use
   - Use `lsof -i :port` to identify processes

2. **Docker Issues**
   - Ensure Docker and docker-compose are installed
   - Check Docker service status

3. **Permission Issues**
   - Ensure scripts are executable
   - Check file ownership and permissions

### Log Locations
- **MCP Server**: `pieces/mcp_server.log`
- **Nginx Access**: `pieces/nginx-logs/access.log`
- **Nginx Error**: `pieces/nginx-logs/error.log`

## Conclusion

The PiecesOS MCP integration is now fully deployed and operational. The system provides:
- Local PiecesOS LTM access
- Hosted MCP server on `kali.pieces.cloud`
- Nginx proxy for production deployment
- Complete management infrastructure
- Comprehensive documentation

This integration enables seamless access to PiecesOS Long Term Memory capabilities both locally and through your custom domain.
