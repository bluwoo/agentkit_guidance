---
name: veadk
description: VeADK（Volcengine Agent Development Kit）火山引擎智能体开发套件——veadk.Agent 继承 Google ADK LlmAgent、veadk.Runner 管理会话事件流，内置 run_code/web_search/image_generate 等工具与长期记忆/知识库/Skills/追踪能力；create_agentkit_app 工厂一键把 Agent 发布为带 Web UI 的 AgentKit 服务。当需要编写火山引擎 Agent 主体、接入内置工具/记忆/知识库、或用工厂函数生产级部署 Agent 时使用本 Skill。
---

# VeADK 智能体开发套件 Skill

## 1. 概述

VeADK（Volcengine Agent Development Kit）是火山引擎为 Agent 应用提供的开发、部署、观测、评测全流程云原生 SDK，与火山引擎产品体系深度融合。其 `Agent` 类**直接继承 Google ADK 的 `LlmAgent`**（已核验源码 `veadk/agent.py`：`class Agent(LlmAgent)`），因此天然兼容 Google ADK 2.0（2026-06-22 起）；在此基础上通过 Pydantic 扩展了火山引擎特有能力（长期记忆、知识库、Skills、tracers、多运行时后端等）。AgentKit Python SDK 是 VeADK 的轻量装饰器封装；需要完整能力时直接使用 VeADK。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已注册火山引擎账号并开通 AgentKit 服务
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] Python ≥ 3.10（推荐 3.12）
- [ ] 已选择方舟模型（默认豆包模型，平台自动处理模型 Key）
- 依赖包：`veadk-python`（离线验证固定版本 **1.1.13**；内部文档示例曾用 1.0.10，最低可用下限按 `>=1.0.8` 理解）
  ```bash
  uv add veadk-python==1.1.13   # 与离线验证环境一致（2026-09-18，84/84 通过）
  # 长期记忆/知识库用 backend="local" 离线调试时，必须装 extensions extras：
  uv add 'veadk-python[extensions]==1.1.13'   # 裸包装 local 后端会 ImportError
  # 长期记忆 mem0 后端额外依赖：
  uv add mem0ai==0.1.118
  ```
- 环境变量：`VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`

## 3. 快速上手

### 3.1 控制台/入口路径
AgentKit Studio 创建智能体（可视化装配）→ 调试（Tracing/拓扑）→ 部署到 Runtime；或本地 `veadk studio` 启动本地工作台。

### 3.2 代码集成（veadk.Agent + Runner 最小示例）
```python
# 【静态核验通过】veadk.Agent 继承 google.adk.agents.LlmAgent（已核验 veadk/agent.py 源码）
from veadk import Agent, Runner

# Agent 继承 Google ADK LlmAgent，支持 instruction/tools/description 等 ADK 参数
agent = Agent(
    name="code_agent",
    model_name="<model-name>",
    description="A fun coding assistant",
    instruction="你是一个编程助手，使用 run_code 工具执行代码。",
    tools=[],
)
runner = Runner(agent=agent, app_name="my_app")

# 用 AgentKit SDK 包装后启动（见 agentkit-sdk Skill）
# 【离线核验通过 2026-09-18】AgentkitSimpleApp 与 run_code 的 import 均实测 PASS
#   （results.json：import #03 / #19；见 docs/offline-verification-report.md）
from agentkit.apps import AgentkitSimpleApp
from veadk.tools.builtin_tools.run_code import run_code

agent_with_tools = Agent(
    name="code_agent",
    instruction="...使用 run_code 工具...",
    tools=[run_code],
)
```

### 3.3 工厂函数一键部署（create_agentkit_app，全功能路径）
```python
# 【静态核验通过】create_agentkit_app / run_agentkit_app 已核验 veadk/integrations/agentkit/app.py 源码
from veadk import Agent, Runner
from veadk.integrations.agentkit import create_agentkit_app, run_agentkit_app

root_agent = Agent(name="support_agent", instruction="你是技术支持助手。")

app = create_agentkit_app(
    root_agent=root_agent,
    enable_studio_tools=True,   # 挂载 Studio BFF 动态工具
    # enable_feishu=True,       # 需要飞书 channel 时开启
)

if __name__ == "__main__":
    run_agentkit_app(app, host="0.0.0.0", port=8000)
```
工厂自动配置 `/run`、`/run_sse`、`/invoke`、`/ping`、`/web/agent-info/{app_name}`、`/web/agent-graph`、`/web/search` 路由并挂载内置 Web UI。

## 4. 核心概念与 API

### Agent 类（已核验源码 `veadk/agent.py`）
- 继承：`google.adk.agents.LlmAgent`（`from google.adk.agents import LlmAgent`）
- 通过 Pydantic `ConfigDict(arbitrary_types_allowed=True, extra="allow")` 扩展火山能力
- 覆写 `_run_async_impl` 支持多运行时后端；覆写 `_llm_flow` 支持 Supervisor 模式

| 概念/参数 | 说明 |
|---|---|
| `Agent(name=, instruction=, tools=, model_name=)` | LLM Agent 主体，参数与 Google ADK LlmAgent 一致 |
| `Runner(agent=, app_name=)` | 运行器，管理会话与事件流；继承 ADK Runner |
| `tools=[run_code]` | 接入内置工具，见下表 |
| `long_term_memory=LongTermMemory(...)` | 长期记忆，自动挂载 ADK `load_memory` 工具 |
| `knowledgebase=KnowledgeBase(...)` | 知识库，自动挂载 `LoadKnowledgebaseTool` |
| `skills=["..."]` | 技能列表；`skills_mode: "skills_sandbox"\|"aio_sandbox"\|"local"` |
| `runtime: Literal["adk","codex","piagent"]` | 多运行时后端切换 |
| `enable_supervisor=True` | Supervisor 模式（`SupervisorSingleFlow`/`SupervisorAutoFlow`） |
| `tracers=[...]` | 可观测性导出器（APMPlus/CozeLoop/TLS） |

### 内置工具清单
| 工具 | import 路径 | 用途 | 核验状态 |
|---|---|---|---|
| `run_code` | `veadk.tools.builtin_tools.run_code` | 沙箱代码执行（Python/JS 等） | ✅ 离线 import PASS（2026-09-18，results.json #19） |
| `web_search` | `veadk.tools.builtin_tools`（子模块待核验） | 联网搜索 | ⚠️ 仅确认存在，精确 import 子模块/签名待核验 |
| `image_generate` | VeADK 内置（精确 import 待核验） | 文生图 | ⚠️ 待核验 |
| `image_edit` | VeADK 内置（精确 import 待核验） | 图像编辑 | ⚠️ 待核验 |
| `video_generate` | VeADK 内置（精确 import 待核验） | 视频生成 | ⚠️ 待核验 |

### create_agentkit_app 工厂函数（9 个参数，已核验源码 `veadk/integrations/agentkit/app.py`）

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `root_agent` | `BaseAgent \| None` | `None` | 根 ADK Agent，与 `app` 互斥 |
| `display_names` | `Mapping[str,str] \| None` | `None` | 技术名→用户友好名映射 |
| `app` | `App \| None` | `None` | 可选 ADK App，保留其 plugins |
| `agent_draft` | `Mapping \| None` | `None` | 只读编辑元数据 |
| `enable_feishu` | `bool` | `False` | 是否启动飞书 channel |
| `enable_studio_tools` | `bool` | `False` | 是否挂载 Studio BFF 动态工具 |
| `enable_studio_routes` | `bool` | `False` | 是否挂载 Studio BFF 动态 HTTP 路由 |
| `identity` | `RuntimeIdentity \| None` | `None` | AgentKit Runtime 身份边界 |
| `harness_extension` | `Any \| None` | `None` | 托管 Harness Extension（外部 agent sidecar），需提供 `sidecar_status_payload()` 与 `close()` |

配套函数：`run_agentkit_app(app, host=None, port=None)` 运行工厂产物。

### Agent 核心能力清单（源码核验）
多模型 fallback（`model_fallbacks`）、`update_model()` 热切换模型、短期/长期记忆、Skills 与动态技能加载、技能检查清单、tracers、授权检查（`enable_authz`）、自动会话保存（`auto_save_session`）、多运行时、A2UI、Tunnel（本地 MCP 隧道）、飞书 channel、数据集生成、Supervisor 模式、Run Processor。

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` | 火山引擎 AK/SK | 是 |
| `MODEL_AGENT_NAME` / `MODEL_AGENT_API_KEY` | 方舟模型 ID 与 Key | 自定义模型时必填 |
| `AGENTKIT_TOOL_ID` | 沙箱工具实例 ID（Skills 加载与 run_code） | 用沙箱/Skills 时必填 |
| `ENABLE_APMPLUS` / `ENABLE_COZELOOP` / `ENABLE_TLS` | 观测导出器开关 | 观测时按需 |
| `veadk.config.getenv` | SDK 统一读环境变量入口 | 推荐用法 |

## 5. 输入输出规范

### 输入
- 经 AgentKit SDK 包装：Header `user_id`/`session_id`，Body `prompt`/`files`
- 工厂路由：`/run`、`/run_sse`（SSE）、`/invoke`
- Runner 调用有两种方式：
  - **【源码核验-签名匹配】简单调用**：`await runner.run(messages="...", user_id="...", session_id="...")` → 返回 `str`（自动建session，自动转Content，内部聚合）
  - **流式运行（ADK父类）**：`runner.run_async(user_id=, session_id=, new_message=types.Content(...), run_config=RunConfig(...))` → async generator of Event（需手动构造Content，需预建session）。完整可运行骨架与 SSE 示例见 [`../references/runner-entrypoint.md`](../references/runner-entrypoint.md)。

### 输出
- 同步：字符串响应
- 流式：SSE 事件（`event.model_dump_json(exclude_none=True, by_alias=True)`）
- 长期记忆落库：`await runner.save_session_to_long_term_memory(session_id=, user_id=)`

## 6. 权限与安全

- **所需 IAM 权限**：火山引擎访问密钥（AK/SK）；Runtime 侧用 IAM 角色替代硬编码密钥
- **入站认证**：经 AgentKit 网关的 API Key / SSO；工厂路由默认服务于 Runtime 内网或公网网关
- **出站凭据**：AK/SK 环境变量；第三方 OAuth 令牌托管；MCP 隧道（`enable_tunnel`）把本地 MCP 暴露给云上 Agent
- **数据安全**：会话按 user/session 隔离；长期记忆后端可选 mem0/VikingDB/Redis/OpenSearch 等 8 种
- **授权检查**：`enable_authz=True` 通过 before_agent_callback 注入授权校验

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| `class Agent` 无法当作 LlmAgent 用 | 把非 ADK Agent 传给 veadk | veadk.Agent 必须继承 ADK LlmAgent，独立框架（如 Hermes）不能直接替换 |
| `create_agentkit_app` 报 TypeError | `harness_extension` 缺方法 | 扩展对象必须实现 `sidecar_status_payload()` 与 `close()` |
| 长期记忆不生效 | 未调 save_session / 后端未配 | 每轮后 `await runner.save_session_to_long_term_memory(...)`，检查 `DATABASE_MEM0_*` |
| mem0 安装冲突 | 版本不符 | 固定 `mem0ai==0.1.118` |
| Skills 不加载 | `AGENTKIT_TOOL_ID` 未设 / skills_mode 错 | 确认环境变量，按平台工具类型选 `skills_sandbox`/`aio_sandbox`/`local` |
| 飞书 channel 无反应 | `enable_feishu` 未开 | `create_agentkit_app(..., enable_feishu=True)` |

排障路径：veadk 日志 → tracers（APMPlus/TLS）→ 内省路由 `/web/agent-graph` 查看拓扑。

## 8. 可执行验证办法

1. 本地导入成功：
```bash
# 【需云凭据联调】需先安装 veadk-python，本精修环境未安装（Python 3.14，未实测）；
#   下列签名已于 2026-09-18 在 venv（Python 3.13.7 + veadk 1.1.13）实测 PASS（results.json）。
uv add veadk-python==1.1.13
python3 -c "from veadk import Agent, Runner; print(Agent.__mro__[:3])"
# 应见 (<class 'veadk.agent.Agent'>, <class 'google.adk.agents.llm_agent.LlmAgent'>, ...)
# Runner.run / run_async 签名自检（替代过去逐文件复制的 inspect.signature 一行）：
python3 skills/references/verify_runner_signature.py
# 实测签名见 ../references/runner-entrypoint.md §3：run(self, messages, user_id='',
#   session_id='tmp-session-<时间戳>', run_config=None, ...) -> str；messages 必填。
```

> **离线构造探针注意（2026-09-28 钉版 venv 无 AK/SK 实测）**：裸 `Agent(name=, instruction=)` 会触发 `get_ark_token` 凭据查找，无凭据时抛 `FileNotFoundError: ... VeFaaS IAM file (/var/run/secrets/iam/credential) not exists`。只做离线构造/import 探针时，可显式传一个**非真实本地占位** `model_api_key`（如 `Agent(..., model_api_key="placeholder")`）绕过凭据查找；但该占位 key **不得用于真实模型调用**，生产/真实推理仍须配置正规 AK/SK 或 `MODEL_AGENT_API_KEY`。

2. `create_agentkit_app` 启动后访问 `/ping` 返回正常，`/web/agent-graph` 返回 Agent 拓扑
3. 调用 `/invoke` 发送测试 prompt，Agent 按 instruction 回答
4. 接入 `run_code` 后让 Agent 执行 `print(1+1)`，确认沙箱返回 `2`
5. 接长期记忆后同 session 两轮对话，第二轮能回忆第一轮事实

## 9. 与其他组件的关系

- **上游依赖**：火山方舟模型、Google ADK 2.0 底座、AgentKit Runtime（部署载体）
- **下游联动**：沙箱（run_code/skills）、记忆库（mem0/VikingDB）、知识库（Viking）、MCP 网关、A2A Registry、观测（APMPlus/TLS）
- **常见组合**：
  - veadk.Agent + AgentkitSimpleApp = 标准部署入口
  - veadk.Agent + create_agentkit_app = Studio 全功能集成
  - veadk.Agent + Supervisor + 多子 Agent = 多 Agent 协作（见 adk-workflow Skill）

## 10. 已知限制与注意事项

- 固定版本为 `veadk-python==1.1.13`（离线验证环境，2026-09-18，84/84 通过）；内部文档示例曾用 1.0.10，最低可用下限约 `>=1.0.8`。兼容 Google ADK 2.0 自 2026-06-22 起。
- veadk-python 是**开源仓库**（github.com/volcengine/veadk-python），但 README 中 "Hermes AgentKit Sessions" 等描述属 Studio 平台侧功能，Runtime 侧无 Hermes 专属代码，仅有通用 `harness_extension` 接口
- Python SDK/CLI 不覆盖 veadk 全部能力，缺失操作直接用 veadk 多语言 SDK
- 长期记忆后端 `viking_mem` 已废弃，转发到 `viking`；新建项目直接用 `viking`/`mem0`
- 内置工具 `web_search`/`image_generate` 等的精确签名以源码 `veadk/tools/builtin_tools/` 为准（部分参数待核验）

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| VeADK 概述与兼容 Google ADK 2.0 | https://docs.volcengine.com/docs/AgentKit/VeADKoverview?lang=zh | 概述 |
| 发布记录（多 Runtime/飞书/A2UI 等） | https://docs.volcengine.com/docs/AgentKit/VeADKreleasenotes?lang=zh | 发布记录 |
| Agent 继承 LlmAgent 源码核验 | https://raw.githubusercontent.com/volcengine/veadk-python/main/veadk/agent.py | veadk/agent.py |
| create_agentkit_app 9 参数源码核验 | https://raw.githubusercontent.com/volcengine/veadk-python/main/veadk/integrations/agentkit/app.py | integrations/agentkit/app.py |
| 内置能力与 Agent 参数清单 | https://github.com/volcengine/veadk-python（核验报告 02-veadk-verification） | Agent 核心能力清单 |
| Hermes 无 Runtime 侧实现 | https://github.com/volcengine/veadk-python（README） | harness_extension 机制 |
| 长期记忆后端工厂 | https://raw.githubusercontent.com/volcengine/veadk-python/main/veadk/memory/long_term_memory.py | long_term_memory.py |
| import 路径与 Runner.run 签名离线核验 | 本地 `docs/offline-verification-report.md`、`docs/verification/results.json`（2026-09-18，Python 3.13.7 + veadk 1.1.13，84/84 通过） | 离线验证报告 |
