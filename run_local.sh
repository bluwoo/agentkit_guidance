#!/usr/bin/env bash
# Start the AgentKit Wizard locally (backend serving the built frontend).
# Usage: bash run_local.sh [port]
set -euo pipefail
cd "$(dirname "$0")"
PORT="${1:-8000}"
PY=/tmp/agentkit_verify_venv/bin/python
export WIZARD_DATA_DIR="${WIZARD_DATA_DIR:-$PWD/wizard_data}"
export SERVE_FRONTEND_DIST="$PWD/web/dist"
mkdir -p "$WIZARD_DATA_DIR"
echo "AgentKit Wizard -> http://127.0.0.1:${PORT}  (mock Hermes bridge, no LLM/APMPlus creds needed)"
exec "$PY" -m uvicorn server.wizard.main:app --host 0.0.0.0 --port "$PORT"
