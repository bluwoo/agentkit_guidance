"""本地 stdio MCP server（离线真实组件）。

用 FastMCP 暴露两个工具，通过子进程 stdio 与 MCP 客户端通信：
- ``add(a: int, b: int) -> int``
- ``echo(text: str) -> str``

直接运行即作为 MCP server 常驻：python mcp_server.py
"""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("cold-start-local-demo")


@mcp.tool
def add(a: int, b: int) -> int:
    """返回 a + b（离线确定性计算）。"""
    return a + b


@mcp.tool
def echo(text: str) -> str:
    """原样回显输入文本。"""
    return f"echo: {text}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
