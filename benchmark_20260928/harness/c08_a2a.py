"""Component: **agentkit-a2a-registry** (A2A center / Registry).

Per the Skill:
  * AgentCard (Google A2A protocol) exposed at ``GET /.well-known/agent-card.json``;
    runtime messages over JSON-RPC 2.0 ``message/send``.
  * Supported ``protocolVersion``: 0.2.6 / 0.3.0; ``protocolBinding`` = JSONRPC.
  * Provider containers MUST use ``veadk.a2a.ve_a2a_server.init_app()`` — not a hand-rolled
    HTTP handler — and add a ``_GatewayPathRewrite`` ASGI middleware that rewrites POST path to
    ``/`` (the gateway double-prefixes ``/runtime/<id>``).

We model the AgentCard schema, the JSON-RPC message/send contract, and the path-rewrite
middleware. Standing up a real A2A FastAPI server / registering to a cloud space is a
CloudBoundary.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class AgentCard:
    name: str
    description: str
    version: str = "1.0.0"
    protocolVersion: str = "0.3.0"
    url: str = "http://localhost:8000"
    skills: list[dict] = field(default_factory=lambda: [
        {"id": "chat", "name": "chat", "description": "general chat"}])

    def to_dict(self) -> dict:
        return {
            "name": self.name, "description": self.description, "version": self.version,
            "protocolVersion": self.protocolVersion,
            "supportedInterfaces": [{"url": self.url, "protocolBinding": "JSONRPC"}],
            "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain"],
            "skills": self.skills,
        }

    def validate(self) -> None:
        if self.protocolVersion not in ("0.2.6", "0.3.0"):
            raise ValueError("protocolVersion must be 0.2.6 or 0.3.0")


class A2AJsonRpc:
    """Local JSON-RPC handler for ``message/send`` / ``initialize``."""

    def __init__(self, card: AgentCard):
        self.card = card

    def handle(self, body: str) -> str:
        req = json.loads(body)
        method, rid = req.get("method"), req.get("id")
        if method == "initialize":
            return json.dumps({"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": self.card.protocolVersion,
                "agentCard": self.card.to_dict()}})
        if method == "message/send":
            text = req.get("params", {}).get("message", {}).get("parts", [{}])[0].get("text", "")
            return json.dumps({"jsonrpc": "2.0", "id": rid, "result": {
                "message": {"role": "assistant",
                            "parts": [{"type": "text",
                                       "text": f"[{self.card.name}] received: {text}"}]}}})
        return json.dumps({"jsonrpc": "2.0", "id": rid,
                           "error": {"code": -32601, "message": "unknown method"}})


class GatewayPathRewrite:
    """ASGI middleware from the Skill: rewrite every POST path to '/'."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("method") == "POST":
            scope = dict(scope)
            scope["path"] = "/"
            scope["raw_path"] = b"/"
        await self.inner(scope, receive, send)
