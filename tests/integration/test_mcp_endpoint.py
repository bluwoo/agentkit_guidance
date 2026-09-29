"""Integration: native MCP streamable-HTTP handshake on /mcp."""
from __future__ import annotations

import os

os.environ.setdefault("WIZARD_MODE", "mock")

import anyio

from server.wizard.mcp_endpoint import mcp, set_bridge


class FakeBridge:
    name = "fake"

    def new_session(self, session_id="", user_id=""):
        return session_id or "sess-1"

    def turn(self, session_id, user_id, message, on_delta=None):
        return {"reply": f"echo:{message}", "trace_id": "abc123", "failed": False}


def test_mcp_tools_list_and_call():
    set_bridge(FakeBridge())

    names = anyio.run(mcp.list_tools)
    assert "invoke" in [t.name for t in names]

    result = anyio.run(mcp.call_tool, "invoke", {"message": "hello"})
    assert "echo:hello" in str(result)


def test_mcp_mount_returns_handler():
    from server.wizard.main import create_app
    app = create_app()
    routes = [getattr(r, "path", "") for r in app.routes]
    assert any("/mcp" in p for p in routes)
