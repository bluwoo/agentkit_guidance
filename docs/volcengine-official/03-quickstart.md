# 03 快速入门与开发部署

> 来源：入口用户指南"快速入门"与"进阶入门"章节

## 1 分钟快速部署智能体

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Gettingstarted1-minuteagentrapiddeployment?lang=zh
- 路径：开通 [PRODUCT] → 进入 [PRODUCT] Studio → 选择模板（如 Basic Agent）→ 自然语言/配置搭建 → 一键部署到 Runtime → 通过 `[PRODUCT] invoke` 或控制台测试调用。
- 目标：用最小步骤跑通"创建→部署→调用"闭环。

## 三种开发部署方式

来源：开发并部署 Agent 概览（未逐页读）+ SDK 参考
1. **[PRODUCT] Studio**：可视化/自然语言搭建，支持「快速模式」（自动内置 CreateAgentToolset 动态子 Agent 委派）与「智能模式」；可从 LangChain/LangGraph/Dify 存量项目迁移（2026-08-21）。
2. **[PRODUCT] CLI**：工程化命令行，`[PRODUCT] init / config / launch / invoke`；支持与 TRAE 配合自然语言驱动开发。
3. **[BASE-ADK]**：多语言 ADK，覆盖 Python SDK 不支持的操作。

## 本地开发 → 云端部署标准流程（SDK Runtime 文档）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Runtime?lang=zh
前提：开通 [PRODUCT] + 镜像仓库；获取 AK/SK；Python ≥ 3.10（推荐 3.12）。

```bash
# 1. 环境
mkdir [PRODUCT]-runtime-quickstart && cd $_
uv venv --python 3.12.0 && source .venv/bin/activate
uv add [BASE-ADK]-python
uv add [PRODUCT]-sdk-python

# 2. 从模板初始化（生成 simple_agent.py + requirements.txt）
[PRODUCT] init

# 3. 配置凭证
export VOLCENGINE_ACCESS_KEY=your_ak
export VOLCENGINE_SECRET_KEY=your_sk

# 4. 本地启动（监听 0.0.0.0:8000）
python simple_agent.py

# 5. 本地调用
curl 'http://localhost:8000/invoke' -H 'Content-Type: application/json' \
  -H 'user_id: test' -H 'session_id: local_session' \
  -d '{"prompt": "讲一个笑话！"}'

# 6. 云端部署与调用
[PRODUCT] config
[PRODUCT] launch
[PRODUCT] invoke "讲一个笑话！"
```

**核心代码骨架（[PRODUCT]SimpleApp + [BASE-ADK] Runner + SSE 流式）**：
```python
from [BASE-ADK] import Agent, Runner
from [PRODUCT].apps import [PRODUCT]SimpleApp
app = [PRODUCT]SimpleApp()
agent = Agent(name="Agent", description=..., instruction=..., tools=[])
runner = Runner(agent=agent, app_name="simple_streamable_app")

@app.entrypoint
async def run(payload: dict, headers: dict):
    prompt = payload["prompt"]
    user_id = headers["user_id"]
    session_id = headers["session_id"]
    # 会话存在性判断 + SSE 流式 yield
    async for event in runner.run_async(...):
        yield event.model_dump_json(exclude_none=True, by_alias=True)

@app.ping
def ping() -> str:
    return "pong!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```
- 默认使用火山方舟豆包模型，自动处理模型 API Key。
- 内置短期会话管理保证多轮连续；SSE（`StreamingMode.SSE`）流式输出。

## 存量 Agent 迁移

来源：存量 Agent 迁移概述/原理/操作指南（未逐页读，仅目录确认存在）
- 支持从高代码框架（[BASE-ADK]/Google ADK/LangGraph/LangChain）与低代码框架（Dify 等）迁移。
- 通过 Studio「从存量项目迁移」或 Harness Sidecar（不改 Agent 主体代码即可提升稳定性/任务成功率）。
- 迁移 FAQ 单独成文。
