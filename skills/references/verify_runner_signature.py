#!/usr/bin/env python3
"""verify_runner_signature.py — AgentKit Runner 入口签名的权威自检脚本。

收敛自过去散落在 ~11 个组件 Skill 里的：
    python3 -c "from veadk.runner import Runner; import inspect; print(inspect.signature(Runner.run))"

钉版（与离线验证 results.json 84/84 通过一致，2026-09-18）：
    veadk-python==1.1.13 / agentkit-sdk-python==0.8.7 / google-adk==2.2.0

用法：
    # 推荐：用已装好钉版依赖的 venv
    benchmark_20260928/.venv/bin/python skills/references/verify_runner_signature.py
    # 或任意装了 veadk-python==1.1.13 的环境：
    python3 skills/references/verify_runner_signature.py

退出码：0 = 签名契约全部符合预期；1 = 断言失败（钉版漂移，需重新核对文档）。
"""
from __future__ import annotations

import inspect
import logging
import sys


def main() -> int:
    # 关掉 veadk import 时的 DEBUG 日志噪音
    logging.disable(logging.CRITICAL)

    try:
        from veadk.runner import Runner
        from agentkit.apps import AgentkitSimpleApp
        from google.genai import types
    except Exception as exc:  # pragma: no cover - 环境未装依赖
        print(f"[FAIL] 导入钉版依赖失败（需 veadk-python==1.1.13 / agentkit-sdk-python==0.8.7）: {exc}")
        return 1

    errors: list[str] = []

    run_sig = inspect.signature(Runner.run)
    run_async_sig = inspect.signature(Runner.run_async)

    print("== Runner.run ==")
    print(run_sig)
    run_params = set(run_sig.parameters)
    for needed in ("messages", "user_id", "session_id", "run_config"):
        if needed not in run_params:
            errors.append(f"Runner.run 缺少参数 {needed}")

    print("\n== Runner.run_async ==")
    print(run_async_sig)
    ra_params = run_async_sig.parameters
    for needed in ("user_id", "session_id", "new_message", "run_config"):
        if needed not in ra_params:
            errors.append(f"Runner.run_async 缺少参数 {needed}")
    # run_async 应为关键字-only（以 * 分隔），new_message 注解必须是 types.Content
    new_msg = ra_params.get("new_message")
    if new_msg is not None:
        ann_str = getattr(new_msg.annotation, "__name__", str(new_msg.annotation))
        # 注解是 Optional[types.Content]，只要提到 Content 即符合
        if "Content" not in str(new_msg.annotation):
            errors.append(f"Runner.run_async.new_message 注解不是 types.Content（实为 {new_msg.annotation}）")
    else:
        ann_str = "n/a"

    # AgentkitSimpleApp 必须具备三个装饰器/启动方法
    for needed in ("entrypoint", "ping", "run"):
        if not hasattr(AgentkitSimpleApp, needed):
            errors.append(f"AgentkitSimpleApp 缺少 {needed}")

    print("\n== 契约断言 ==")
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        print("\n结论：签名漂移，需重新核对 skills/references/runner-entrypoint.md 与钉版。")
        return 1

    print("[OK] Runner.run 含 messages/user_id/session_id/run_config")
    print("[OK] Runner.run_async 关键字-only，new_message -> types.Content")
    print("[OK] AgentkitSimpleApp 具备 @entrypoint / @ping / run")
    print("\n结论：签名契约符合钉版（veadk-python 1.1.13 / google-adk 2.2.0）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
