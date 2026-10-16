---
name: agentkit-sdk
description: AgentKit Python SDK / CLI——用装饰器式 API（AgentkitSimpleApp + @app.entrypoint + @app.ping + app.run）把 VeADK Agent 包装成可部署服务，并用 agentkit init/config/launch/invoke 完成本地开发到云端部署调用闭环。当需要编写 AgentKit 应用入口代码、配置请求契约（Header user_id/session_id、Body prompt/files）、接入 SSE 流式、或用 CLI 部署调用 Runtime 时使用本 Skill。
---

# AgentKit SDK / CLI Skill

## 1. 概述

AgentKit Python SDK 深度封装 VeADK，提供**装饰器式应用入口**：用 `AgentkitSimpleApp()` 作为应用容器，`@app.entrypoint` 定义 Agent 入口函数，`@app.ping` 提供健康检查，`app.run()` 启动本地服务。配合 `agentkit` CLI（`init / config / launch / invoke`），完成"本地模板生成 → 本地调试 → 云端部署 → 在线调用"的标准闭环。SDK 不修改 VeADK Agent/Runner 行为，是一层薄包装；请求契约统一为 Header 传 `user_id`/`session_id`、Body 传 `prompt`/`files`，响应支持同步字符串与 SSE 事件流。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已注册火山引擎账号并开通 AgentKit 服务
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] Python ≥ 3.10（官方推荐 3.12，quickstart 使用 `3.12.0`）
- [ ] 已有容器镜像仓库（CR）权限（`agentkit launch` 部署需要）
- [ ] 默认使用火山方舟豆包模型，模型 API Key 由平台自动处理；自定义模型需自行配置
- 依赖包（两个**独立 PyPI 包**，需分别安装）：
  ```bash
  uv pip install veadk-python==1.1.13        # 先装 VeADK（离线验证版本）
  uv pip install agentkit-sdk-python==0.8.7  # 再装 AgentKit SDK
  # 【边界】官网快速上手示例曾钉 agentkit-sdk-python==0.6.4（早于本仓实测基线），勿照抄；以本钉版为准
  ```
- 服务域名：Region 为 `cn-beijing`。注意区分两类域名——**控制面 OpenAPI** 用 `agentkit.<region>.volcengineapi.com`；**InvokeTool/AsyncExecCommand** 等工具执行接口用 `agentkit.<region>.volces.com`（见 shard1 服务地址页）。已部署 Runtime 的自身调用域名由 `GetRuntime.Endpoint` 返回。

## 3. 快速上手

### 3.1 控制台操作路径
AgentKit 控制台 → 智能体运行时 → 创建运行时（关联镜像/模型/观测）→ 发布；或 AgentKit Studio → 选择模板 → 一键部署。代码侧则用 `agentkit init` 从模板生成项目。

### 3.2 代码集成（最小可运行示例）
```python
# simple_agent.py —— AgentkitSimpleApp 装饰器式入口
# Runner.run 签名 / SSE 流式(run_async+types.Content+预建session) / inspect 自检脚本
#   → 统一见 ../references/runner-entrypoint.md（本文件是其中「鉴权400」与「短期会话持久化」两条契约的权威实现）。
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp
from veadk.memory.short_term_memory import ShortTermMemory, DatabaseSessionService
from starlette.responses import JSONResponse

app = AgentkitSimpleApp()

# ========== 显式持久化 ShortTermMemory（DatabaseSessionService backend） ==========
# 【关键】auto_save_session=True 不足以证明跨请求持久化——它只控制保存时机，
# 不指定持久化 backend。必须显式构造 ShortTermMemory 并传给 Runner。
#
# veadk 1.1.13: ShortTermMemory 通过 db_url 触发 model_post_init 构造 DatabaseSessionService。
# SQLite 相对路径 URL 格式（3 斜杠）：sqlite+aiosqlite:///./.sessions.db（本地开发默认，无需 root）
# SQLite 绝对路径 URL 格式（4 斜杠）：sqlite+aiosqlite:////data/sessions.db（生产容器内 /data 可写时用）
# PostgreSQL URL 格式：               postgresql+asyncpg://user:pass@host:5432/db
import os
from pathlib import Path

SESSION_DB_URL = os.getenv("SESSION_DB_URL", "").strip()
if not SESSION_DB_URL:
    session_path = Path(os.getenv("SESSION_SQLITE_PATH", "./.sessions.db")).expanduser()
    # 仅创建实际 SQLite 文件的父目录；不要在 import 时无条件创建 /data。
    session_path.parent.mkdir(parents=True, exist_ok=True)
    SESSION_DB_URL = f"sqlite+aiosqlite:///{session_path.resolve()}"

short_term_memory = ShortTermMemory(db_url=SESSION_DB_URL)
# 断言：确认用的是持久化 backend 而非 InMemorySessionService
assert isinstance(short_term_memory.session_service, DatabaseSessionService)

agent = Agent(
    name="Agent",
    description="A helpful assistant",
    instruction="你是一个乐于助人的助手。",
    tools=[],
)
runner = Runner(
    agent=agent,
    app_name="simple_streamable_app",
    short_term_memory=short_term_memory,  # 显式传入持久化 STM
)


@app.entrypoint
async def run(payload: dict, headers: dict):
    # 【关键】缺 user_id / session_id 时拒绝请求（400），不回落 "default"，不生成随机标识。
    # 否则不同用户/请求会聚合到同一会话，造成数据泄漏。
    user_id = headers.get("user_id")
    session_id = headers.get("session_id")
    if not user_id or not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "user_id and session_id headers are required"},
        )
    result = await runner.run(
        messages=payload["prompt"],
        user_id=user_id,
        session_id=session_id,
    )
    return result

# 流式 SSE（run_async + types.Content + 先 create_session）写法见 ../references/runner-entrypoint.md §4，
# 本处不再复制注释块。

@app.ping
def ping() -> str:
    return "pong!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### 3.3 本地开发 → 云端部署标准流程
```bash
# 【需云凭据联调】以下 CLI 流程来自 SDK quickstart 文档，未在本环境实际执行（本阶段未执行云联调，火山引擎凭据可用性尚未核验）。
# 1. 环境
mkdir agentkit-runtime-quickstart && cd $_
uv venv --python 3.12.0 && source .venv/bin/activate
uv add veadk-python==1.1.13
uv add agentkit-sdk-python==0.8.7

# 2. 从模板初始化（生成 simple_agent.py + requirements.txt）
agentkit init

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
agentkit config
agentkit launch
agentkit invoke "讲一个笑话！"
```

### 3.4 配置片段（agentkit.yaml，云端环境变量注入）
```yaml
launch_types:
  cloud:
    runtime_envs:
      VOLCENGINE_ACCESS_KEY: <your_ak>
      VOLCENGINE_SECRET_KEY: <your_sk>
      # 长期记忆 mem0 后端示例
      DATABASE_MEM0_BASE_URL: <your_mem0_url>
      DATABASE_MEM0_API_KEY: <your_mem0_api_key>
```

## 4. 核心概念与 API

| 概念/类/函数 | 说明 | 关键参数 |
|---|---|---|
| `AgentkitSimpleApp()` | SDK 应用容器，提供装饰器与 HTTP 启动能力 | 无必填；薄包装层，不修改 VeADK 行为 |
| `@app.entrypoint` | 装饰 Agent 入口函数 | 函数签名 `(payload: dict, headers: dict)`；可 `return str` 或 `async yield` SSE 事件 |
| `@app.ping` | 装饰健康检查函数，返回 `"pong!"` | 无参数 |
| `app.run(host, port)` | 启动本地服务 | `host: str`（默认 0.0.0.0）、`port: int`（默认 8000） |
| `Runner(agent, app_name)` | VeADK Runner，管理会话与事件流 | `agent`、`app_name` |
| `runner.run(messages=...)` | 【源码核验-签名匹配】简单调用，自动建session，返回str | `messages: str/list/MediaMessage`、`user_id`、`session_id`、`run_config` |
| `runner.run_async(...)` | 流式运行（ADK父类方法，需手动构造Content） | `user_id`、`session_id`、`new_message: types.Content`、`run_config` |
| `StreamingMode.SSE` | SSE 流式开关 | 在 `RunConfig(streaming_mode=StreamingMode.SSE)` 中指定 |
| `agentkit init` | 从模板生成项目 | 生成 `simple_agent.py` + `requirements.txt` |
| `agentkit config / launch / invoke` | 配置 / 部署 / 调用 | `invoke "提示词"` 直接调用已部署 Runtime |

**两种集成路径对比**（同属本 SDK 生态，按需选择）：

| 维度 | `AgentkitSimpleApp` 路径 | `create_agentkit_app` 路径（见 veadk Skill） |
|---|---|---|
| 适用场景 | 简单单 Agent，开发者完全控制入口 | 需 Studio 集成、Web UI、拓扑展示 |
| 路由 | 开发者手动定义 `/invoke` | 工厂自动配置 `/run`、`/run_sse`、`/invoke`、`/web/*` |
| Web UI | 无 | 内置 VeADK Web UI |
| 代码量 | ~50 行 | ~100 行配置 |

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` | 火山引擎 AK/SK | 是（部署/调用） |
| `MODEL_AGENT_NAME` / `MODEL_AGENT_API_KEY` | 方舟模型 ID 与 Key | 自定义模型时必填 |
| `AGENTKIT_TOOL_ID` | 沙箱工具实例 ID（接入 run_code 时） | 用沙箱时必填 |
| `DATABASE_MEM0_BASE_URL` / `DATABASE_MEM0_API_KEY` | mem0 长期记忆连接 | 用 mem0 记忆时必填 |
| `DATABASE_VIKINGMEM_COLLECTION` / `DATABASE_VIKINGMEM_MEMORY_TYPE` | Viking 记忆库 | 用 Viking 记忆时必填 |
| `DATABASE_VIKING_COLLECTION` | Viking 知识库 collection | 用 RAG 知识库时必填 |
| `MCP_ENDPOINT` / `MCP_AUTH_KEY` | 网关 MCP 接入（Header 鉴权 `Authorization: Bearer <MCP_AUTH_KEY>`） | 接 MCP 时必填 |
| `API_KEY` | 方舟 Key（MCP 示例场景） | 视示例而定 |

## 5. 输入输出规范

### 输入（调用 Agent 服务）
- Header: `user_id` (string) — 用户标识
- Header: `session_id` (string) — 会话标识；同 session_id 复用短期会话与沙箱实例
- Body: `prompt` (string) — 文本指令
- Body: `files` (array, optional) — 多模态文件（图片/文件）

### 输出
- 同步模式：字符串响应
- SSE 流式：逐事件 JSON 字符串（`event.model_dump_json(exclude_none=True, by_alias=True)`）
- 健康检查：`/ping` 返回 `"pong!"`
- 错误：标准 HTTP 状态码 + 错误信息

### 会话管理
- 短期会话：`runner.short_term_memory.session_service.get_session` / `create_session`，需在 entrypoint 中手动判断存在性
- 长期记忆：每轮结束调用 `await runner.save_session_to_long_term_memory(session_id=..., user_id=...)`

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit 相关管理权限（CLI 部署走 AK/SK 或 IAM 角色）
- **入站认证**：调用 Runtime 时用 API Key（共享/专属网关）或 SSO（开启快速登录后）；Header 必带 `user_id`/`session_id` 做多租隔离
- **出站凭据**：AK/SK 经环境变量注入容器；MCP 网关用 `MCP_AUTH_KEY` Bearer Token；第三方资源走 IAM 角色/OAuth 托管
- **数据安全**：会话按 `user_id`+`session_id` 隔离；`files` 多模态上传需注意 PII
- **安全围栏兼容**：可与 AgentKit Guardrails 联动（提示词攻击/模型滥用/敏感数据防护），在 Runtime 侧开启

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| `agentkit launch` 失败 | 镜像未构建 / 凭证未配置 / 健康检查不通过 | 检查 AK/SK、CR 镜像权限、容器监听 8000 端口 |
| 本地 `/invoke` 返回 404 | 未启动服务或路径不对 | 确认 `app.run(host="0.0.0.0", port=8000)` 已执行 |
| 流式输出无数据 | 未设 `RunConfig(streaming_mode=StreamingMode.SSE)` 或未 `yield` | 对照 3.2 流式示例，确认 `new_message` 为 `types.Content` 而非纯字符串，并逐个 yield 事件 |
| 多轮对话无上下文 | 未复用 `session_id` / 未创建 session | 检查同一请求传相同 `session_id`，调用 `session_service.create_session` |
| 模型调用 401/403 | 模型 API Key 未配置 | 检查 `MODEL_AGENT_API_KEY` 或平台默认方舟 Key |
| `uv add` 后 import 失败 | 两个包未分别安装 | 确认 `veadk-python` 与 `agentkit-sdk-python` 均已安装 |

排障路径：本地 curl 复现 → Runtime 实例实时日志 → TLS 日志 → 观测 Trace 下钻。

## 8. 可执行验证办法

1. `agentkit init` 后生成 `simple_agent.py`，`python simple_agent.py` 启动无报错
2. 本地调用返回 200 且内容符合预期：
```bash
curl 'http://localhost:8000/invoke' -H 'Content-Type: application/json' \
  -H 'user_id: test' -H 'session_id: local_session' \
  -d '{"prompt": "讲一个笑话！"}'
```
3. 健康检查：`curl http://localhost:8000/ping` 返回 `pong!`
4. 云端：`agentkit launch` 后 `agentkit invoke "讲一个笑话！"` 返回非空响应
5. 多轮验证：同一 `session_id` 连续两问，第二问能记住第一问上下文

## 9. 与其他组件的关系

- **上游依赖**：VeADK（Agent/Runner 定义）、火山方舟模型服务、CR 镜像仓库
- **下游联动**：Runtime（部署载体）、观测（APMPlus/TLS）、沙箱（`AGENTKIT_TOOL_ID` 接入 run_code）、记忆库（mem0/Viking）、知识库（Viking）、MCP 网关
- **常见组合**：
  - SDK + Runtime = 标准在线 Agent 服务
  - SDK + 沙箱 run_code = 代码执行 Agent
  - SDK + LongTermMemory + KnowledgeBase = 记忆化 RAG 助手
  - SDK + MCP Toolset = 工具丰富的企业 Agent

## 10. 已知限制与注意事项

- `agentkit-sdk-python` 与 `veadk-python` 是**两个独立 PyPI 包**，必须分别安装；官方推荐先装 veadk-python
- Python SDK/CLI 不覆盖 VeADK 全部能力，缺失时需直接用 VeADK 多语言 SDK
- `@app.entrypoint` 中开发者需**手动管理会话**（get_session/create_session），SDK 不自动处理
- **`auto_save_session=True` 不足以证明跨请求持久化**：它仅控制是否自动保存 session，不指定持久化 backend。必须显式构造 `ShortTermMemory(db_url=...)` 并传入 `Runner(short_term_memory=...)`，才能确保会话数据持久化到 SQLite/PostgreSQL 而非进程内存。
- **缺 `user_id` / `session_id` header 时应返回 400**：不回落 `"default"`，不生成随机标识。回落 default 会导致不同用户聚合到同一会话；生成随机标识则每请求独立、无多轮上下文。权威参考实现 `reference-agents/full-feature-agent/agent.py` 已按此约定实现。
- SQLite 持久化 URL 必须用 `sqlite+aiosqlite:////绝对路径`（4 斜杠），裸 `sqlite:///` 会被 SQLAlchemy 当作同步驱动导致 `DatabaseSessionService` 创建失败。
- 文档站部分子页（quickstart 目录、skills、observability）链接曾失效，具体 API 以源码与运行时实测为准（待核验）
- `create_agentkit_app` 是另一条集成路径（自动路由+Web UI），不要与 `AgentkitSimpleApp` 混用，详见 veadk Skill
- 版本演进：早期示例日志曾出现 veadk `0.2.13`（2025-10），内部文档示例用过 `veadk-python==1.0.10`；本 Skill 离线验证与示例统一固定为 `veadk-python==1.1.13`（2026-09-18，84/84 通过），最新版本以官方发布记录为准。

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| SDK 总览与装饰器 API | https://docs.volcengine.com/docs/AgentKit/SDKoverview-9?lang=zh | SDK 参考总览 |
| 快速开始与部署流程 | https://docs.volcengine.com/docs/AgentKit/Quickstart?lang=zh | 快速入门 |
| 本地→云部署命令 | https://docs.volcengine.com/docs/AgentKit/Runtime?lang=zh | Runtime 文档 |
| 环境变量约定 | https://docs.volcengine.com/docs/AgentKit/SDKoverview-9?lang=zh | SDK 参考（环境变量表） |
| Runtime quickstart 代码核验 | https://volcengine.github.io/agentkit-sdk-python/content/4.runtime/1.runtime_quickstart.html | Runtime quickstart |
| Memory quickstart 代码核验 | https://volcengine.github.io/agentkit-sdk-python/content/6.memory/1.memory_quickstart.html | Memory quickstart |
| 两种集成路径对比 | https://volcengine.github.io/agentkit-sdk-python/（核验报告 03-agentkit-sdk） | 集成路径对比 |


---

## 措辞与契约修正记录（2026-09-18）

- §3.3 注释「（无云凭据）」改为「（本阶段未执行云联调，火山引擎凭据可用性尚未核验）」。
