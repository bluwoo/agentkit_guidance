"""D1 持久化贯穿 HTTP / 隔离 / 重建恢复（L2 离线真跑）+ 本地 MCP 往返。"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from workflow import APP_NAME


def _invoke(client, user, session, prompt):
    return client.post(
        "/invoke",
        headers={"user_id": user, "session_id": session},
        json={"prompt": prompt},
    )


def test_http_two_turn_state_across_requests(app_container):
    """同一 user+session 两轮 HTTP：状态累计 turn=1 -> turn=2。"""
    container, _runner, _db = app_container
    client = TestClient(container)
    r1 = _invoke(client, "alice", "sess-A", "I found a bug")
    r2 = _invoke(client, "alice", "sess-A", "I need help")
    assert "turn=1" in r1.json()
    assert "turn=2" in r2.json()


def test_rebuilt_instance_recovers_state(app_container):
    """Graph 状态真正落 sqlite：重建 ShortTermMemory 后仍能召回 turn_count/history。"""
    container, runner, db = app_container
    client = TestClient(container)
    _invoke(client, "alice", "sess-persist", "I found a bug")
    _invoke(client, "alice", "sess-persist", "I need help")

    # “重建实例”：同一 sqlite 路径重新构造 ShortTermMemory（不换库）。
    from veadk.memory.short_term_memory import ShortTermMemory

    rebuilt = ShortTermMemory(db_url=f"sqlite+aiosqlite:///{db}")
    import asyncio

    async def _get():
        return await rebuilt.session_service.get_session(
            app_name=APP_NAME, user_id="alice", session_id="sess-persist"
        )

    sess = asyncio.run(_get())
    assert sess is not None
    assert sess.state.get("turn_count") == 2
    assert len(sess.state.get("history", [])) == 2
    assert sess.state.get("last_branch") == "SUPPORT"


def test_same_user_new_session_is_fresh(app_container):
    """同一 user 但新 session_id：轮次从 1 开始，看不到旧会话历史。"""
    container, runner, _db = app_container
    client = TestClient(container)
    _invoke(client, "alice", "sess-old", "I found a bug")
    r_new = _invoke(client, "alice", "sess-new", "I found a bug again")
    assert "turn=1" in r_new.json()


def test_different_user_isolation(app_container):
    """异 user 用同 session_id 也取不到该会话（按 user+session 隔离）。"""
    container, runner, _db = app_container
    client = TestClient(container)
    _invoke(client, "alice", "sess-x", "I found a bug")

    import asyncio

    async def _get(uid):
        return await runner.short_term_memory.session_service.get_session(
            app_name=APP_NAME, user_id=uid, session_id="sess-x"
        )

    assert asyncio.run(_get("alice")) is not None
    assert asyncio.run(_get("bob")) is None


@pytest.mark.asyncio
async def test_local_mcp_roundtrip_echo():
    from mcp_client import call_echo

    out = await call_echo("hello-mcp")
    assert "echo" in out["tool_names"]
    assert any("hello-mcp" in c for c in out["content"]), out["content"]


@pytest.mark.asyncio
async def test_local_mcp_roundtrip_add():
    from mcp_client import call_add

    out = await call_add(40, 2)
    assert any("42" in c for c in out["content"]), out["content"]
