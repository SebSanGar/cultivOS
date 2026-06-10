#!/bin/bash
# ═══════════════════════════════════════════
# cultivOS — Launch Script
# Usage: ./run.sh
# Stop:  Ctrl+C
# ═══════════════════════════════════════════

cd "$(dirname "$0")"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════╗"
echo "  ║     cultivOS  Starting...     ║"
echo "  ╚═══════════════════════════════╝"
echo -e "${NC}"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${CYAN}Using venv${NC}"
fi

# Require Python 3.11+ — the codebase uses PEP 604 `X | None` unions that error on 3.9/3.10
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo -e "${CYAN}Error: cultivOS needs Python 3.11+. Rebuild the venv:${NC}"
    echo "  rm -rf venv && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# First run: create a local .env (dev JWT secret + AUTH_ENABLED=false) so login and the
# farm dropdown work out of the box. Production sets these via real env vars, not this file.
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${CYAN}Created .env from .env.example (local dev defaults)${NC}"
fi

echo -e "${CYAN}[0/2] Checking dependencies...${NC}"
pip install -r requirements.txt -q 2>/dev/null
echo -e "${CYAN}Dependencies OK${NC}"

lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

cleanup() {
    echo -e "\n${CYAN}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${CYAN}Starting → http://localhost:8000${NC}"
PYTHONPATH="$PWD/src" uvicorn cultivos.app:create_app --factory --reload --reload-dir "$PWD/src" --port 8000 &
BACKEND_PID=$!

echo ""
echo -e "${GREEN}Open http://localhost:8000${NC}"
echo -e "${CYAN}  Ctrl+C to stop.${NC}"
echo ""

wait
