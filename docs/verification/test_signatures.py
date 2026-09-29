#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试关键函数/类签名。
方法：用 inspect.signature() 实际获取签名，并验证关键参数是否存在、默认值是否正确。
不只测方法名是否存在，要测参数绑定（bind 绑定 + 默认值检查）。
约束：不实例化需要 LLM/云资源的对象；仅做静态签名检查。
"""
from __future__ import annotations

import inspect
import json
import sys
from typing import Any


def _check(sig: inspect.Signature, name: str, expected: dict[str, dict]) -> list[dict[str, Any]]:
    """对单个签名逐项断言：参数存在 + 默认值匹配。"""
    out = []
    for param_name, spec in expected.items():
        if param_name not in sig.parameters:
            out.append({
                "check": f"{name}.{param_name}",
                "passed": False,
                "detail": f"缺少参数 {param_name}",
            })
            continue
        p = sig.parameters[param_name]
        # 默认值检查
        if "default" in spec:
            expected_default = spec["default"]
            actual_default = p.default
            # 对动态默认值（如 lambda/工厂）用标记字符串比较
            if expected_default == "<dynamic>":
                ok = actual_default is not inspect.Parameter.empty
            else:
                ok = actual_default == expected_default
            out.append({
                "check": f"{name}.{param_name} 默认值",
                "passed": bool(ok),
                "detail": f"期望 {expected_default!r}, 实际 {actual_default!r}",
            })
        # 是否必填（无默认值）
        if spec.get("required"):
            ok = p.default is inspect.Parameter.empty
            out.append({
                "check": f"{name}.{param_name} 必填",
                "passed": bool(ok),
                "detail": f"实际 default={p.default!r}",
            })
        # kind 检查（KEYWORD_ONLY 等）
        if "kind" in spec:
            kind_map = {
                "KEYWORD_ONLY": inspect.Parameter.KEYWORD_ONLY,
                "POSITIONAL_OR_KEYWORD": inspect.Parameter.POSITIONAL_OR_KEYWORD,
                "VAR_KEYWORD": inspect.Parameter.VAR_KEYWORD,
                "VAR_POSITIONAL": inspect.Parameter.VAR_POSITIONAL,
            }
            expected_kind = kind_map[spec["kind"]]
            ok = p.kind == expected_kind
            out.append({
                "check": f"{name}.{param_name} kind",
                "passed": bool(ok),
                "detail": f"期望 {spec['kind']}, 实际 {p.kind}",
            })
    return out


def run_signature_tests() -> dict[str, Any]:
    from [BASE-ADK] import Agent, Runner
    from google.adk.runners import Runner as ADKRunner
    from [PRODUCT].apps import [PRODUCT]SimpleApp, [PRODUCT]AgentServerApp
    from [BASE-ADK].integrations.[PRODUCT] import create_[PRODUCT]_app, run_[PRODUCT]_app
    from google.adk.agents import RunConfig
    from google.adk.agents.run_config import StreamingMode

    all_checks: list[dict[str, Any]] = []

    # 1. Runner.__init__（[BASE-ADK]）
    sig = inspect.signature(Runner.__init__)
    all_checks += _check(sig, "Runner.__init__", {
        "agent": {"default": None},
        "short_term_memory": {"default": None},
        "app_name": {"default": None},
        "user_id": {"default": "[BASE-ADK]_default_user"},
        "upload_inline_data_to_tos": {"default": False},
    })

    # 2. Runner.run（[BASE-ADK] 覆盖版）
    sig = inspect.signature(Runner.run)
    all_checks += _check(sig, "Runner.run", {
        "messages": {"required": True},
        "user_id": {"default": ""},
        "session_id": {"default": "<dynamic>"},  # timestamp-based
        "run_config": {"default": None},
        "save_tracing_data": {"default": False},
    })

    # 3. Runner.run_async（继承自 ADKRunner，被 MethodType 包装）
    sig = inspect.signature(Runner.run_async)
    all_checks += _check(sig, "Runner.run_async", {
        "user_id": {"required": True, "kind": "KEYWORD_ONLY"},
        "session_id": {"required": True, "kind": "KEYWORD_ONLY"},
        "invocation_id": {"default": None},
        "new_message": {"default": None},
        "run_config": {"default": None},
        "yield_user_message": {"default": False},
    })

    # 4. ADKRunner.__init__ 的 auto_create_session 默认值（关键！）
    sig = inspect.signature(ADKRunner.__init__)
    all_checks += _check(sig, "ADKRunner.__init__", {
        "session_service": {"required": True},
        "auto_create_session": {"default": False},
    })

    # 5. [PRODUCT]SimpleApp.__init__
    sig = inspect.signature([PRODUCT]SimpleApp.__init__)
    all_checks += _check(sig, "[PRODUCT]SimpleApp.__init__", {})
    # 验证 __init__ 无额外必填参数
    has_required = any(
        p.default is inspect.Parameter.empty and p.name != "self"
        for p in sig.parameters.values()
    )
    all_checks.append({
        "check": "[PRODUCT]SimpleApp.__init__ 无必填参数",
        "passed": not has_required,
        "detail": f"parameters={list(sig.parameters.keys())}",
    })

    # 6. [PRODUCT]SimpleApp 关键方法存在
    for method in ["entrypoint", "run", "ping"]:
        all_checks.append({
            "check": f"[PRODUCT]SimpleApp.{method} 存在",
            "passed": hasattr([PRODUCT]SimpleApp, method),
            "detail": f"callable={callable(getattr([PRODUCT]SimpleApp, method, None))}",
        })

    # 7. create_[PRODUCT]_app
    sig = inspect.signature(create_[PRODUCT]_app)
    all_checks += _check(sig, "create_[PRODUCT]_app", {
        "root_agent": {"default": None},
        "enable_feishu": {"default": False},
        "enable_studio_tools": {"default": False},
        "enable_studio_routes": {"default": False},
    })

    # 8. run_[PRODUCT]_app  (app: FastAPI, *, host=None, port=None)
    sig = inspect.signature(run_[PRODUCT]_app)
    all_checks += _check(sig, "run_[PRODUCT]_app", {
        "app": {"required": True, "kind": "POSITIONAL_OR_KEYWORD"},
        "host": {"default": None},
        "port": {"default": None},
    })

    # 9. StreamingMode 枚举成员
    for member in ["NONE", "SSE", "BIDI"]:
        all_checks.append({
            "check": f"StreamingMode.{member} 存在",
            "passed": hasattr(StreamingMode, member),
            "detail": f"value={getattr(StreamingMode, member, None)}",
        })

    # 10. 参数绑定实测：Runner.run 的默认 session_id 是动态生成的（非空）
    sig = inspect.signature(Runner.run)
    sid_default = sig.parameters["session_id"].default
    all_checks.append({
        "check": "Runner.run.session_id 默认值非空（时间戳）",
        "passed": isinstance(sid_default, str) and sid_default.startswith("tmp-session-"),
        "detail": f"default={sid_default!r}",
    })

    passed = sum(1 for c in all_checks if c["passed"])
    failed = sum(1 for c in all_checks if not c["passed"])
    return {
        "suite": "test_signatures",
        "total": len(all_checks),
        "passed": passed,
        "failed": failed,
        "results": all_checks,
    }


if __name__ == "__main__":
    report = run_signature_tests()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["failed"] == 0 else 1)
