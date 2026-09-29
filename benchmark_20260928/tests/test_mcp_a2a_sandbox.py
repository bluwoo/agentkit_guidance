"""MCP gateway handshake + A2A AgentCard/JSON-RPC + sandbox session reuse."""
import asyncio
import json

import pytest

from harness.c07_mcp_gateway import LocalMCPServer, LocalMCPTool, Unauthorized
from harness.c08_a2a import AgentCard, A2AJsonRpc, GatewayPathRewrite
from harness.c09_sandbox import LocalSandbox


# ---- MCP ----
def _server():
    s = LocalMCPServer(auth_key="secret")
    s.add_tool(LocalMCPTool(name="echo", description="echo tool",
                            handler=lambda a: f"echo:{a.get('msg','')}"))
    return s


def test_mcp_no_key_401():
    s = _server()
    with pytest.raises(Unauthorized):
        s.handle(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                             "params": {"protocolVersion": "2024-11-05", "capabilities": {}}}),
                 headers={})


def test_mcp_four_layer_acceptance():
    s = _server()
    res = asyncio.run(s.four_layer_acceptance(headers={"Authorization": "Bearer secret"}))
    assert res == {"initialize_ok": True, "tools_visible": 1,
                   "tool_is_error": False, "backend_executed": True}


# ---- A2A ----
def test_agentcard_validates_and_serializes():
    card = AgentCard(name="weather", description="weather provider")
    card.validate()
    d = card.to_dict()
    assert d["protocolVersion"] == "0.3.0"
    assert d["supportedInterfaces"][0]["protocolBinding"] == "JSONRPC"


def test_agentcard_bad_protocol_version():
    with pytest.raises(ValueError):
        AgentCard(name="x", description="y", protocolVersion="0.1.0").validate()


def test_a2a_message_send():
    h = A2AJsonRpc(AgentCard(name="w", description="d"))
    out = json.loads(h.handle(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "message/send",
                                         "params": {"message": {"parts": [{"text": "北京天气"}]}}})))
    assert "北京天气" in out["result"]["message"]["parts"][0]["text"]


def test_gateway_path_rewrite():
    seen = {}

    async def inner(scope, receive, send):
        seen["path"] = scope["path"]

    import asyncio
    async def run():
        mw = GatewayPathRewrite(inner)
        await mw({"type": "http", "method": "POST", "path": "/runtime/abc/card"}, None, None)
        await mw({"type": "http", "method": "GET", "path": "/.well-known/agent-card.json"}, None, None)
    asyncio.run(run())
    # second GET call overwrites, but the POST branch rewrote to '/'
    assert seen["path"] == "/.well-known/agent-card.json"  # GET untouched


# ---- Sandbox ----
def test_sandbox_exec_and_session_reuse():
    sb = LocalSandbox()
    sb.exec_code("sessA", "open('note.txt','w').write('hello-reuse')")
    r = sb.exec_code("sessA", "print(open('note.txt').read())")
    assert r["exit_code"] == 0 and "hello-reuse" in r["stdout"]


def test_sandbox_isolation_between_sessions():
    sb = LocalSandbox()
    sb.exec_code("sessB", "open('x.txt','w').write('B')")
    r = sb.exec_code("sessC", "import os; print(os.path.exists('x.txt'))")
    # different workspace dir => file from sessB not visible in sessC
    assert "False" in r["stdout"]
