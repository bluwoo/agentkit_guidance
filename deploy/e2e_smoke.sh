#!/usr/bin/env bash
# Reproducible, screenshot-free E2E smoke test for the AgentKit Wizard backend.
#
# Boots uvicorn in WIZARD_MODE=mock (deterministic offline bridge, no LLM),
# then drives the real HTTP endpoints with curl and greps the SSE stream.
# Any non-2xx / missing event exits non-zero. Safe to run repeatedly.
#
# Contract under test (matches server/wizard/main.py + run_local.sh):
#   * GET  /health /readiness          — public liveness probes
#   * POST /api/auth/setup             — one-time owner bootstrap; sets the
#                                        wizard_session cookie used for all
#                                        /api/wizard/* business routes (the
#                                        browser login gate, see auth.public_path)
#   * GET  /api/wizard/components      — business route, REQUIRES the cookie
#   * POST /invoke                    — Layer-1 runtime protocol (public to the
#                                        front door; KeyAuth off when no key set)
#   * POST /run_sse                   — Layer-2 SSE streaming (public)
#
# Usage:
#   bash deploy/e2e_smoke.sh [port]
# Env:
#   PY  python interpreter (default /tmp/agentkit_verify_venv/bin/python)
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PY:-/tmp/agentkit_verify_venv/bin/python}"

# --- port: default to a FREE ephemeral port so we never probe a foreign server
# already listening on a well-known port. An explicit arg pins it. ------------
if [ "$#" -ge 1 ]; then
  PORT="$1"
else
  PORT="$("$PY" - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
)"
fi
BASE="http://127.0.0.1:${PORT}"
WORKDIR="$(mktemp -d)/wizdata"
JAR="$(mktemp)"
mkdir -p "$WORKDIR"

export WIZARD_MODE=mock
export WIZARD_DATA_DIR="$WORKDIR"
# Bootstrap token for the one-time owner setup (local smoke only, no cloud).
export WIZARD_OWNER_SETUP_TOKEN="${WIZARD_OWNER_SETUP_TOKEN:-e2e-smoke-bootstrap}"
# API-only smoke (do not require a built frontend here).
unset SERVE_FRONTEND_DIST || true

echo "[e2e] starting uvicorn on :${PORT} (WIZARD_MODE=mock)..."
"$PY" -m uvicorn server.wizard.main:app --host 127.0.0.1 --port "$PORT" \
    > /tmp/e2e_uvicorn.log 2>&1 &
UVPID=$!
# uvicorn's graceful shutdown can hang on the MCP session manager, so give it
# SIGTERM briefly then fall back to SIGKILL (never leak a listener).
trap 'kill -TERM ${UVPID} 2>/dev/null || true; for _ in $(seq 1 10); do kill -0 ${UVPID} 2>/dev/null || break; sleep 0.3; done; kill -KILL ${UVPID} 2>/dev/null || true' EXIT

# Fail fast if uvicorn died on boot (e.g. EADDRINUSE -> we would otherwise
# probe whatever foreign server already owns the port).
sleep 1
if ! kill -0 "${UVPID}" 2>/dev/null; then
  echo "FAIL: uvicorn exited during boot (port ${PORT}?)"
  echo "---- uvicorn log ----" >&2
  cat /tmp/e2e_uvicorn.log >&2 || true
  exit 1
fi

# Wait for /health (max ~20s).
echo -n "[e2e] waiting for /health"
ready=0
for _ in $(seq 1 40); do
  if curl -fsS "${BASE}/health" >/dev/null 2>&1; then ready=1; echo " up"; break; fi
  echo -n "."
  sleep 0.5
done
if [ "$ready" -ne 1 ]; then
  echo " TIMEOUT"
  echo "---- uvicorn log ----" >&2
  cat /tmp/e2e_uvicorn.log >&2 || true
  exit 1
fi

# Self-identity check: confirm the responder is OUR app in mock mode, not some
# other process that happened to answer /health on this port. Our /readiness
# envelope always carries bridge=mock + mode=mock in mock/local no-cloud mode.
echo "[e2e] verifying responder identity (/readiness envelope)..."
RDY="$(curl -fsS "${BASE}/readiness")"
echo "$RDY" | grep -q '"bridge":"mock"' || { echo "FAIL: not the mock wizard bridge: $RDY"; cat /tmp/e2e_uvicorn.log >&2; exit 1; }
echo "$RDY" | grep -q '"mode":"mock"'   || { echo "FAIL: not WIZARD_MODE=mock: $RDY"; cat /tmp/e2e_uvicorn.log >&2; exit 1; }
echo "OK: responder is agentkit-wizard (bridge=mock, mode=mock)"

fail=0
check() { # check <desc> <curl-args...>
  local desc="$1"; shift
  local out
  out="$(curl -fsS "$@" 2>&1)" || { echo "FAIL: $desc (curl failed)"; echo "$out"; fail=1; return; }
  echo "OK: $desc"
}

echo "---- probes ----"
check "GET /health"            "${BASE}/health"
check "GET /readiness"         "${BASE}/readiness"

# Owner bootstrap: business routes under /api/wizard are behind the browser
# login gate (auth.public_path). Bootstrapping the owner issues a session cookie
# that subsequent authenticated probes carry.
echo "---- POST /api/auth/setup (bootstrap owner, save cookie) ----"
SETUP="$(curl -fsS -c "$JAR" -X POST "${BASE}/api/auth/setup" \
  -H 'Content-Type: application/json' \
  -d '{"password":"e2e-smoke-password-123","setup_token":"'"${WIZARD_OWNER_SETUP_TOKEN}"'"}')"
echo "$SETUP" | grep -q '"ok":true' && echo "OK: owner bootstrapped" || { echo "FAIL: setup: $SETUP"; fail=1; }

echo "---- GET /api/wizard/components (authenticated) ----"
COMP="$(curl -fsS -b "$JAR" "${BASE}/api/wizard/components")"
echo "$COMP" | grep -q '"components"' && echo "OK: /api/wizard/components lists catalog" || { echo "FAIL: /api/wizard/components: $COMP"; fail=1; }

echo "---- POST /invoke (mock step1) ----"
INV="$(curl -fsS -X POST "${BASE}/invoke" \
  -H 'Content-Type: application/json' \
  -d '{"input":"step1","user_id":"e2e","session_id":"e2e-1"}')"
echo "$INV" | grep -q '"reply"' && echo "OK: /invoke returns reply" || { echo "FAIL: /invoke no reply"; echo "$INV"; fail=1; }

echo "---- POST /run_sse (expect event: done) ----"
SSE="$(curl -fsS -N -X POST "${BASE}/run_sse" \
  -H 'Content-Type: application/json' \
  -d '{"message":"step2","user_id":"e2e","session_id":"e2e-2"}' || true)"
echo "$SSE" | grep -q '^event: done' && echo "OK: /run_sse emitted event: done" || {
  echo "FAIL: /run_sse missing event: done"; echo "$SSE"; fail=1; }
echo "$SSE" | grep -q '^event: delta' && echo "OK: /run_sse streamed at least one delta" || true

echo "---- shutdown ----"
if [ "$fail" -ne 0 ]; then
  echo "E2E SMOKE FAILED"
  exit 1
fi
echo "E2E SMOKE PASSED"
