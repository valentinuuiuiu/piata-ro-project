
#!/usr/bin/env python3
"""
Start script for Piata.ro project that starts both Django server and MCP agents (8001-8003).
"""

import os
import sys
import subprocess
import time
import signal
import requests
from pathlib import Path
from threading import Thread
from typing import List, Optional

# Add project root to Python path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class MCPAgent:
    """Represents an MCP agent process."""
    def __init__(self, name: str, script_path: Path, port: int):
        self.name = name
        self.script_path = script_path
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.running = False

    def start(self) -> bool:
        """Start the MCP agent process."""
        try:
            print(f"🚀 Starting {self.name} on port {self.port}...")
            cmd = [sys.executable, str(self.script_path), "--host", "0.0.0.0", "--port", str(self.port)]
            env = os.environ.copy()
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.script_path.parent),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            Thread(target=self._monitor_output, daemon=True).start()
            Thread(target=self._monitor_error, daemon=True).start()
            time.sleep(2)
            if self.is_healthy():
                self.running = True
                print(f"✅ {self.name} started successfully on port {self.port}")
                return True
            print(f"❌ {self.name} failed to start on port {self.port}")
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
            return False
        except Exception as e:
            print(f"❌ Error starting {self.name}: {e}")
            return False

    def _monitor_output(self):
        if not self.process or not self.process.stdout:
            return
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    print(f"[{self.name}-OUT] {line.strip()}")
        except Exception as e:
            if self.running:
                print(f"[{self.name}-OUT] monitor error: {e}")

    def _monitor_error(self):
        if not self.process or not self.process.stderr:
            return
        try:
            for line in iter(self.process.stderr.readline, ''):
                if line:
                    print(f"[{self.name}-ERR] {line.strip()}")
        except Exception as e:
            if self.running:
                print(f"[{self.name}-ERR] monitor error: {e}")

    def is_healthy(self) -> bool:
        try:
            resp = requests.get(f"http://127.0.0.1:{self.port}/health", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def stop(self):
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
        archive_path = BASE_DIR / "archive" / "mcp-servers-20250630"
        # Map ports to existing scripts in archive folder
        self.mcp_agents_config = [
            {"name": "Advertising Agent", "script": archive_path / "advertising-agent.py", "port": 8001},
            {"name": "Django SQL Agent", "script": archive_path / "django_sql_agent.py", "port": 8002},
            {"name": "Stock Agent", "script": archive_path / "stock_agent.py", "port": 8003},
        ]

    def start_mcp_agents(self):
        for cfg in self.mcp_agents_config:
            agent = MCPAgent(cfg["name"], cfg["script"], cfg["port"])
            ok = agent.start()
            if ok:
                self.mcp_agents.append(agent)
            else:
                print(f"⚠️  {cfg['name']} did not start properly.")

    def check_django(self) -> bool:
        """Check if Django server is running and accessible"""
        try:
            r = requests.get("http://127.0.0.1:8000/", timeout=3)
            if r.status_code == 200:
                return True
            else:
                print(f"⚠️  Django server responded with status: {r.status_code}")
                return False
        except requests.exceptions.SSLError:
            print("🔒 SSL Error: Something is trying to use HTTPS with development server")
            print("   Development server only supports HTTP. Use http://localhost:8000")
            return False
        except requests.exceptions.ConnectionError:
            # Server not running yet or connection refused
            return False
        except Exception as e:
            print(f"⚠️  Unexpected error checking Django server: {e}")
            return False

    def start_django(self) -> bool:
        try:
            print("🚀 Starting Django development server on port 8000...")
            print("⚠️  Note: Development server runs on HTTP only. For HTTPS, use a reverse proxy like nginx.")
            
            # Set environment variable to prevent HTTPS upgrade attempts
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["DJANGO_SETTINGS_MODULE"] = "piata_ro.settings"
            
            cmd = [sys.executable, "manage.py", "runserver", "0.0.0.0:8000", "--noreload", "--insecure"]
            self.django_process = subprocess.Popen(
                cmd, cwd=str(BASE_DIR), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            Thread(target=self._monitor_django_output, daemon=True).start()
            time.sleep(5)  # Give more time for server to start
            if self.check_django():
                print("✅ Django server started successfully")
                print("🌐 Server available at: http://localhost:8000")
                print("🔒 For HTTPS, configure nginx or use production deployment")
                return True
            print("❌ Django server failed to start")
            return False
        except Exception as e:
            print(f"❌ Error starting Django server: {e}")
            return False

    def _monitor_django_output(self):
        if not self.django_process or not self.django_process.stdout:
            return
        try:
            for line in iter(self.django_process.stdout.readline, ''):
                if line:
                    print(f"[DJANGO] {line.strip()}")
        except Exception as e:
            print(f"[DJANGO] monitor error: {e}")

    def start_all(self):
        print("🛒 Starting MCP agents (8001-8003) and Django server...")
        self.start_mcp_agents()
        if not self.start_django():
            print("❌ Could not start Django server. Shutting down agents.")
            self.stop_all()
            sys.exit(1)
        print("✅ All services started. Admin Assistant can connect to 8001-8003.")

    def stop_all(self):
        if self.django_process and self.django_process.poll() is None:
            print("🛑 Stopping Django server...")
            self.django_process.terminate()
            try:
                self.django_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("⚠️  Forcing Django kill...")
                self.django_process.kill()
                self.django_process.wait()
        for a in self.mcp_agents:
            a.stop()

def main():
    mgr = ServerManager()
    def handle_signal(signum, frame):
        mgr.stop_all()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    mgr.start_all()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_signal(None, None)

if __name__ == "__main__":
    main()
