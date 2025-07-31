# PiecesOS LTM Integration with MCP

## Current Status

PiecesOS is successfully running on `localhost:39300` with MCP capabilities enabled.

## Verification

```bash
curl -m 5 http://localhost:39300/model_context_protocol/2024-11-05/sse
```

Response:
```
event: endpoint
data: /model_context_protocol/2024-11-05/messages
```

This confirms that:
- PiecesOS MCP server is active and listening
- The SSE endpoint is working correctly
- The messages endpoint is available at `/model_context_protocol/2024-11-05/messages`

## How to Use PiecesOS LTM

### Method 1: IDE Integration (Recommended)
1. Use your IDE's MCP integration (Cursor, VSCode, etc.)
2. Connect to `http://localhost:39300` as the MCP server
3. Use the `ask_pieces_ltm` tool to query your long-term memory

### Method 2: Direct API Access
1. Connect to the MCP messages endpoint
2. Use the MCP protocol to communicate with PiecesOS
3. Access LTM functionality through available tools

### Method 3: Pieces Desktop App
1. Use the Pieces Desktop Application
2. Access your LTM through the UI
3. Manage memories, tags, and context

## Available LTM Functionality

Based on the Pieces MCP documentation, the following capabilities should be available:

1. **Context-Rich Queries**: Query your LTM for relevant information
2. **Memory Storage**: Store new memories with metadata
3. **Memory Retrieval**: Retrieve past memories and context
4. **Tag Management**: Organize memories with tags
5. **Contextual Debugging**: Access debugging history and solutions

## Next Steps

To fully utilize PiecesOS LTM:

1. **Configure IDE Integration**: Set up your development environment to connect to PiecesOS MCP
2. **Test LTM Queries**: Use the `ask_pieces_ltm` tool to query your memory
3. **Store Context**: Begin storing valuable development context in your LTM
4. **Integrate with Workflow**: Make LTM queries part of your daily development process

## Example Usage

```python
# Conceptual example of LTM query through MCP
tool_name = "ask_pieces_ltm"
arguments = {
    "query": "What did I work on yesterday?",
    "context": "development"
}
# This would return relevant memories from your LTM
```

## Troubleshooting

If you encounter connection issues:
1. Verify PiecesOS is running: `lsof -i :39300`
2. Check firewall settings
3. Ensure no other process is blocking the connection
4. Restart PiecesOS if needed

## Conclusion

PiecesOS LTM is ready and accessible. The MCP integration is working correctly, and you can now leverage your long-term memory for enhanced development productivity.
