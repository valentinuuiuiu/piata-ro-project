# Deployment Guide: PiecesOS LTM MCP Server on kali.pieces.cloud

## Overview

This guide explains how to deploy the PiecesOS LTM MCP server on your domain `kali.pieces.cloud`.

## Server Details

- **File**: `mcp_servers/kali_pieces_cloud_server.py`
- **Port**: 8005
- **Endpoints**:
  - `/` - Health check and server info
  - `/tools` - List available MCP tools
  - `/tools/{tool_name}` - Execute MCP tools
  - `/health` - Health check endpoint

## Prerequisites

1. Python 3.9+
2. Required packages (install with pip):
   ```bash
   pip install fastapi uvicorn pydantic starlette
   ```

## Deployment Steps

### 1. Copy Server File
```bash
# Ensure the server file exists
ls -la mcp_servers/kali_pieces_cloud_server.py
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn pydantic starlette
```

### 3. Start the Server
```bash
python mcp_servers/kali_pieces_cloud_server.py
```

### 4. Configure Reverse Proxy (Nginx/Apache)
To make the server accessible via `kali.pieces.cloud`, configure your web server to proxy requests to port 8005.

#### Nginx Example Configuration:
```nginx
server {
    listen 80;
    server_name kali.pieces.cloud;

    location / {
        proxy_pass http://localhost:8005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Systemd Service (Optional)
Create a systemd service to run the server automatically:

```bash
sudo nano /etc/systemd/system/pieces-ltm-mcp.service
```

Service file content:
```ini
[Unit]
Description=PiecesOS LTM MCP Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/piata-ro-project
ExecStart=/home/your-username/piata-ro-project/venv/bin/python mcp_servers/kali_pieces_cloud_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable pieces-ltm-mcp.service
sudo systemctl start pieces-ltm-mcp.service
sudo systemctl status pieces-ltm-mcp.service
```

## Available MCP Tools

### 1. query_pieces_ltm
Query the PiecesOS Long Term Memory for relevant information.

**Parameters**:
- `query` (string, required): The query to search for in LTM
- `context` (string, optional): Optional context for the query

**Example**:
```bash
curl -X POST http://kali.pieces.cloud/tools/query_pieces_ltm \
  -H "Content-Type: application/json" \
  -d '{"query": "What did I work on today?", "context": "development"}'
```

### 2. get_recent_memories
Get recent memories from PiecesOS LTM.

**Parameters**:
- `limit` (integer, optional): Maximum number of memories to return (default: 10)

**Example**:
```bash
curl -X POST http://kali.pieces.cloud/tools/get_recent_memories \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

## Testing the Deployment

### Health Check
```bash
curl http://kali.pieces.cloud/
```

### List Tools
```bash
curl http://kali.pieces.cloud/tools
```

### Query LTM
```bash
curl -X POST http://kali.pieces.cloud/tools/query_pieces_ltm \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

## Integration with IDEs

To use this hosted MCP server with your IDE:

1. Configure your IDE's MCP settings to connect to `http://kali.pieces.cloud`
2. Use the available tools:
   - `query_pieces_ltm` for context-rich queries
   - `get_recent_memories` for recent memory retrieval

## Troubleshooting

### Server Not Starting
- Check if port 8005 is already in use: `lsof -i :8005`
- Verify Python dependencies are installed
- Check file permissions

### Connection Issues
- Verify the reverse proxy configuration
- Check firewall settings
- Ensure DNS is properly configured for `kali.pieces.cloud`

### Performance Issues
- Monitor server logs: `journalctl -u pieces-ltm-mcp.service -f`
- Check system resources: `htop`, `df -h`
- Consider adding load balancing for high traffic

## Security Considerations

1. **CORS**: The server allows all origins by default. For production, restrict to specific domains.
2. **Authentication**: Consider adding authentication for production use.
3. **Rate Limiting**: Implement rate limiting to prevent abuse.
4. **HTTPS**: Use SSL/TLS certificates for secure connections.

## Monitoring

### Health Endpoint
```bash
curl http://kali.pieces.cloud/health
```

### Log Monitoring
```bash
# If using systemd service
sudo journalctl -u pieces-ltm-mcp.service -f

# If running directly
tail -f nohup.out
```

## Updates and Maintenance

### Updating the Server
1. Pull the latest code
2. Restart the service: `sudo systemctl restart pieces-ltm-mcp.service`
3. Verify the service is running: `sudo systemctl status pieces-ltm-mcp.service`

### Backup Configuration
Regularly backup your configuration files and any persistent data.

## Conclusion

Your PiecesOS LTM MCP server is now ready to be hosted on `kali.pieces.cloud`. The server provides MCP-compatible tools for querying your long-term memory and can be integrated with various IDEs and development tools.
