#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取 14 个 Skill 中所有 ```python 代码块，用 py_compile 校验语法。
方法：遍历 skills/*/SKILL.md，正则提取 ```python ... ``` 块，逐块 py_compile.compile()。
约束：只做语法校验，不执行代码（不触发 LLM/云资源）。
"""
from __future__ import annotations

import json
import os
import py_compile
import re
import sys
import tempfile
from typing import Any

SKILLS_DIR = os.environ.get(
    "SKILLS_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "skills")),
)

# 提取 ```python ... ``` 块（支持多行）
CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


def extract_python_blocks(skill_dir: str) -> list[dict[str, Any]]:
    md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md_path):
        return []
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = []
    for i, m in enumerate(CODE_BLOCK_RE.finditer(content)):
        code = m.group(1)
        # 计算块在原文件中的起止行号
        start_line = content[: m.start()].count("\n") + 1
        blocks.append({
            "skill": os.path.basename(skill_dir),
            "block_index": i,
            "start_line": start_line,
            "line_count": code.count("\n") + 1,
            "code": code,
        })
    return blocks


def run_code_block_tests() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    skills = sorted(
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
    )
    total_blocks = 0
    passed = 0
    failed = 0
    for skill in skills:
        skill_path = os.path.join(SKILLS_DIR, skill)
        if not os.path.isfile(os.path.join(skill_path, "SKILL.md")):
            continue
        blocks = extract_python_blocks(skill_path)
        for b in blocks:
            total_blocks += 1
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False, encoding="utf-8"
                ) as tf:
                    tf.write(b["code"])
                    tmp_path = tf.name
                py_compile.compile(tmp_path, doraise=True)
                results.append({
                    "skill": b["skill"],
                    "block_index": b["block_index"],
                    "start_line": b["start_line"],
                    "line_count": b["line_count"],
                    "method": "py_compile",
                    "passed": True,
                    "error": None,
                })
                passed += 1
            except py_compile.PyCompileError as e:
                results.append({
                    "skill": b["skill"],
                    "block_index": b["block_index"],
                    "start_line": b["start_line"],
                    "line_count": b["line_count"],
                    "method": "py_compile",
                    "passed": False,
                    "error": str(e).splitlines()[-1] if str(e) else "PyCompileError",
                })
                failed += 1
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    return {
        "suite": "test_code_blocks",
        "skills_scanned": len(skills),
        "total_blocks": total_blocks,
        "passed": passed,
        "failed": failed,
        "results": results,
    }


if __name__ == "__main__":
    report = run_code_block_tests()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["failed"] == 0 else 1)
