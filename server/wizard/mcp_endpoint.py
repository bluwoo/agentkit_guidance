"""Native MCP streamable-HTTP endpoint backed by the Hermes bridge.

Mounted at `/mcp` on the FastAPI app. Exposes one tool, ``invoke``, which calls
the existing Hermes bridge and returns the agent reply. Keeps OTel tracing: each
tool call starts a child span under the request root.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from opentelemetry import trace

_allowed_hosts = [
    item.strip()
    for item in os.environ.get(
        "WIZARD_MCP_ALLOWED_HOSTS", "127.0.0.1,localhost,127.0.0.1:*"
    ).split(",")
    if item.strip()
]
mcp = FastMCP(
    "agentkit-wizard",
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_allowed_hosts,
        allowed_origins=[],
    ),
)
_mcp_app = mcp.streamable_http_app()

_bridge: Any = None


def set_bridge(bridge: Any) -> None:
    global _bridge
    _bridge = bridge


def get_bridge() -> Any:
    return _bridge


@mcp.tool()
def invoke(message: str, session_id: str = "", user_id: str = "mcp") -> dict[str, Any]:
    """Send a message to the AgentKit Wizard (Hermes) and get a reply.

    Args:
        message: The user message / prompt to the agent.
        session_id: Optional conversation session id.
        user_id: Optional caller identity.
    """
    bridge = get_bridge()
    if bridge is None:
        return {"error": "bridge not initialised", "reply": "", "trace_id": None}

    tracer = trace.get_tracer("wizard.mcp")
    with tracer.start_as_current_span("mcp.invoke") as span:
        span.set_attribute("mcp.tool", "invoke")
        if not session_id:
            session_id = bridge.new_session("", user_id)
        # fastmcp runs sync tools in a thread pool, so the blocking bridge.turn
        # does not block the event loop.
        result = bridge.turn(session_id, user_id, message)
        span.set_attribute("wizard.trace_id", result.get("trace_id") or "")
        return {
            "reply": result.get("reply", ""),
            "trace_id": result.get("trace_id"),
            "session_id": session_id,
            "failed": bool(result.get("failed")),
        }


@asynccontextmanager
async def mcp_lifespan():
    """Run the FastMCP session manager inside the parent FastAPI lifespan."""
    async with _mcp_app.router.lifespan_context(_mcp_app):
        yield


def mount_mcp(app) -> None:
    """Register the native streamable-HTTP route at exactly ``/mcp``."""
    app.router.routes.extend(_mcp_app.routes)
