#!/usr/bin/env bash
# scripts/verify.sh — canonical "is cultivOS 100%?" gate.
#
# North Star (locked 2026-06-15): full test suite green AND key pages work
# end-to-end. This is the single source of truth for "done" — used by the
# in-session dev loop and by autoagent as its success check. Exit 0 = healthy.
#
# Usage: ./scripts/verify.sh   (run from anywhere; resolves repo root itself)
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src"

echo "[verify] 1/2 — test suite (timeout-guarded, cannot hang)…"
if ! python3 -m pytest tests/ -q -p no:cacheprovider --timeout=120; then
  echo "[verify] ✗ FAIL: test suite"; exit 1
fi

echo "[verify] 2/2 — pages end-to-end…"
PORT="${VERIFY_PORT:-8099}"
python3 -m uvicorn cultivos.app:create_app --factory --host 127.0.0.1 --port "$PORT" \
  >/tmp/cultivos_verify_boot.log 2>&1 &
SRV=$!
trap 'kill "$SRV" 2>/dev/null' EXIT
for _ in $(seq 1 40); do curl -sf -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.5; done

fail=0
# farmer surfaces, owner surfaces, core API + docs
for url in / "/api/farms?page_size=5" /campo /notificaciones /conocimiento \
           /impacto-agricultor /impacto-economico /docs; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT$url")
  if [ "$code" != "200" ]; then echo "[verify]   ✗ $url -> $code"; fail=1; fi
done

if [ "$fail" -ne 0 ]; then echo "[verify] ✗ FAIL: pages"; exit 1; fi
echo "[verify] ✓ ALL GREEN — suite passing + pages live end-to-end"
