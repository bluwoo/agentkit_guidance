#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 14 个 Skill 中出现的全部 25 个第三方 import。
方法：在 venv 中逐条执行 `from xxx import yyy`，捕获成功/失败。
约束：不触发 LLM / 云资源调用。
"""
from __future__ import annotations

import importlib
import json
import sys
import traceback
from typing import Any

# 25 个 import 语句（修正后的完整列表，含 from google.adk import Context）
IMPORT_CASES: list[dict[str, str]] = [
    {"id": "01", "stmt": "from [BASE-ADK] import Agent, Runner", "desc": "[BASE-ADK] 顶层 Agent + Runner"},
    {"id": "02", "stmt": "from [BASE-ADK] import Agent", "desc": "[BASE-ADK] 顶层 Agent（单独）"},
    {"id": "03", "stmt": "from [PRODUCT].apps import [PRODUCT]SimpleApp", "desc": "[PRODUCT] 简单应用"},
    {"id": "04", "stmt": "from [PRODUCT].apps import [PRODUCT]AgentServerApp", "desc": "[PRODUCT] Agent 服务端应用"},
    {"id": "05", "stmt": "from google.genai import types", "desc": "Google GenAI types"},
    {"id": "06", "stmt": "from google.adk.agents import RunConfig", "desc": "ADK RunConfig"},
    {"id": "07", "stmt": "from google.adk.agents.run_config import StreamingMode", "desc": "ADK StreamingMode 枚举"},
    {"id": "08", "stmt": "from google.adk.agents import SequentialAgent", "desc": "ADK 顺序编排"},
    {"id": "09", "stmt": "from google.adk.agents import ParallelAgent", "desc": "ADK 并行编排"},
    {"id": "10", "stmt": "from google.adk.agents import LoopAgent", "desc": "ADK 循环编排"},
    {"id": "11", "stmt": "from google.adk import Agent", "desc": "ADK 顶层 Agent"},
    {"id": "12", "stmt": "from google.adk import Workflow", "desc": "ADK 顶层 Workflow"},
    {"id": "13", "stmt": "from google.adk import Event", "desc": "ADK 顶层 Event"},
    {"id": "14", "stmt": "from google.adk.workflow import node", "desc": "ADK workflow node 装饰器"},
    {"id": "15", "stmt": "from google.adk.agents.remote_a2a_agent import RemoteA2aAgent", "desc": "ADK 远程 A2A Agent"},
    {"id": "16", "stmt": "from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset", "desc": "ADK MCP 工具集"},
    {"id": "17", "stmt": "from google.adk.tools.mcp_tool.mcp_toolset import StreamableHTTPConnectionParams", "desc": "ADK MCP 流式 HTTP 连接参数"},
    {"id": "18", "stmt": "from [BASE-ADK].knowledgebase import KnowledgeBase", "desc": "[BASE-ADK] 知识库"},
    {"id": "19", "stmt": "from [BASE-ADK].tools.builtin_tools.run_code import run_code", "desc": "[BASE-ADK] 内置 run_code 工具"},
    {"id": "20", "stmt": "from [BASE-ADK].memory.long_term_memory import LongTermMemory", "desc": "[BASE-ADK] 长期记忆"},
    {"id": "21", "stmt": "from [BASE-ADK].integrations.[PRODUCT] import create_[PRODUCT]_app", "desc": "[BASE-ADK] 创建 [PRODUCT] 应用"},
    {"id": "22", "stmt": "from [BASE-ADK].integrations.[PRODUCT] import run_[PRODUCT]_app", "desc": "[BASE-ADK] 运行 [PRODUCT] 应用"},
    {"id": "23", "stmt": "from [PRODUCT].auth._openapi import OpenApiClient", "desc": "[PRODUCT] OpenAPI 客户端（私有模块）"},
    {"id": "24", "stmt": "from [PRODUCT].sdk.mcp.client import [PRODUCT]MCPClient", "desc": "[PRODUCT] MCP 客户端"},
    {"id": "25", "stmt": "from google.adk import Context", "desc": "ADK Context（顶层 re-export，修正点）"},
]


def run_import_tests() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0
    g: dict[str, Any] = {}
    for case in IMPORT_CASES:
        try:
            exec(case["stmt"], g)
            results.append({
                "id": case["id"],
                "stmt": case["stmt"],
                "desc": case["desc"],
                "method": "import",
                "passed": True,
                "error": None,
            })
            passed += 1
        except Exception as e:  # noqa: BLE001
            results.append({
                "id": case["id"],
                "stmt": case["stmt"],
                "desc": case["desc"],
                "method": "import",
                "passed": False,
                "error": f"{type(e).__name__}: {e}",
            })
            failed += 1
    return {
        "suite": "test_imports",
        "total": len(IMPORT_CASES),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


if __name__ == "__main__":
    report = run_import_tests()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["failed"] == 0 else 1)
