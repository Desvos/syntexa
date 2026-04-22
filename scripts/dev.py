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
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def get_python():
    """Get Python executable from backend/.venv or fallback to system python."""
    # Windows
    venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)

    # Linux/Mac
    venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)

    return "python"

def run_api():
    """Start API server with auto-reload."""
    print("🚀 Starting API server on http://localhost:8000")
    os.chdir(BACKEND_DIR)

    python = get_python()
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
    os.chdir(BACKEND_DIR)

    python = get_python()
    cmd = [python, "-m", "syntexa.daemon.main"]
    subprocess.run(cmd)

def run_frontend():
    """Start frontend dev server."""
    print("💻 Starting frontend on http://localhost:5173")
    os.chdir(FRONTEND_DIR)
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
            print("⚠️  'all' requires running multiple processes.")
            print("   Please use separate terminals or run:")
            print("     python scripts/dev.py api")
            print("     python scripts/dev.py daemon")
            print("     python scripts/dev.py frontend")
        else:
            print(f"Unknown command: {command}")
            show_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
