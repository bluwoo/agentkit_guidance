"""Graph 条件路由测试（L2 离线真跑）：三分支精确断言 + 路由表含 DEFAULT_ROUTE。"""

from __future__ import annotations

import pytest
from google.adk.sessions import InMemorySessionService

from workflow import APP_NAME, run_routing


@pytest.fixture()
def mem_svc():
    return InMemorySessionService()


@pytest.mark.asyncio
async def test_bug_branch(mem_svc):
    out = await run_routing(
        "I found a bug in login", user_id="u", session_id="s", session_service=mem_svc
    )
    assert out == "[BUG] 已登记缺陷单: I found a bug in login | turn=1"


@pytest.mark.asyncio
async def test_support_branch(mem_svc):
    out = await run_routing(
        "I need help with setup", user_id="u", session_id="s", session_service=mem_svc
    )
    assert out == "[SUPPORT] 已转人工支持: I need help with setup | turn=1"


@pytest.mark.asyncio
async def test_default_route_other(mem_svc):
    out = await run_routing(
        "just some general feedback", user_id="u", session_id="s", session_service=mem_svc
    )
    assert out == "[OTHER] 已归档通用队列: just some general feedback | turn=1"


@pytest.mark.asyncio
async def test_two_turn_state_accumulates(mem_svc):
    await run_routing("found a bug", user_id="u", session_id="s", session_service=mem_svc)
    out2 = await run_routing("need help", user_id="u", session_id="s", session_service=mem_svc)
    assert "turn=2" in out2


def test_routing_table_has_default_route():
    from google.adk.workflow import DEFAULT_ROUTE

    from workflow import routing_workflow

    classify_edge = routing_workflow.edges[1]
    mapping = classify_edge[1]
    assert "BUG" in mapping and "SUPPORT" in mapping
    assert DEFAULT_ROUTE in mapping
