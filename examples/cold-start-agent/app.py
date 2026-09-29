"""AgentKit SDK 服务入口（AgentkitSimpleApp 装饰器式）。

契约（来自 skills/agentkit-sdk 与 skills/references/runner-entrypoint.md）：
- 入站 Header ``user_id`` / ``session_id``：缺任一 -> 返回 400，不回落默认值、不随机补值。
- 短期记忆显式持久化：``ShortTermMemory(db_url="sqlite+aiosqlite:///<绝对路径>")``，
  并传入 ``Runner(short_term_memory=...)``；断言底层为 ``DatabaseSessionService``。
- 本离线阶段不调用真实模型：入口用 Google ADK Graph（无模型 FunctionNode）做条件路由。
- ``/ping`` 返回 ``pong!``。
"""

from __future__ import annotations

import os
from pathlib import Path

from starlette.responses import JSONResponse

from agentkit.apps import AgentkitSimpleApp
from veadk.memory.short_term_memory import DatabaseSessionService, ShortTermMemory

from agent import build_agent
from workflow import run_routing

_BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = _BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 绝对路径 SQLite（4 斜杠）；可用环境变量覆盖，便于测试指向临时库。
_DEFAULT_DB = DATA_DIR / "sessions.db"
_SESSION_DB_URL = os.getenv(
    "SESSION_DB_URL", f"sqlite+aiosqlite:///{_DEFAULT_DB}"
)

# 显式持久化短期记忆。
short_term_memory = ShortTermMemory(db_url=_SESSION_DB_URL)
assert isinstance(short_term_memory.session_service, DatabaseSessionService), (
    "短期记忆必须是持久化 DatabaseSessionService，不能是 InMemorySessionService"
)

agent = build_agent()
app_container = AgentkitSimpleApp()

from veadk import Runner  # noqa: E402

runner = Runner(
    agent=agent,
    app_name="cold_start_demo",
    short_term_memory=short_term_memory,  # 显式传入持久化 STM
)


@app_container.entrypoint
async def run(payload: dict, headers: dict):
    """Agent 入口：Header 给 user_id/session_id，Body 给 prompt。"""
    user_id = headers.get("user_id")
    session_id = headers.get("session_id")
    # 硬契约：缺任一标识 -> 400，不回落 default、不生成随机 id。
    if not user_id or not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "user_id and session_id headers are required"},
        )

    prompt = (payload or {}).get("prompt", "")

    # D1 修复：Graph 直接复用持久化 session_service（DatabaseSessionService），
    # 节点对 session.state 的读写落 sqlite；run_routing 内部 get-or-create。
    result = await run_routing(
        prompt,
        user_id=user_id,
        session_id=session_id,
        session_service=runner.short_term_memory.session_service,
    )
    return result


@app_container.ping
def ping() -> str:
    return "pong!"


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    app_container.run(host=host, port=port)


if __name__ == "__main__":
    main()
