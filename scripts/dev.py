#!/usr/bin/env python3
"""
Syntexa Development Launcher
Usage: python scripts/dev.py [api|daemon|frontend|all]
"""

import sys
import subprocess
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_api():
    """Start API server with auto-reload."""
    print("🚀 Starting API server on http://localhost:8000")
    os.chdir(PROJECT_ROOT / "backend")

    # Check for venv
    venv_python = PROJECT_ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = PROJECT_ROOT / "backend" / ".venv" / "bin" / "python"

    if venv_python.exists():
        python = str(venv_python)
    else:
        python = "python"

    cmd = [
        python, "-m", "uvicorn",
        "syntexa.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ]
    subprocess.run(cmd)

def run_daemon():
    """Start daemon."""
    print("🤖 Starting daemon...")
    os.chdir(PROJECT_ROOT / "backend")

    venv_python = PROJECT_ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = PROJECT_ROOT / "backend" / ".venv" / "bin" / "python"

    python = str(venv_python) if venv_python.exists() else "python"

    cmd = [python, "-m", "syntexa.daemon.main"]
    subprocess.run(cmd)

def run_frontend():
    """Start frontend dev server."""
    print("💻 Starting frontend on http://localhost:5173")
    os.chdir(PROJECT_ROOT / "frontend")
    subprocess.run(["bun", "run", "dev"])

def show_help():
    print("""
Syntexa Development Launcher

Usage: python scripts/dev.py [COMMAND]

Commands:
  api       - Start API server with auto-reload (port 8000)
  daemon    - Start daemon
  frontend  - Start frontend dev server (port 5173)
  all       - Start all services

Examples:
  python scripts/dev.py api       # API only
  python scripts/dev.py frontend # Frontend only
  python scripts/dev.py all       # Full stack
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1]

    try:
        if command == "api":
            run_api()
        elif command == "daemon":
            run_daemon()
        elif command == "frontend":
            run_frontend()
        elif command == "all":
            print("Starting all services...")
            print("Use Ctrl+C to stop")
            # Run all in parallel - Windows compatible
            import threading
            threads = [
                threading.Thread(target=run_api, daemon=True),
                threading.Thread(target=run_daemon, daemon=True),
                threading.Thread(target=run_frontend, daemon=True),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        else:
            print(f"Unknown command: {command}")
            show_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
