"""测试A2A server正式实现：AgentCard端点 + message/send标准schema"""
import json
import os

# 不加载.env
os.environ.pop("VEADK_CONFIG", None)

def test_get_agent_card_returns_valid_card():
    """验证get_agent_card生成标准AgentCard"""
    from veadk import Agent
    from veadk.a2a.agent_card import get_agent_card

    agent = Agent(name="test_a2a_agent", instruction="test")
    card = get_agent_card(agent, url="https://example.com/a2a", version="1.0.0")

    # 标准A2A AgentCard必须字段
    assert card.name == "test_a2a_agent"
    assert card.url == "https://example.com/a2a"
    assert card.version == "1.0.0"
    assert card.protocol_version is not None  # 必须有protocolVersion
    assert hasattr(card, 'capabilities')
    print(f"AgentCard: name={card.name}, url={card.url}, protocol={card.protocol_version}")

def test_init_app_creates_fastapi_with_routes():
    """验证init_app创建FastAPI app并包含agent-card和message/send路由"""
    from veadk import Agent
    from veadk.a2a.ve_a2a_server import init_app
    from veadk.memory.short_term_memory import InMemorySessionService, ShortTermMemory

    agent = Agent(name="test_a2a_agent", instruction="test", model_name="doubao-seed-2-0-lite-260428")
    stm = ShortTermMemory(session_service=InMemorySessionService())

    app = init_app(
        server_url="https://example.com/a2a",
        app_name="test_app",
        agent=agent,
        short_term_memory=stm,
    )

    # FastAPI app必须有路由
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    print(f"Routes: {routes}")

    # 必须包含 /.well-known/agent-card.json (GET)
    assert any('agent-card' in r for r in routes), f"缺少agent-card路由: {routes}"
    # 必须包含 / (POST message/send)
    assert any(r == '/' for r in routes), f"缺少根路由: {routes}"

def test_agent_card_endpoint_returns_200():
    """验证GET /.well-known/agent-card.json返回200和标准JSON"""
    from fastapi.testclient import TestClient
    from veadk import Agent
    from veadk.a2a.ve_a2a_server import init_app
    from veadk.memory.short_term_memory import InMemorySessionService, ShortTermMemory

    agent = Agent(name="test_a2a_agent", instruction="test", model_name="doubao-seed-2-0-lite-260428")
    stm = ShortTermMemory(session_service=InMemorySessionService())
    app = init_app("https://example.com/a2a", "test_app", agent, stm)
    client = TestClient(app)

    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200, f"agent-card返回{resp.status_code}: {resp.text}"

    card = resp.json()
    assert 'name' in card
    assert 'url' in card
    assert 'protocolVersion' in card or 'protocol_version' in card
    print(f"AgentCard endpoint: {json.dumps(card, indent=2, default=str)[:300]}")

if __name__ == "__main__":
    test_get_agent_card_returns_valid_card()
    print("PASS: test_get_agent_card_returns_valid_card")
    test_init_app_creates_fastapi_with_routes()
    print("PASS: test_init_app_creates_fastapi_with_routes")
    test_agent_card_endpoint_returns_200()
    print("PASS: test_agent_card_endpoint_returns_200")
    print("\n所有A2A server测试通过!")
