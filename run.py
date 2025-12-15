#!/usr/bin/env python3
"""
War Room Application Launcher

This script provides a unified way to run the War Room system:
1. Builds the React frontend if needed
2. Starts the webhook server (port 8001) 
3. Starts the main application server (port 8000)

Usage:
    python run.py              # Run both servers
    python run.py --build      # Force rebuild frontend first
    python run.py --dev        # Development mode (frontend dev server)
"""

import os
import sys
import subprocess
import threading
import time
import argparse
from pathlib import Path

def run_command(command, cwd=None, name="Process"):
    """Run a command and stream output."""
    print(f"[{name}] Starting: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(f"[{name}] {line.rstrip()}")
        
        process.wait()
        if process.returncode != 0:
            print(f"[{name}] Process exited with code {process.returncode}")
    except KeyboardInterrupt:
        print(f"[{name}] Interrupted")
        process.terminate()
    except Exception as e:
        print(f"[{name}] Error: {e}")

def check_node_modules():
    """Check if node_modules exists and install if needed."""
    frontend_path = Path("Frontend")
    node_modules_path = frontend_path / "node_modules"
    
    if not node_modules_path.exists():
        print("Installing frontend dependencies...")
        result = subprocess.run(["npm", "install"], cwd=frontend_path)
        if result.returncode != 0:
            print("Failed to install frontend dependencies")
            return False
    return True

def build_frontend():
    """Build the React frontend."""
    frontend_path = Path("Frontend")
    build_path = frontend_path / "build"
    
    print("Building React frontend...")
    
    if not check_node_modules():
        return False
    
    # Build the frontend
    result = subprocess.run(["npm", "run", "build"], cwd=frontend_path)
    
    if result.returncode == 0 and build_path.exists():
        print("Frontend build successful")
        return True
    else:
        print("Frontend build failed")
        return False

def check_frontend_build():
    """Check if frontend is built."""
    build_path = Path("Frontend/build")
    return build_path.exists() and (build_path / "index.html").exists()

def run_webhook_server():
    """Run the webhook server."""
    run_command(
        [sys.executable, "server.py"],
        name="Webhook Server"
    )

def run_main_server():
    """Run the main application server."""
    run_command(
        [sys.executable, "main.py"],
        name="Main Server"
    )

def run_frontend_dev():
    """Run the frontend development server."""
    frontend_path = Path("Frontend")
    if not check_node_modules():
        return
    
    run_command(
        ["npm", "run", "dev"],
        cwd=frontend_path,
        name="Frontend Dev"
    )

def main():
    parser = argparse.ArgumentParser(description="War Room Application Launcher")
    parser.add_argument("--build", action="store_true", help="Force rebuild frontend")
    parser.add_argument("--dev", action="store_true", help="Development mode (frontend dev server)")
    parser.add_argument("--webhook-only", action="store_true", help="Run only webhook server")
    parser.add_argument("--main-only", action="store_true", help="Run only main server")
    
    args = parser.parse_args()
    
    print("War Room Application Launcher")
    print("=" * 50)
    
    # Check Python dependencies
    try:
        import fastapi
        import uvicorn
        print("Python dependencies available")
    except ImportError as e:
        print(f"Missing Python dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return 1
    
    # Development mode
    if args.dev:
        print("Development Mode")
        print("Frontend: http://localhost:5173")
        print("Main API: http://localhost:8000")
        print("Webhook API: http://localhost:8001")
        print("-" * 50)
        
        # Start servers in parallel
        webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
        main_thread = threading.Thread(target=run_main_server, daemon=True)
        
        webhook_thread.start()
        time.sleep(2)  # Give webhook server time to start
        main_thread.start()
        time.sleep(2)  # Give main server time to start
        
        # Run frontend dev server in foreground
        run_frontend_dev()
        return 0
    
    # Production mode
    if args.webhook_only:
        print("Starting Webhook Server Only")
        run_webhook_server()
        return 0
    
    if args.main_only:
        if not check_frontend_build():
            print("Frontend not built. Run with --build first or run full startup.")
            return 1
        
        print("Starting Main Server Only")
        run_main_server()
        return 0
    
    # Full startup
    print("Production Mode")
    
    # Build frontend if needed or requested
    if args.build or not check_frontend_build():
        if not build_frontend():
            return 1
    else:
        print("Frontend already built")
    
    print("\nStarting servers...")
    print("Main App: http://localhost:8000")
    print("Webhook API: http://localhost:8001")
    print("-" * 50)
    print("Press Ctrl+C to stop all servers")
    
    try:
        # Start webhook server in background thread
        webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
        webhook_thread.start()
        
        # Give webhook server time to start
        time.sleep(2)
        
        # Start main server in foreground
        run_main_server()
        
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        return 0

if __name__ == "__main__":
    sys.exit(main())