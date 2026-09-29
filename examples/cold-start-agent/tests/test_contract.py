"""契约测试（L1 静态 + L2 离线真跑）。

- /ping 精确返回 {"status":"pong!"}
- /invoke 缺 user_id 或 session_id（含只缺其一）-> 400，不回落默认值
- /invoke 带齐 header -> 经 Graph 条件路由返回分支文本（含 turn=）
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_ping_exact(app_container):
    container, _runner, _db = app_container
    client = TestClient(container)
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"status": "pong!"}


def test_invoke_missing_identity_returns_400(app_container):
    container, _runner, _db = app_container
    client = TestClient(container)

    # 两个 header 都缺
    r = client.post("/invoke", json={"prompt": "I found a bug"})
    assert r.status_code == 400, r.status_code

    # 只缺 session_id（有 user_id）
    r = client.post(
        "/invoke",
        headers={"user_id": "alice"},
        json={"prompt": "I found a bug"},
    )
    assert r.status_code == 400, r.status_code

    # 只缺 user_id（有 session_id）——审计 D5 补的负例
    r = client.post(
        "/invoke",
        headers={"session_id": "sess-x"},
        json={"prompt": "I found a bug"},
    )
    assert r.status_code == 400, r.status_code


def test_invoke_happy_path_routes(app_container):
    container, _runner, _db = app_container
    client = TestClient(container)
    r = client.post(
        "/invoke",
        headers={"user_id": "alice", "session_id": "sess-1"},
        json={"prompt": "I found a bug in login"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "[BUG]" in body
    assert "turn=1" in body
