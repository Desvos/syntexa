#!/bin/bash
# Development launcher for Syntexa
# Usage: ./scripts/dev.sh [api|daemon|frontend|all]

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_help() {
    echo "Syntexa Development Launcher"
    echo ""
    echo "Usage: ./scripts/dev.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  api       - Start API server with auto-reload"
    echo "  daemon    - Start daemon with auto-reload"
    echo "  frontend  - Start frontend dev server"
    echo "  all       - Start all services (api + daemon + frontend)"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./scripts/dev.sh api      # API only"
    echo "  ./scripts/dev.sh frontend # Frontend only"
    echo "  ./scripts/dev.sh all      # Full stack"
}

# Detect venv path (Windows Git Bash uses Scripts/, Linux/Mac uses bin/)
get_venv_python() {
    if [ -f ".venv/Scripts/python.exe" ]; then
        echo ".venv/Scripts/python"
    elif [ -d ".venv/bin" ]; then
        echo ".venv/bin/python"
    else
        echo "python"
    fi
}

start_api() {
    echo -e "${GREEN}Starting API server...${NC}"
    cd "$PROJECT_ROOT/backend"
    PYTHON=$(get_venv_python)
    # Note: --reload is disabled because sessions are stored in-memory
    # and reload clears them. For dev with auth, don't use reload.
    exec "$PYTHON" -m uvicorn syntexa.api.main:app --host 0.0.0.0 --port 8000
}

start_daemon() {
    echo -e "${GREEN}Starting daemon...${NC}"
    cd "$PROJECT_ROOT/backend"
    PYTHON=$(get_venv_python)
    exec "$PYTHON" -m syntexa.daemon.main
}

start_frontend() {
    echo -e "${GREEN}Starting frontend...${NC}"
    cd "$PROJECT_ROOT/frontend"
    exec bun run dev
}

start_all() {
    echo -e "${YELLOW}Starting all services...${NC}"
    # Start API
    start_api &
    API_PID=$!

    # Wait a moment for API to start
    sleep 2

    # Start daemon
    start_daemon &
    DAEMON_PID=$!

    # Start frontend
    start_frontend &
    FRONTEND_PID=$!

    echo -e "${GREEN}All services started!${NC}"
    echo "API:      http://localhost:8000"
    echo "Frontend: http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop all services"

    # Wait for all processes
    wait $API_PID $DAEMON_PID $FRONTEND_PID
}

# Main
COMMAND=${1:-help}

case $COMMAND in
    api)
        start_api
        ;;
    daemon)
        start_daemon
        ;;
    frontend)
        start_frontend
        ;;
    all)
        start_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
