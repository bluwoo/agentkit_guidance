#!/usr/bin/env bash
# E2E check for the built frontend: serves web/dist from the same uvicorn
# process and asserts index.html + the hashed JS bundle both return 200.
# Does NOT take a screenshot. Requires web/dist to have been built.
#
# Usage:
#   bash deploy/e2e-web.sh [port]
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-8125}"
PY="${PY:-/tmp/agentkit_verify_venv/bin/python}"
BASE="http://127.0.0.1:${PORT}"
DIST="$PWD/web/dist"

if [ ! -f "$DIST/index.html" ]; then
  echo "FAIL: $DIST/index.html missing — build the frontend first (web/)"
  exit 1
fi

export WIZARD_MODE=mock
export WIZARD_DATA_DIR="$(mktemp -d)/wizdata"
export SERVE_FRONTEND_DIST="$DIST"
mkdir -p "$WIZARD_DATA_DIR"

echo "[e2e-web] starting uvicorn on :${PORT} (serving $DIST)..."
"$PY" -m uvicorn server.wizard.main:app --host 127.0.0.1 --port "$PORT" \
    > /tmp/e2e_web_uvicorn.log 2>&1 &
UVPID=$!
trap 'kill ${UVPID} 2>/dev/null || true' EXIT

echo -n "[e2e-web] waiting for /"
ready=0
for _ in $(seq 1 40); do
  if curl -fsS "${BASE}/" >/dev/null 2>&1; then ready=1; echo " up"; break; fi
  echo -n "."
  sleep 0.5
done
[ "$ready" -eq 1 ] || { echo " TIMEOUT"; cat /tmp/e2e_web_uvicorn.log >&2; exit 1; }

# index.html must be served and reference a JS bundle.
HTML="$(curl -fsS "${BASE}/")"
JS="$(echo "$HTML" | grep -oE '/assets/[^"]+\.js' | head -1 || true)"
if [ -z "$JS" ]; then echo "FAIL: index.html has no /assets/*.js reference"; exit 1; fi
echo "OK: GET / (index.html), bundle=$JS"

code="$(curl -fsS -o /dev/null -w '%{http_code}' "${BASE}${JS}")"
[ "$code" = "200" ] || { echo "FAIL: bundle $JS -> HTTP $code"; exit 1; }
echo "OK: GET $JS -> 200"

echo "E2E WEB PASSED"
