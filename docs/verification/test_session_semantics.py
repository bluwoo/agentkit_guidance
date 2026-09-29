#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session 语义源码分析（不触发 LLM）。
方法：
  1. 用 inspect.getsource + ast 解析 google/adk/runners.py 的 _get_or_create_session
  2. 用 ast 解析 [BASE-ADK]/runner.py 的 run 方法，确认它是否显式调用 create_session
  3. 用 inspect.signature 确认 auto_create_session 默认值
  4. 用 ast 确认 [BASE-ADK] Runner.__init__ 是否向 super().__init__ 传了 auto_create_session=True
结论：
  - run() 是否自动建 session
  - run_async() 是否需要预建 session
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import sys
from typing import Any

from google.adk.runners import Runner as _ADKRunner
from [BASE-ADK] import Runner as _[BASE-ADK]Runner
ADK_RUNNER_PY = inspect.getfile(_ADKRunner)
[BASE-ADK]_RUNNER_PY = inspect.getfile(_[BASE-ADK]Runner)


def _parse_file(path: str) -> ast.AST:
    with open(path, "r", encoding="utf-8") as f:
        return ast.parse(f.read())


def _find_method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                    return item
    return None


def _find_class(tree: ast.AST, class_name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


def analyze_adk_get_or_create_session() -> dict[str, Any]:
    """分析 ADK Runner._get_or_create_session：确认只有 auto_create_session=True 才创建。"""
    tree = _parse_file(ADK_RUNNER_PY)
    method = _find_method(tree, "Runner", "_get_or_create_session")
    if method is None:
        return {"found": False, "auto_create_gate": None, "raises_when_false": None}

    # 遍历方法体，找 if self.auto_create_session: 分支和 raise SessionNotFoundError
    has_auto_create_check = False
    raises_session_not_found = False
    calls_create_session = False
    for node in ast.walk(method):
        # if self.auto_create_session:
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Attribute) and isinstance(test.value, ast.Name)
                    and test.value.id == "self" and test.attr == "auto_create_session"):
                has_auto_create_check = True
        # raise SessionNotFoundError(...)
        if isinstance(node, ast.Raise):
            exc = node.exc
            if isinstance(exc, ast.Call):
                func = exc.func
                if isinstance(func, ast.Name) and func.id == "SessionNotFoundError":
                    raises_session_not_found = True
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "SessionNotFoundError":
                    raises_session_not_found = True
            if isinstance(exc, ast.Name) and exc.id == "SessionNotFoundError":
                raises_session_not_found = True
        # self.session_service.create_session(...)
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Attribute) and func.attr == "create_session"):
                calls_create_session = True

    return {
        "found": True,
        "auto_create_gate": has_auto_create_check,
        "raises_when_false": raises_session_not_found,
        "calls_create_session_inside": calls_create_session,
    }


def analyze_[BASE-ADK]_run_creates_session() -> dict[str, Any]:
    """分析 [BASE-ADK] Runner.run()：确认它显式调用 short_term_memory.create_session。"""
    tree = _parse_file([BASE-ADK]_RUNNER_PY)
    method = _find_method(tree, "Runner", "run")
    if method is None:
        return {"found": False, "explicit_create_session": False}

    calls_create_session = False
    for node in ast.walk(method):
        if isinstance(node, ast.Call):
            func = node.func
            # self.short_term_memory.create_session(...)
            if (isinstance(func, ast.Attribute) and func.attr == "create_session"
                    and isinstance(func.value, ast.Attribute)
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == "self"
                    and func.value.attr == "short_term_memory"):
                calls_create_session = True
    return {
        "found": True,
        "explicit_create_session": calls_create_session,
    }


def analyze_[BASE-ADK]_init_passes_auto_create() -> dict[str, Any]:
    """分析 [BASE-ADK] Runner.__init__：确认它没有向 super().__init__ 传 auto_create_session=True。"""
    tree = _parse_file([BASE-ADK]_RUNNER_PY)
    method = _find_method(tree, "Runner", "__init__")
    if method is None:
        return {"found": False, "passes_auto_create_true": None}

    passes_auto_create_true = False
    for node in ast.walk(method):
        if isinstance(node, ast.Call):
            func = node.func
            # super().__init__(...)
            if isinstance(func, ast.Attribute) and func.attr == "__init__":
                for kw in node.keywords:
                    if kw.arg == "auto_create_session":
                        # 检查值是否为 True
                        if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            passes_auto_create_true = True
                        elif isinstance(kw.value, ast.NameConstant) and kw.value.value is True:
                            passes_auto_create_true = True
    return {
        "found": True,
        "passes_auto_create_true": passes_auto_create_true,
    }


def analyze_[BASE-ADK]_run_async_inherited() -> dict[str, Any]:
    """确认 [BASE-ADK] Runner 没有覆盖 run_async 方法体（仅用 MethodType 包装）。"""
    tree = _parse_file([BASE-ADK]_RUNNER_PY)
    cls = _find_class(tree, "Runner")
    if cls is None:
        return {"found": False, "overrides_run_async": None}
    has_run_async = any(
        isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "run_async"
        for item in cls.body
    )
    # 注意：MethodType 赋值在 __init__ 里，不是方法定义
    return {
        "found": True,
        "overrides_run_async_as_def": has_run_async,
    }


def run_session_semantics_tests() -> dict[str, Any]:
    from google.adk.runners import Runner as ADKRunner
    from [BASE-ADK] import Runner as [BASE-ADK]Runner
    import inspect

    # 1. inspect 确认 auto_create_session 默认值
    adk_init_sig = inspect.signature(ADKRunner.__init__)
    auto_create_default = adk_init_sig.parameters["auto_create_session"].default

    # 2. AST 分析
    adk_analysis = analyze_adk_get_or_create_session()
    [BASE-ADK]_run_analysis = analyze_[BASE-ADK]_run_creates_session()
    [BASE-ADK]_init_analysis = analyze_[BASE-ADK]_init_passes_auto_create()
    [BASE-ADK]_run_async_analysis = analyze_[BASE-ADK]_run_async_inherited()

    # 3. 结论推导
    # 分支A: run() 是否自动建 session
    run_auto_creates = (
        [BASE-ADK]_run_analysis["found"]
        and [BASE-ADK]_run_analysis["explicit_create_session"]
    )
    # 分支B: run_async() 是否需要预建 session
    # 条件：auto_create_session 默认 False + [BASE-ADK] 未覆盖为 True + _get_or_create_session 在 False 时 raise
    run_async_requires_presession = (
        auto_create_default is False
        and not [BASE-ADK]_init_analysis["passes_auto_create_true"]
        and adk_analysis["raises_when_false"]
    )

    checks = [
        {
            "check": "ADK Runner.__init__ auto_create_session 默认值 == False",
            "passed": auto_create_default is False,
            "detail": f"实际默认值={auto_create_default!r}",
        },
        {
            "check": "_get_or_create_session 受 auto_create_session 门控",
            "passed": adk_analysis["auto_create_gate"] is True,
            "detail": f"AST 找到 if self.auto_create_session: = {adk_analysis['auto_create_gate']}",
        },
        {
            "check": "_get_or_create_session 在 auto_create=False 时 raise SessionNotFoundError",
            "passed": adk_analysis["raises_when_false"] is True,
            "detail": f"AST 找到 raise SessionNotFoundError = {adk_analysis['raises_when_false']}",
        },
        {
            "check": "[BASE-ADK] Runner.run() 显式调用 short_term_memory.create_session()",
            "passed": [BASE-ADK]_run_analysis["explicit_create_session"] is True,
            "detail": f"AST 找到 create_session 调用 = {[BASE-ADK]_run_analysis['explicit_create_session']}",
        },
        {
            "check": "[BASE-ADK] Runner.__init__ 未向 super() 传 auto_create_session=True",
            "passed": [BASE-ADK]_init_analysis["passes_auto_create_true"] is False,
            "detail": f"AST 检测到传 True = {[BASE-ADK]_init_analysis['passes_auto_create_true']}",
        },
        {
            "check": "[BASE-ADK] Runner 未用 def 覆盖 run_async（仅 MethodType 包装）",
            "passed": [BASE-ADK]_run_async_analysis["overrides_run_async_as_def"] is False,
            "detail": f"AST 检测到 def run_async = {[BASE-ADK]_run_async_analysis['overrides_run_async_as_def']}",
        },
        {
            "check": "结论: runner.run(messages=...) 自动建 session（显式 create_session）",
            "passed": run_auto_creates,
            "detail": "run() 内部 short_term_memory.create_session() 后再调 run_async",
        },
        {
            "check": "结论: runner.run_async(...) 需要预建 session（否则 SessionNotFoundError）",
            "passed": run_async_requires_presession,
            "detail": "auto_create_session=False 默认，未覆盖，_get_or_create_session 会 raise",
        },
    ]

    passed = sum(1 for c in checks if c["passed"])
    failed = sum(1 for c in checks if not c["passed"])
    return {
        "suite": "test_session_semantics",
        "total": len(checks),
        "passed": passed,
        "failed": failed,
        "auto_create_session_default": repr(auto_create_default),
        "conclusion": {
            "run_auto_creates_session": run_auto_creates,
            "run_async_requires_presession": run_async_requires_presession,
            "note": (
                "run() 通过 short_term_memory.create_session() 显式建 session（非 auto_create_session 机制）；"
                "run_async() 继承 ADK 父类，auto_create_session=False，session 不存在时 raise SessionNotFoundError"
            ),
        },
        "results": checks,
    }


if __name__ == "__main__":
    report = run_session_semantics_tests()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["failed"] == 0 else 1)
