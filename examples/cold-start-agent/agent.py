"""veADK Agent 构造。

离线冷启动阶段不调用真实模型：按 veadk Skill §8，显式传入一个**非真实本地占位**
``model_api_key`` 以绕过 ``get_ark_token`` 凭据查找（该 key 绝不可用于真实推理）。
真实模型联调属后续 L3 门禁，不在本离线示例范围。
"""

from __future__ import annotations

from veadk import Agent

# 仅用于离线构造，使 veadk.Agent 不查找云凭据；不是真实密钥。
OFFLINE_PLACEHOLDER_KEY = "placeholder-offline-not-a-real-key"


def build_agent() -> Agent:
    return Agent(
        name="cold_start_agent",
        description="冷启动演示 Agent：离线 Graph 条件路由 + 持久化短期记忆",
        instruction=(
            "你是一个冷启动演示 Agent。本离线阶段由 Google ADK Graph 做条件路由，"
            "不调用真实模型。"
        ),
        model_api_key=OFFLINE_PLACEHOLDER_KEY,
        tools=[],
    )
