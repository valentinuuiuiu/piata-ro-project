
#!/usr/bin/env python3
"""
Start script for Piata.ro project that starts both Django server and MCP agents.
"""

import os
import sys
import subprocess
import time
import signal
import requests
from pathlib import Path
from threading import Thread
from typing import List, Dict, Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

class MCPAgent:
    """Represents an MCP agent process."""
    
    def __init__(self, name: str, script_path: str, port: int):
        self.name = name
        self.script_path = script_path
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.running = False
    
    def start(self) -> bool:
        """Start the MCP agent process."""
        try:
            print(f"🚀 Starting {self.name} on port {self.port}...")
            
            # Create the command to run the agent with host and port arguments
            cmd = [sys.executable, str(self.script_path), "--host", "0.0.0.0", "--port", str(self.port)]
            
            # Set environment variables
            env = os.environ.copy()
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                cwd=Path(__file__).parent,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start output monitoring for both stdout and stderr in separate threads
            Thread(target=self._monitor_output, daemon=True).start()
            Thread(target=self._monitor_error, daemon=True).start()
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Check if the agent is responding
            if self.is_healthy():
                self.running = True
                print(f"✅ {self.name} started successfully on port {self.port}")
                return True
            else:
                print(f"❌ {self.name} failed to start on port {self.port}")
                if self.process:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                return False
                
        except Exception as e:
            print(f"❌ Error starting {self.name}: {e}")
            return False

    def _monitor_output(self):
        """Monitor the agent's stdout output and print it."""
        if not self.process or not self.process.stdout:
            return
            
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    print(f"[{self.name}-OUT] {line.strip()}")
        except Exception as e:
            if self.running:
                print(f"[{self.name}-OUT] Output monitoring error: {e}")

    def _monitor_error(self):
        """Monitor the agent's stderr output and print it."""
        if not self.process or not self.process.stderr:
            return
            
        try:
            for line in iter(self.process.stderr.readline, ''):
                if line:
                    print(f"[{self.name}-ERR] {line.strip()}")
        except Exception as e:
            if self.running:
                print(f"[{self.name}-ERR] Error monitoring error: {e}")

    def is_healthy(self) -> bool:
        """Check if the agent is running and healthy."""
        try:
            response = requests.get(f'http://localhost:{self.port}/health', timeout=5)
            return response.status_code == 200
        except:
            return False

    def stop(self):
        """Stop the MCP agent process."""
        if self.process and self.process.poll() is None:
            print(f"🛑 Stopping {self.name}...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"⚠️  {self.name} didn't terminate gracefully, forcing kill...")
                self.process.kill()
                self.process.wait()
        self.running = False

class ServerManager:
    """Manages the Django server and MCP agents."""
    
    def __init__(self):
        self.django_process: Optional[subprocess.Popen] = None
        self.mcp_agents: List[MCPAgent] = []
        self.running = False
        
        # Define MCP agents
        archive_path = Path(__file__).parent / "archive" / "mcp-servers-20250630"
        self.mcp_agents_config = [
            {
                "name": "Simple SQL Agent",
                "script": archive_path / "simple_sql_agent.py",
                "port": 8002
            },
            {
                "name": "Stock Agent",
                "script": archive_path / "stock_agent.py",
                "port": 8003
            }
        ]
    
    def check_django_server(self) -> bool:
        """Check if Django server is running."""
        try:
            response = requests.get('http://127.0.0.1:8000/', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_django_server(self) -> bool:
        """Start the Django development server."""
        try:
            print("🚀 Starting Django development server on port 8000...")
            
            # Create command to start Django server
            cmd = [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"]
            
            # Set environment variables
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            # Start the process
            self.django_process = subprocess.Popen(
                cmd,
                cwd=Path(__file__).parent,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is running
            if self.check_django_server():
                print("✅ Django server started successfully")
                # Start output monitoring
                Thread(target=self._monitor_django_output, daemon=True).start()
                return True
            else:
                print("❌ Django server failed to start")
                if self.django_process:
                    self.django_process.terminate()
                    self.django_process.wait(timeout=5)
                return False
                
        except Exception as e:
            print(f"❌ Error starting Django server: {e}")
            return False
    
    def _monitor_django_output(self):
        """Monitor Django server output."""
        if not self.django_process or not self.django_process.stdout:
            return
            
        try:
            for line in iter(self.django_process.stdout.readline, ''):
                if line:
                    print(f"[Django] {line.strip()}")
        except Exception as e:
            if self.running:
                print(f"[Django] Output monitoring error: {e}")
    
    def start_mcp_agents(self) -> bool:
        """Start all MCP agents."""
        success = True
        for config in self.mcp_agents_config:
            # Check if agent is already running
            try:
                response = requests.get(f'http://localhost:{config["port"]}/health', timeout=2)
                if response.status_code == 200:
                    print(f"✅ {config['name']} is already running on port {config['port']}")
                    continue
            except:
                pass
            
            # Create and start agent
            agent = MCPAgent(config["name"], config["script"], config["port"])
            if agent.start():
                self.mcp_agents.append(agent)
            else:
                success = False
        
        return success
    
    def start(self):
        """Start the complete server setup."""
        print("🛒 Starting Piata.ro Development Environment")
        print("=" * 50)
        
        # Start Django server
        if not self.start_django_server():
            print("❌ Failed to start Django server. Aborting.")
            return
        
        # Start MCP agents
        if not self.start_mcp_agents():
            print("⚠️  Some MCP agents failed to start. Continuing with available services.")
        
        self.running = True
        print("\n🎉 All services started successfully!")
        print("\n🌐 Application is now available at: http://localhost:8000")
        print("\n📋 MCP Agent Endpoints:")
        for config in self.mcp_agents_config:
            print(f"   • {config['name']}: http://localhost:{config['port']}")
        
        print("\n💡 Press Ctrl+C to stop all services")
        
        # Wait for termination signal
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Received shutdown signal...")
            self.stop()
    
    def stop(self):
        """Stop all services."""
        print("\n🛑 Stopping all services...")
        
        # Stop MCP agents
        for agent in self.mcp_agents:
            agent.stop()
        
        # Stop Django server
        if self.django_process and self.django_process.poll() is None:
            print("🛑 Stopping Django server...")
            self.django_process.terminate()
            try:
                self.django_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("⚠️  Django server didn't terminate gracefully, forcing kill...")
                self.django_process.kill()
                self.django_process.wait()
        
        self.running = False
        print("✅ All services stopped")

def main():
    """Main entry point."""
    # Create server manager
    manager = ServerManager()
    
    # Register signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        if hasattr(manager, 'stop'):
            manager.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the server
    manager.start()

if __name__ == "__main__":
    main()
