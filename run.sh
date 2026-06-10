#!/bin/bash
# ═══════════════════════════════════════════
# cultivOS — One-command launch
# Usage: ./run.sh        (does everything: venv, deps, .env, demo data, server)
# Stop:  Ctrl+C
# ═══════════════════════════════════════════
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[0;33m'; NC='\033[0m'

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════╗"
echo "  ║     cultivOS  Starting...     ║"
echo "  ╚═══════════════════════════════╝"
echo -e "${NC}"

# 1. Find a Python 3.11+ interpreter (codebase uses PEP 604 `X | None` unions).
find_py() {
    for c in python3.13 python3.12 python3.11 python3 python; do
        if command -v "$c" >/dev/null 2>&1 && \
           "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
            echo "$c"; return 0
        fi
    done
    return 1
}

# 2. Create the venv (with a 3.11+ interpreter) if it's missing.
if [ ! -d venv ]; then
    PY=$(find_py) || {
        echo -e "${YELLOW}Python 3.11+ not found.${NC}"
        echo "  Install it, then re-run ./run.sh :"
        echo "    macOS:  brew install python@3.11"
        echo "    Ubuntu: sudo apt install python3.11 python3.11-venv"
        exit 1
    }
    echo -e "${CYAN}Creating venv with $PY ($($PY --version 2>&1))...${NC}"
    "$PY" -m venv venv
fi
source venv/bin/activate

# Safety net: venv must be 3.11+ (e.g. an old venv created with 3.9).
if ! python -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
    echo -e "${YELLOW}Existing venv is older than Python 3.11. Rebuilding...${NC}"
    deactivate 2>/dev/null || true
    rm -rf venv
    PY=$(find_py) || { echo "  Python 3.11+ not found — see install hint above."; exit 1; }
    "$PY" -m venv venv && source venv/bin/activate
fi

# 3. First run: local .env (dev JWT secret + AUTH_ENABLED=false) so login + the
#    farm dropdown work out of the box. Production injects these as real env vars.
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${CYAN}Created .env from .env.example (local dev defaults)${NC}"
fi

# 4. Dependencies.
echo -e "${CYAN}[1/3] Installing dependencies...${NC}"
pip install -q --upgrade pip >/dev/null 2>&1 || true
pip install -q -r requirements.txt

# 5. Demo data (idempotent — safe every run; gives a populated dashboard, not "Cargando...").
echo -e "${CYAN}[2/3] Seeding demo data...${NC}"
PYTHONPATH="$PWD/src" python scripts/seed_demo.py || \
    echo -e "${YELLOW}  (seed skipped — continuing)${NC}"

# 6. Launch.
echo -e "${CYAN}[3/3] Starting server...${NC}"
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

cleanup() { echo -e "\n${CYAN}Shutting down...${NC}"; kill $BACKEND_PID 2>/dev/null; exit 0; }
trap cleanup SIGINT SIGTERM

PYTHONPATH="$PWD/src" uvicorn cultivos.app:create_app --factory \
    --reload --reload-dir "$PWD/src" --port 8000 &
BACKEND_PID=$!

echo ""
echo -e "${GREEN}  ✓ cultivOS running → http://localhost:8000${NC}"
echo -e "${CYAN}    Auth is OFF in local dev — just open the URL. Ctrl+C to stop.${NC}"
echo ""
wait
