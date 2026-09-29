#!/usr/bin/env bash
# 离线启动 AgentKit 服务（本地 sqlite，无云凭据）。
set -euo pipefail
cd "$(dirname "$0")"
# 优先使用本工程 venv；否则回退到系统 python3。
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
exec python app.py
