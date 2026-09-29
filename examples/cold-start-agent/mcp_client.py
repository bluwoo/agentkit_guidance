"""本地 MCP 客户端：经 stdio 完成真实 MCP 四层验收的前三层（离线）。

initialize 握手 -> tools/list -> tools/call，均通过 ``mcp`` SDK 的
``ClientSession`` + ``stdio_client`` 与本地子进程 ``mcp_server.py`` 通信。
"""

from __future__ import annotations

import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_SERVER = Path(__file__).resolve().parent / "mcp_server.py"


def _params() -> StdioServerParameters:
    return StdioServerParameters(command=sys.executable, args=[str(_SERVER)])


async def call_echo(text: str) -> dict:
    async with stdio_client(_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()                      # ① 握手
            tools = await session.list_tools()             # ② tools/list
            tool_names = [t.name for t in tools.tools]
            result = await session.call_tool(               # ③ tools/call
                "echo", {"text": text}
            )
            return {
                "tool_names": tool_names,
                "content": [getattr(p, "text", str(p)) for p in result.content],
            }


async def call_add(a: int, b: int) -> dict:
    async with stdio_client(_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("add", {"a": a, "b": b})
            return {"content": [getattr(p, "text", str(p)) for p in result.content]}
