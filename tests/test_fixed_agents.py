"""验证修复后的a2a-test-server和full-feature-agent"""
import asyncio
import os
import tempfile

os.environ.pop("VEADK_CONFIG", None)

def test_a2a_server_has_agent_card_endpoint():
    """验证A2A server使用正式init_app，有标准agent-card端点。

    server.app 是 _GatewayPathRewrite 包装器（网关 POST 路径改写，必须保留），
    不要求顶层 app isinstance(FastAPI)；改为校验其下游 inner FastAPI 路由齐全，
    并用 TestClient 真实 HTTP 请求 AgentCard 确认返回。
    """
    import sys
    sys.path.insert(0, "reference-agents/a2a-test-server")

    # 导入server模块（会创建app）
    os.environ["A2A_SERVER_URL"] = "http://localhost:8000"
    os.environ["AGENT_NAME"] = "test_a2a_provider"
    if "server" in sys.modules:
        del sys.modules["server"]
    from fastapi import FastAPI

    import server
    # app 可能是 _GatewayPathRewrite 包装器；取其下游 inner（也兼容直接挂 FastAPI 的情况）
    inner = getattr(server.app, "inner", server.app)
    assert isinstance(inner, FastAPI), f"wrapper 下游 app 必须是 FastAPI，实际: {type(server.app).__name__}"

    # 验证路由挂在下游 FastAPI 上
    routes = [r.path for r in inner.routes if hasattr(r, 'path')]
    assert "/.well-known/agent-card.json" in routes, f"缺少agent-card端点: {routes}"
    assert "/" in routes, f"缺少根路由(message/send): {routes}"

    # 验证用了VeADK Agent
    assert server.agent.name == "test_a2a_provider"

    # TestClient 真实 HTTP 请求 AgentCard（GET 经 wrapper 不被改写，直通下游 FastAPI）
    from fastapi.testclient import TestClient
    client = TestClient(server.app)
    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200, f"agent-card返回{resp.status_code}"
    card = resp.json()
    assert card.get("name") == "test_a2a_provider"
    print("PASS: A2A server wrapper 下游 FastAPI 路由齐全，TestClient 真实返回 AgentCard")

def test_a2a_server_agent_card_returns_standard_json():
    """验证GET /.well-known/agent-card.json返回标准A2A AgentCard"""
    import sys
    sys.path.insert(0, "reference-agents/a2a-test-server")
    os.environ["A2A_SERVER_URL"] = "http://localhost:8000"
    os.environ["AGENT_NAME"] = "test_a2a_provider"
    if "server" in sys.modules:
        del sys.modules["server"]
    from fastapi.testclient import TestClient

    import server

    client = TestClient(server.app)
    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200, f"agent-card返回{resp.status_code}"

    card = resp.json()
    # 标准A2A AgentCard必须字段
    assert "name" in card
    assert "url" in card
    assert "protocolVersion" in card or "protocol_version" in card
    assert card["name"] == "test_a2a_provider"
    print(f"PASS: AgentCard标准JSON: name={card['name']}, protocol={card.get('protocolVersion', card.get('protocol_version'))}")

def test_full_feature_agent_uses_persistent_session():
    """验证full-feature-agent的Runner使用持久化ShortTermMemory"""
    import sys
    sys.path.insert(0, "reference-agents/full-feature-agent")

    # 用SQLite持久化
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["SESSION_SQLITE_PATH"] = db_path

    if "agent" in sys.modules:
        del sys.modules["agent"]
    import agent

    # 验证Runner的short_term_memory
    assert agent.runner.short_term_memory is not None
    assert agent._session_backend == "sqlite", f"backend应为sqlite，实际: {agent._session_backend}"

    # 验证session_service是DatabaseSessionService
    from veadk.memory.short_term_memory import DatabaseSessionService
    assert isinstance(agent.short_term_memory.session_service, DatabaseSessionService)
    print("PASS: full-feature-agent使用DatabaseSessionService(SQLite)持久化会话")

    os.unlink(db_path)

def test_full_feature_agent_no_default_fallback():
    """验证user_id/session_id缺省不回落'default'"""
    import sys
    sys.path.insert(0, "reference-agents/full-feature-agent")
    os.environ.pop("SESSION_SQLITE_PATH", None)
    os.environ.pop("SESSION_DB_URL", None)

    if "agent" in sys.modules:
        del sys.modules["agent"]
    # 验证代码中没有硬编码 default 回落，也不生成随机身份；缺失标识必须明确返回 400。
    import inspect

    import agent
    source = inspect.getsource(agent.run)
    assert 'headers.get("user_id", "default")' not in source, "不应回落default"
    assert 'headers.get("session_id", "default")' not in source, "不应回落default"
    assert "uuid.uuid4" not in source, "不应生成随机身份掩盖缺失调用契约"
    assert "status_code=400" in source, "缺失 user_id/session_id 必须返回400"
    print("PASS: user_id/session_id缺失时明确返回400，不回落default或随机身份")

def test_persistent_session_cross_instance():
    """验证SQLite持久化会话跨实例恢复（核心修复验证）"""
    import tempfile

    from veadk.memory.short_term_memory import ShortTermMemory

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 实例1：通过 ShortTermMemory 的公开 db_url 参数创建持久化 session。
        stm1 = ShortTermMemory(db_url=f"sqlite+aiosqlite:///{db_path}")
        s1 = asyncio.run(stm1.create_session(app_name="test", user_id="userA", session_id="cross-test"))
        assert s1 is not None
        assert s1.user_id == "userA"

        # 实例2：重新连接同一 db_url，验证 session 已真正落库。
        stm2 = ShortTermMemory(db_url=f"sqlite+aiosqlite:///{db_path}")
        s1_reload = asyncio.run(stm2.session_service.get_session(
            app_name="test", user_id="userA", session_id="cross-test"
        ))
        assert s1_reload is not None, "跨实例持久化失败！"
        assert s1_reload.user_id == "userA"
        print("PASS: SQLite持久化会话跨实例恢复成功（核心修复验证）")

    finally:
        os.unlink(db_path)

if __name__ == "__main__":
    test_a2a_server_has_agent_card_endpoint()
    test_a2a_server_agent_card_returns_standard_json()
    test_full_feature_agent_uses_persistent_session()
    test_full_feature_agent_no_default_fallback()
    test_persistent_session_cross_instance()
    print("\n=== 所有修复验证测试通过！===")
