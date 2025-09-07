#!/usr/bin/env python3
"""
Test script to verify MCP server configurations
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def test_mcp_config():
    """Test MCP server configurations"""
    
    # Get the MCP config file
    config_path = Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    
    if not config_path.exists():
        print(f"❌ MCP config file not found: {config_path}")
        return False
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        print("✅ MCP config file found and valid JSON")
        
        # Check servers
        servers = config.get("mcp", {}).get("servers", {})
        print(f"📊 Found {len(servers)} MCP servers configured")
        
        for name, server_config in servers.items():
            print(f"\n🔍 Testing server: {name}")
            print(f"   Type: {server_config.get('type')}")
            print(f"   Command: {server_config.get('command')}")
            print(f"   Args: {server_config.get('args', [])}")
            
            # Test if command exists
            cmd = server_config.get('command')
            if cmd:
                try:
                    result = subprocess.run(['which', cmd], capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"   ✅ Command '{cmd}' found at: {result.stdout.strip()}")
                    else:
                        print(f"   ⚠️  Command '{cmd}' not found in PATH")
                except Exception as e:
                    print(f"   ⚠️  Error checking command: {e}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def test_server_startup():
    """Test if MCP servers can start"""
    
    test_commands = [
        ["npx", "-y", "@modelcontextprotocol/server-memory@latest"],
        ["npx", "-y", "@upstash/context7-mcp@latest"],
        ["npx", "-y", "@playwright/mcp@latest"],
    ]
    
    print("\n🚀 Testing MCP server startup...")
    
    for cmd in test_commands:
        try:
            print(f"\nTesting: {' '.join(cmd)}")
            result = subprocess.run(cmd + ["--help"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"   ✅ Server started successfully")
            else:
                print(f"   ⚠️  Server failed to start: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Server startup timed out")
        except Exception as e:
            print(f"   ⚠️  Error starting server: {e}")

if __name__ == "__main__":
    print("🔧 MCP Configuration Test")
    print("=" * 50)
    
    success = test_mcp_config()
    test_server_startup()
    
    if success:
        print("\n✅ Configuration test completed")
    else:
        print("\n❌ Configuration test failed")
        sys.exit(1)
