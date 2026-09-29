"""Shared fixtures / canned payloads for shim + api tests.

Imported by tests as needed; not a pytest plugin (conftest.py owns fixtures).
"""
from __future__ import annotations

# A minimal InvokeRequest payload shaped like AgentkitSimpleApp's body.
INVOKE_REQUEST = {
    "session_id": "fixture-session",
    "user_id": "fixture-user",
    "message": "step1 这是一段来自 fixture 的请求",
}

# A canned GoalCard draft.
GOAL_CARD = {
    "name": "工单聚类助手",
    "target_user": "运营同学",
    "task": "把客户反馈聚类成工单并起草回复",
    "typical_input": "一段自由文本反馈",
    "expected_output": "聚类结果 + 每条草稿回复",
    "non_goals": ["不自动发送回复"],
    "long_running": False,
    "classification": "tool_call",
}

# A minimal two-node Topology used by validate tests.
TOPOLOGY = {
    "nodes": [
        {"component_id": "agent:target", "kind": "agent", "label": "目标 Agent"},
        {"component_id": "gateway:mcp", "kind": "gateway", "label": "Gateway/MCP"},
    ],
    "edges": [
        {"edge_id": "e1", "source": "agent:target", "target": "gateway:mcp", "type": "sync"},
    ],
}
