"""Component: **agentkit-gateway-mcp** (gateway / MCP).

Per the Skill:
  * ``MCPToolset(connection_params=StreamableHTTPConnectionParams(url=MCP_ENDPOINT,
    headers={"Authorization": f"Bearer {MCP_AUTH_KEY}"})`` attaches MCP tools to an Agent.
  * Inbound auth: ApiKey (Bearer) or CustomJWT — mutually exclusive per service.
  * Four-layer acceptance: ① initialize -> ② tools/list -> ③ tools/call (isError=false) ->
    ④ real backend execution. No/wrong key must yield 401.

The real gateway lives at MCP_ENDPOINT (AK/SK managed, CloudBoundary). We run a local
in-process JSON-RPC MCP stub that reproduces the handshake + tools/list + tools/call contract
and the Bearer auth semantics.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


class Unauthorized(Exception):
    pass


@dataclass
class LocalMCPTool:
    name: str
    description: str
    schema: dict = field(default_factory=lambda: {"type": "object", "properties": {}})
    handler: Any = None

    def run(self, args: dict) -> str:
        if self.handler is None:
            return "ok"
        return self.handler(args)


class LocalMCPServer:
    """In-process MCP server stub implementing JSON-RPC 2.0 over the Skill contract."""

    PROTOCOL_VERSION = "2024-11-05"  # one of the accepted legacy handshake versions

    def __init__(self, auth_key: str):
        self.auth_key = auth_key
        self.tools: dict[str, LocalMCPTool] = {}
        self.handshakes = 0

    def add_tool(self, tool: LocalMCPTool):
        self.tools[tool.name] = tool

    def _check_auth(self, headers: dict):
        expected = f"Bearer {self.auth_key}"
        if headers.get("Authorization") != expected:
            raise Unauthorized("missing/invalid bearer token -> 401")

    def handle(self, body: str, headers: dict) -> str:
        self._check_auth(headers)  # layer: inbound auth
        req = json.loads(body)
        method, rid = req.get("method"), req.get("id")
        if method == "initialize":
            self.handshakes += 1
            return json.dumps({"jsonrpc": "2.0", "id": rid,
                               "result": {"protocolVersion": self.PROTOCOL_VERSION,
                                          "capabilities": {"tools": {}}}})
        if method == "tools/list":
            return json.dumps({"jsonrpc": "2.0", "id": rid, "result": {"tools": [
                {"name": t.name, "description": t.description, "inputSchema": t.schema}
                for t in self.tools.values()]}})
        if method == "tools/call":
            params = req.get("params", {})
            tool = self.tools.get(params.get("name"))
            if tool is None:
                return json.dumps({"jsonrpc": "2.0", "id": rid,
                                   "error": {"code": -32601, "message": "no such tool"}})
            out = tool.run(params.get("arguments", {}))
            return json.dumps({"jsonrpc": "2.0", "id": rid,
                               "result": {"content": [{"type": "text", "text": out}],
                                          "isError": False}})
        return json.dumps({"jsonrpc": "2.0", "id": rid,
                           "error": {"code": -32601, "message": "unknown method"}})

    async def four_layer_acceptance(self, headers: dict) -> dict:
        """Runs ① initialize -> ② tools/list -> ③ tools/call -> ④ backend (local)."""
        r1 = json.loads(self.handle(
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": self.PROTOCOL_VERSION, "capabilities": {}}}),
            headers))
        r2 = json.loads(self.handle(
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}), headers))
        first_tool = r2["result"]["tools"][0]["name"] if r2["result"]["tools"] else None
        r3 = json.loads(self.handle(
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": first_tool, "arguments": {}}}), headers))
        return {
            "initialize_ok": "result" in r1,
            "tools_visible": len(r2["result"]["tools"]),
            "tool_is_error": r3["result"]["isError"],
            "backend_executed": first_tool is not None,
        }
