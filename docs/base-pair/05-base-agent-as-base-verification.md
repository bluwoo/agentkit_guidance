# 05 — [BASE-AGENT] Agent 作为 [DELIVERY] 底座的适配路径核验

> 核验日期：2026-09-18（Asia/Shanghai）
> 固定版本/commit：
> - **[BASE-AGENT] Agent**：仓库 `NousResearch/[BASE-AGENT]-agent`，分支 `main`，HEAD commit `e83b1d51f13a08b424636f0b519db86a35aa7bd7`（committer 2026-09-18T01:52:15Z），`pyproject.toml` 标注版本 **0.21.1**。
> - **[BASE-ADK]**：`volcengine/[BASE-ADK]-python` 分支 `main`，文件 `[BASE-ADK]/integrations/[PRODUCT]/app.py`（本次未单独固定其 commit hash，记录为 main 分支读取）。
> - **[PRODUCT] Runtime API**：Version `2025-10-30`，证据来自本地 `docs/volcengine-official/[SHARD-1]-results.md`。
>
> 结论先行：**[BASE-AGENT] 不是 [BASE-ADK] 的 LlmAgent 子类，但这并不阻断它在 [PRODUCT] Runtime 上运行。** Runtime 本质是「托管容器镜像 + 强制其满足层 1 托管要求（监听端口、启动命令、健康检查、鉴权、资源/网络/IAM，见 §3c 三层区分）」的托管服务。**关键修正（2026-09-18 二次核验）**：此前把 `/run`、`/run_sse`、`/invoke`、`/sessions`、`/ping` 一并列为"Runtime 强制契约"证据不足——它们是 [BASE-ADK]/ADK 的**应用层路由**（SDK 最精简的 `[PRODUCT]SimpleApp` 只含 `/invoke`+四个健康探针，并无 `/run`/`/run_sse`/`/sessions`），不等于云 Runtime 对托管容器的普遍强制要求。真正需要补齐的不是「继承 LlmAgent」，而是**让 [BASE-AGENT] 进程满足层 1**（或加一层薄 shim）。下文给出代码证据与两条可行适配方案。

---

## 1. [BASE-AGENT] 原生主循环与入口核验

### 1a. 主入口（console_scripts）

证据：`pyproject.toml` → `[project.scripts]`：

```toml
[project.scripts]
[BASE-AGENT]       = "[BASE-AGENT]_cli.main:main"
[BASE-AGENT]-agent = "run_agent:main"
[BASE-AGENT]-acp   = "acp_adapter.entry:main"
```

- 面向用户的 CLI 入口是 **`[BASE-AGENT]` → `[BASE-AGENT]_cli.main:main`**（基于 Google Fire，`fire==0.7.1` 在依赖里）。注意：本次 `[BASE-AGENT]_cli/main.py` 通过 raw 拉取两次均返回 `link fetch error`（网络层问题，非文件不存在），但其存在性由 `[project.scripts]` 与 `gateway/run.py` docstring 共同确认。
- **`[BASE-AGENT]-agent` → `run_agent:main`** 是直接跑 agent runner 的入口。
- `[BASE-AGENT]-acp` → `acp_adapter.entry:main` 是 ACP（Agent Client Protocol）适配器入口。

> 修正用户假设：仓库里**没有 `apps/gateway/` 目录**。gateway 是顶层 Python 包 `gateway/`（见 `[tool.setuptools.packages.find]` 的 `include = [..., "gateway", "gateway.*", ...]`）。

### 1b. Agent loop 核心文件

证据：`run_agent.py` 文件 docstring（原文）：

```
"""AIAgent: the tool-calling agent runner (conversation loop, tool execution, session lifecycle).

 from run_agent import AIAgent
 agent = AIAgent(base_url="http://localhost:30000/v1", model="claude-opus-4-20250514")
 response = agent.run_conversation("Tell me about the latest Python updates")
"""
```

- 主类 **`run_agent.AIAgent`**，由 16 个 mixin 组合而成（`ClientLifecycleMixin / StreamDeliveryMixin / SessionPersistenceMixin / CompressionFacadeMixin / TurnFacadeMixin / ...`）。
- 单轮驱动函数 **`run_conversation(agent, ...)`** 已抽取到独立文件 **`agent/conversation_loop.py`**。其 docstring（原文）：

```
"""The agent conversation loop — extracted from ``run_agent.AIAgent``.
``run_conversation(agent, ...)`` drives one user turn (model call, tool dispatch,
retries, fallbacks, compression, post-turn hooks)."""
```

- 即：**核心循环 = `run_agent.AIAgent` + `agent/conversation_loop.run_conversation`**，负责「模型调用 → 工具分发 → 重试/降级 → 上下文压缩 → turn 后钩子」。这是一个自包含、不依赖 google-adk 的循环。

### 1c. HTTP API 模式 / gateway 支持的平台

证据：
- 依赖里 `fastapi>=0.104.0,<1` 与 `uvicorn[standard]>=0.31.0,<1` 是**核心依赖**（不是 optional）。`[web]` extra 注释写明：`` `[BASE-AGENT] dashboard` (localhost SPA + API)``。
- **`gateway/run.py`** docstring（原文）：

```
"""Gateway runner - entry point for messaging platform integrations.
Provides ``start_gateway()`` (start all configured adapters) and ``GatewayRunner`` (lifecycle).
Run via ``python -m gateway.run`` or ``python cli.py --gateway``."""
```

- `gateway/run.py` 内部把 surface 分为：`{"local", "api_server", "webhook", "msgraph_webhook"}`（见 `_GATEWAY_RAW_TEXT_PLATFORMS = frozenset({"local", "api_server", "webhook", "msgraph_webhook"})`）——**存在一个名为 `api_server` 的 HTTP 程序化表面**，以及 `webhook`。
- 其余 protocol 表面：`acp_adapter/server.py`（53KB，ACP server）、`agent/acp_openai_bridge.py`（OpenAI 桥）。
- 平台 adapter（telegram/discord/slack/matrix/...）由 `[messaging]/[matrix]/[slack]/[feishu]/[dingtalk]` 等 extra 与 `gateway/platforms/` 提供。

> 结论：[BASE-AGENT] **支持 HTTP API 模式**（dashboard FastAPI、gateway 的 `api_server`/`webhook` surface、ACP server、OpenAI bridge），但这些表面讲的是 [BASE-AGENT]/ACP/OpenAI 语义，**不是**火山 [PRODUCT] Runtime 协议。

### 1d. 是否可作为长期运行服务进程

**可以。** 证据：
- `gateway/run.py` 的 `start_gateway()` + `GatewayRunner` 就是常驻服务进程，内置 `_agent_cache`（`_AGENT_CACHE_MAX_SIZE = 128`，`_AGENT_CACHE_IDLE_TTL_SECS = 3600.0`）、reconnect watcher、compaction 后台任务。
- `cron/` 包（`[project.scripts]` 之外，`croniter` 核心依赖）提供定时任务。
- Dockerfile 存在（26KB），天然容器化。

### 1e. `~/.[BASE-AGENT]/` 配置结构

证据：`[BASE-AGENT]_constants.py`：
- `get_[BASE-AGENT]_home()` → POSIX 下 `Path.home() / ".[BASE-AGENT]"`，Windows 下 `%LOCALAPPDATA%\[BASE-AGENT]`；可用 **`[BASE-AGENT]_HOME` 环境变量**或 context-local override 改写。
- 真实 [BASE-AGENT] home 的标志文件：`_[BASE-AGENT]_HOME_MARKERS = ("config.yaml", ".env", "state.db")`。
- 已确认存在的子项/文件：
  - `config.yaml`（主配置）、`.env`（密钥）、`state.db`（SQLite SessionDB）；
  - `sessions/`（来自 `mcp_serve.py`：`_get_sessions_dir() = _[BASE-AGENT]_home() / "sessions"`，含 `sessions.json`）；
  - `channel_directory.json`（MCP/gateway 读取的渠道目录）；
  - `active_profile`（当前 profile 指针）、`profiles/<name>/`（多 profile）、`.deleted/`（墓碑）；
  - `skills/`、`optional-skills/`、`optional-mcps/`、`node/`（托管 node）、`platforms/`（pairing 等）。

---

## 2. [BASE-AGENT] MCP server 实际暴露范围

文件：`mcp_serve.py`（仓库**根目录**，非子包），docstring（原文）：

```
"""[BASE-AGENT] MCP Server — expose messaging conversations as MCP tools (`[BASE-AGENT] mcp serve`).
A stdio MCP server letting any MCP client (Claude Code, Cursor, Codex, ...) list
conversations, read history, send messages, poll live events, and manage approvals.
Matches OpenClaw's 9-tool channel bridge surface plus the [BASE-AGENT]-specific
channels_list. Client config: {"mcpServers": {"[BASE-AGENT]": {"command": "[BASE-AGENT]", "args": ["mcp", "serve"]}}}
"""
```

### 2a. 是「工具桥」还是「完整 agent loop」？

**是 messaging bridge（工具桥），不是完整 agent loop 的 RPC 入口。** 关键证据：

- 它是 **stdio** MCP server（`run_mcp_server()` → `server.run_stdio_async()`）。
- 它**不自己跑 LLM/工具循环**。`messages_read`、`conversations_list` 等全部通过 `SessionDB`（`state.db`）读取，`_get_session_db()` 来自 `[BASE-AGENT]_state_registry.acquire()`。真正的 agent loop 在 gateway 进程里跑，这个 MCP 进程只是**读同一个 SQLite、外加往平台出站发消息**。
- `messages_send` 的实现（原文）：

```python
from tools.send_message_tool import send_message_tool
return send_message_tool({"action": "send", "target": target, "message": message})
```

  它的语义是「**作为 agent 往 telegram/discord/slack 出站发一条消息**」（target 形如 `telegram:6308981865`），**不是**「给 [BASE-AGENT] agent 注入一条 prompt 并同步拿到 LLM 回复」。

### 2b. 实际暴露的 10 个 MCP tools

`_TOOL_NAMES`（注册顺序 == list_tools 顺序，原文）：

```python
_TOOL_NAMES = (
    "conversations_list", "conversation_get", "messages_read", "attachments_fetch",
    "events_poll", "events_wait", "messages_send", "channels_list",
    "permissions_list_open", "permissions_respond",
)
```

| 工具 | 作用（依其 docstring） |
|---|---|
| `conversations_list` | 列出跨平台活跃会话（需 session_key 供后续读取） |
| `conversation_get` | 取单个会话详情 |
| `messages_read` | 读某会话历史消息（role/content/timestamp） |
| `attachments_fetch` | 取某条消息的非文本附件 |
| `events_poll` | 游标轮询新事件（message/approval_requested/approval_resolved） |
| `events_wait` | 长轮询等下一个事件（≤5min） |
| `messages_send` | 向平台会话出站发消息 |
| `channels_list` | 列出可发送的渠道/目标 |
| `permissions_list_open` | 列出本 bridge 存活期间看到的待审批 |
| `permissions_respond` | 审批 allow-once/allow-always/deny |

### 2c. [BASE-AGENT] 的 MCP 客户端能力（连外部 MCP server）

**具备。** 证据：
- `[mcp] = ["mcp==2.0.0", "httpx2==2.7.0", "starlette==1.3.1"]` extra；pyproject 注释引用 `tools/mcp_tool.py` 与 `tools/mcp_oauth_manager.py`（[BASE-AGENT] 作为 MCP **client** 去连外部 server 并构造 client 对象）。
- 即 [BASE-AGENT] 既可「被 MCP client 当桥连」（`[BASE-AGENT] mcp serve`），也可「自己作为 client 连外部 MCP server」（`tools/mcp_tool.py`）。

> 对适配的含义：不能指望 `[BASE-AGENT] mcp serve` 直接当「[DELIVERY] 的 agent RPC」——它没有「发 prompt→跑 loop→回答案」的同步语义。要驱动 [BASE-AGENT] 思考，必须用 `AIAgent.run_conversation`（进程内）或 gateway 的 HTTP surface。

---

## 3. [PRODUCT] Runtime 对任意框架的适配结论

证据：本地 `docs/volcengine-official/[SHARD-1]-results.md`（API Version `2025-10-30`）。

### 3a. CreateRuntime 的关键参数（原文摘录）

```
- ArtifactType（String，必选：image/public_image）
- ArtifactUrl（String，必选，host/namespace/repo:tag；公共镜像示例 <INTERNAL_HOST>.com/template/financial:v1117_1）
- RoleName（String，必选，绑定 IAM 角色）
- AuthorizerConfiguration.KeyAuth.{ApiKeyLocation=Header, ApiKeyName} 或 CustomJwtAuthorizer.{DiscoveryUrl, AllowedClients}（二选一必填）
- Envs.N.Key / Envs.N.Value
- CpuMilli / MemoryMb / MaxConcurrency / MinInstance / MaxInstance
- NetworkConfiguration.EnablePublicNetwork / EnablePrivateNetwork
```

### 3b. Runtime 是「托管非 [BASE-ADK] 镜像」还是「只能跑 [BASE-ADK]」？

**Runtime API 层不强制镜像必须基于 [BASE-ADK]/create_[PRODUCT]_app**（即非 [BASE-ADK] 镜像也可托管），但容器并非「任意无约束」，必须满足 §3c 的运行时契约。证据：

- 输入只要求 `ArtifactType=image` + `ArtifactUrl=<任意镜像:tag>` + `Envs` + 资源规格 + 鉴权；**没有任何请求参数要求传入 `LlmAgent`/`BaseAgent` 对象，也没有要求镜像必须由 `create_[PRODUCT]_app` 生成**。
- `GetRuntime` 返回字段含 **`Command（启动命令）`**（line 172），说明镜像自带 entrypoint/command，Runtime 把它跑起来并做端口/网关接入。
- 对照 Tool 维度更直白（line 270）：`Command（自定义工具时需，默认 ./run.sh）、Port（自定义工具时需，默认8000）、ImageUrl（自定义工具必填）`；`CreateSession` 要求 `ImageInfo.Command/Image/Port（均必选）`——**自定义镜像 + 自定义 command + 自定义 port** 是一等公民。

### 3c. 契约必须分三层：Runtime 强制 ≠ [BASE-ADK]/SDK 应用路由 ≠ [DELIVERY] 自研 API

> **本节为 2026-09-18 二次核验后的修正**。此前把 `/run`、`/run_sse`、`/sessions`、`/ping`、`harness_extension` 一并列为"Runtime 强制契约"，证据不足：这些端点来自 SDK/[BASE-ADK] 的**应用层实现**，不等于云 Runtime 对托管容器的普遍强制要求。本次直接读 [PRODUCT]-sdk 与 [BASE-ADK]-python 源码后重分三层。

#### 核验方法与关键源码事实（本次新增证据）

直接读取 GitHub 源码（`volcengine/[PRODUCT]-sdk-python` main、`volcengine/[BASE-ADK]-python` main）：

1. **SDK 最精简应用 `[PRODUCT]SimpleApp`（Starlette，非 FastAPI）只注册 5 条路由**——`[PRODUCT]/apps/simple_app/simple_app.py` L40-46：
   ```python
   routes = [
       Route("/ping",      self.ping_handler.handle,        methods=["GET"]),
       Route("/health",    self.ping_handler.health_check, methods=["GET"]),
       Route("/readiness", self.ping_handler.readiness,   methods=["GET"]),
       Route("/liveness",  self.ping_handler.liveness,    methods=["GET"]),
       Route("/invoke",    self.invoke_handler.handle,    methods=["POST"]),
   ]
   ```
   **它没有 `/run`、没有 `/run_sse`、没有 `/sessions`。** `run(host, port=8000)` 默认 `0.0.0.0:8000`（L93-96）。这是"用 SDK 上 Runtime 的最小形态"，反证 `/run` `/run_sse` `/sessions` 不是 Runtime 普遍强制项。
2. **`[PRODUCT]AgentServerApp`（FastAPI，包 ADK `AdkWebServer`）才多出这些路由**——`[PRODUCT]/apps/agent_server_app/agent_server_app.py`：
   - `self.app = self.server.get_fast_api_app(...)`（L354）——`/run`、`/run_sse`、`/sessions` 来自 google.adk 的 `AdkWebServer`，**是 ADK 约定，不是 Runtime 网关强制**。
   - `@self.app.post("/run_sse")`（L386）是它**覆写** ADK 默认路由。
   - `/invoke` 路由上方注释明写：**"Compatibility route for [PRODUCT] CLI invoke"**（L637）——即 CLI 兼容路由。
3. **[BASE-ADK] `create_[PRODUCT]_app` 自己又注册了一批路由**——`[BASE-ADK]/integrations/[PRODUCT]/app.py`，装配顺序 L1056-1072：
   - `_configure_dynamic_a2a_routes`：`POST /run`（L719）、`POST /run_sse`（L772）、`POST /invoke`（L841，从 Header 读 `user_id`/`session_id`，L844-845）。
   - `_add_introspection_routes`：`GET /ping`（L440-442，**固定返回 `{"status":"ok"}`**）、`GET /web/agent-info/{app_name}`、`/web/agent-draft`、`/web/search`、`/web/agent-graph`（Studio/拓扑自省用）。
   - `_configure_harness_extension_lifecycle`：`GET /web/harness-sidecar/status`（L410），**仅当 `harness_extension is not None` 才注册**（L1069-1070）。
   - `_mount_webui`：`/`、`/webui`。
   - 身份模式下把 `identity_health_routes` 设为 `("/ping",)`（L1055），注释："[BASE-ADK]'s fixed /ping route returns only {"status": "ok"}"——**这是 [BASE-ADK] 把 `/ping` 当作"身份豁免健康路由"的设计选择，不是 Runtime 网关探活路径的证据。**

#### 层 1：Runtime 实际托管 / 健康 / 调用最低要求（强制，有 API 证据）

基于 [SHARD-1]（API Version `2025-10-30`）+ SDK 最精简应用反推：

| 强制项 | 证据 | 来源 |
|---|---|---|
| 容器必须监听一个 **HTTP 端口**（默认 8000） | Tool/CreateSession `Port`"自定义工具时需，默认8000"；SDK `SimpleApp.run` 默认 `0.0.0.0:8000`；[BASE-ADK] `run_[PRODUCT]_app` 默认 `HOST=0.0.0.0`/`PORT=8000` | [SHARD-1] L270/L359；simple_app.py L93-96；[BASE-ADK] L1090-1091 |
| 容器必须有**启动命令**（`Command`，默认 `./run.sh`） | `GetRuntime` 返回 `Command`；Tool `Command`"自定义工具时需，默认 ./run.sh" | [SHARD-1] L270 |
| Runtime **会做健康检查**（存在该阶段失败） | 发布错误码含 `function_health_check_failed` | [SHARD-1] L241 |
| **鉴权**：KeyAuth（`ApiKeyLocation=Header` + `ApiKeyName`）或 `CustomJwtAuthorizer`（`DiscoveryUrl`+`AllowedClients`）二选一 | `AuthorizerConfiguration` | [SHARD-1] L124/L171 |
| 资源 / 网络 / IAM / 环境变量 | `CpuMilli/MemoryMb/MaxConcurrency/MinInstance/MaxInstance`、`NetworkConfiguration.EnablePublic/PrivateNetwork`、`RoleName`、`Envs` | [SHARD-1] L124 区 |
| **框架无关**（不强制镜像基于 [BASE-ADK]/ADK/LangGraph） | Runtime 概述"框架/模型无关（适配 [BASE-ADK]/LangGraph/ADK）" | [SHARD-1] L433 |

> **层 1 中标"待 POC"的两点（证据不足，不写"必须实现"）**：
> - **具体探活路径**：[SHARD-1] 只证明"存在健康检查"（`function_health_check_failed`），**未写明 Runtime 网关打容器的是 `/ping`、`/health` 还是别的路径**。SDK 提供 `/ping`+`/health`+`/readiness`+`/liveness` 四个候选，到底哪个被网关用作就绪探针，**待一次真实 CreateRuntime 验证**。
> - **调用端点路径**：SDK 最精简应用用 `POST /invoke` 作为调用入口，但 Runtime 网关把业务请求转发到容器的哪条路径（`/invoke`？`/run`？是否可配），[SHARD-1] 未直接写明，**待 POC**。

#### 层 2：[BASE-ADK] / SDK 应用层可选兼容路由（非 Runtime 强制）

这些路由"用 [BASE-ADK]/SDK 就免费得到"，但**不是"不用就上不了 Runtime"**。最精简 `[PRODUCT]SimpleApp` 根本没有其中大部分，即为反证：

| 路由 | 谁提供 | 性质 | 证据 |
|---|---|---|---|
| `POST /run`（同步） | ADK `AdkWebServer` + [BASE-ADK] dynamic | ADK 约定，SDK 最精简应用无 | agent_server_app.py L354；[BASE-ADK] L719 |
| `POST /run_sse`（SSE 流式） | ADK + AgentServerApp 覆写 + [BASE-ADK] dynamic | ADK/SDK 约定，SDK 最精简应用无 | agent_server_app.py L386；[BASE-ADK] L772 |
| `POST /invoke` | SDK SimpleApp（最小调用端点）；AgentServerApp 标注 "Compatibility route for [PRODUCT] CLI invoke"；[BASE-ADK] dynamic 版 | **SDK 最小调用端点（接近层1），但"CLI 兼容"语义是应用层** | simple_app.py L45；agent_server_app.py L637；[BASE-ADK] L841 |
| `GET /ping` | SDK SimpleApp；[BASE-ADK] `_add_introspection_routes` 固定返回 `{"status":"ok"}` | **[BASE-ADK] 固定自省路由**，兼作身份豁免路由；不证明它是 Runtime 网关探活路径 | simple_app.py L41；[BASE-ADK] L440/L1055 |
| `GET /health` `/readiness` `/liveness` | 仅 SDK SimpleApp | k8s 风格探针，SDK 附赠，非 Runtime 文档要求 | simple_app.py L42-44 |
| `/sessions`（会话 CRUD） | ADK `AdkWebServer` session service 路由 | ADK 会话管理约定，SDK 最精简应用无 | agent_server_app.py L354（经 ADK web server 获得） |
| `/web/agent-info` `/web/agent-draft` `/web/search` `/web/agent-graph` | [BASE-ADK] introspection | Studio/拓扑自省用，业务可选 | [BASE-ADK] L444/L469/L478/L505 |
| `/web/harness-sidecar/status` | [BASE-ADK] harness_extension | **[BASE-ADK] 层 sidecar 机制**，仅当 `harness_extension is not None` 才注册；**[BASE-AGENT] 主路径不使用 create_[PRODUCT]_app，故不需要** | [BASE-ADK] L410/L1069 |
| `/` `/webui` | [BASE-ADK] `_mount_webui` | 内嵌 WebUI，业务可选 | [BASE-ADK] L518/L532 |

#### 层 3：[DELIVERY] 自研业务 API（设计选择，标注待 POC）

[BASE-AGENT] 主路径**不使用** `create_[PRODUCT]_app`，薄 FastAPI shim 按三层分工：

- **必须实现（= 层 1 强制项）**：监听 8000 端口、启动命令、健康检查端点（**具体路径待 POC**，先同时提供 `/ping`+`/health` 以兼容 SDK 习惯）、鉴权透传、一个 `POST /invoke` 调用入口。
- **选择实现（层 2 兼容，为兼容 Studio/CLI 工具链）**：`POST /run`、`POST /run_sse`、`/sessions`——若 [DELIVERY] 要复用 [PRODUCT] CLI / Studio 调试工具再补，否则不补。
- **不需要**：`/web/harness-sidecar/status`（[BASE-ADK] 层 sidecar，[BASE-AGENT] 不用 `create_[PRODUCT]_app`）。
- **[DELIVERY] 业务路由（自研，设计选择）**：Step1-4 引导状态机、评测用例 CRUD、审批队列、草稿持久化等（见 `frontend/03-api-integration.md` §2.1）。

> **结论分级（修正后）**：
> - 「Runtime 只能跑 [BASE-ADK]」→ **不成立**（API 层框架无关）。
> - 「任意容器零改造跑」→ **不成立**：须满足层 1（端口/启动命令/健康检查/鉴权/资源网络 IAM）。
> - 「`/run` `/run_sse` `/sessions` `/ping` 是 Runtime 强制」→ **不成立（本次修正）**：它们是 [BASE-ADK]/ADK 应用层路由，SDK 最精简应用不含；薄 shim 只需满足层 1，层 2 按工具链兼容需要选做。
> - 「[BASE-AGENT] 因不继承 LlmAgent 就不能上 Runtime」→ **不成立**：把 [BASE-AGENT] 进程塞进镜像 + 薄 shim 讲通层 1 即可。

### 3d. [PRODUCT] SDK 的 [PRODUCT]AgentServerApp 用法（从 [BASE-ADK] 实际调用反推）

证据：`[BASE-ADK]/integrations/[PRODUCT]/app.py`：

```python
from [PRODUCT].apps import [PRODUCT]AgentServerApp
...
agent_server_kwargs = {"short_term_memory": short_term_memory}
agent_server_kwargs["agent"] = root_agent          # 或 agent_server_kwargs["app"] = adk_app
if identity is not None:
    agent_server_kwargs["identity"] = identity
    agent_server_kwargs["identity_health_routes"] = ("/ping",)
agent_server = [PRODUCT]AgentServerApp(**agent_server_kwargs)
fastapi_app = cast(FastAPI, agent_server.app)
```

- `[PRODUCT]AgentServerApp` 接受 `agent=<BaseAgent>` 或 `app=<google.adk.apps.App>` + `short_term_memory` + 可选 `identity`/`identity_health_routes`，产出一个 FastAPI app（`agent_server.app`），再由 `run_[PRODUCT]_app()` 用 `agent_server.run(host, port)` 跑起来（默认 `HOST=0.0.0.0`、`PORT=8000`）。
- 关于用户提到的「Annotation」机制：**本次读取路径中未获取到** `Annotation` 相关定义（app.py 内未见），标记为「未获取」，不臆造。

---

## 4. harness_extension 实际接口

证据：`[BASE-ADK]/integrations/[PRODUCT]/app.py` → `_configure_harness_extension_lifecycle`（原文关键段）：

```python
def _configure_harness_extension_lifecycle(app: FastAPI, harness_extension: Any) -> None:
    """Expose a safe status route and close the managed extension on shutdown."""
    status_payload = getattr(harness_extension, "sidecar_status_payload", None)
    close = getattr(harness_extension, "close", None)
    if not callable(status_payload) or not callable(close):
        raise TypeError(
            "harness_extension must provide sidecar_status_payload() and close()"
        )

    @app.get("/web/harness-sidecar/status")
    def harness_sidecar_status() -> dict[str, Any]:
        payload = status_payload()
        if not isinstance(payload, Mapping):
            raise RuntimeError("Harness Sidecar status must be an object")
        return {str(key): value for key, value in payload.items()}

    original_lifespan = app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI):
        async with original_lifespan(fastapi_app):
            try:
                yield
            finally:
                close()
    app.router.lifespan_context = lifespan
```

调用点（`create_[PRODUCT]_app` 内）：

```python
if harness_extension is not None:
    _configure_harness_extension_lifecycle(fastapi_app, harness_extension)
```

### 4a. 契约结论（非常窄）

`harness_extension` **只要求实现两个方法**：

| 方法 | 返回 | 用途 |
|---|---|---|
| `sidecar_status_payload()` | 必须是 `Mapping`（dict 类） | 挂到 `GET /web/harness-sidecar/status`，透传给调用方 |
| `close()` | 任意 | FastAPI lifespan 关闭时调用（资源清理） |

- **它是 sidecar 状态查询 + 生命周期钩子，不是完整的 MCP 路由契约，也不是自进化/调用路由契约。** 除了这两个方法，代码里没有对 `harness_extension` 调任何别的接口。
- 因此：**[BASE-AGENT] 完全可以实现这个最小接口**（`sidecar_status_payload()` 返回 [BASE-AGENT] 的版本/profile/会话数等状态 dict；`close()` 关 gateway/db），把它塞进 `create_[PRODUCT]_app(harness_extension=...)`。前提是 [BASE-AGENT] 能被包进一个 `BaseAgent`/`App`（见第 7 节方案）。

---

## 5. adk.dev/workflows 实际接口清单

### 5a. 页面本体（已读到，Total 1642 字符）

`https://adk.dev/workflows/` 确认四大类 + 实验特性：

- **Graph-based workflows**（ADK 2.0+）：把 AI agent 与确定性节点编成可分支的执行图。
- **Dynamic workflows**（ADK 2.0+）：用完整代码逻辑编排 AI agent 与确定性节点。
- **Collaborative workflows**（ADK 2.0+）：单个 agent 动态协调一组 sub-agent。
- **Template workflows**：继承自 `BaseAgent` 的固定结构（sequence / loop / parallel）。
- **Experimental: Agent Routing**：运行时用 router function 在多个 agent 间选择（fallback / A/B / auto-routing）。

### 5b. 子页面读取状态

`graph-workflows/`、`dynamic-workflows/`、`collaborative-workflows/`、`template-workflows/`、`agent-routing` 等子路径多次尝试（含 `/workflows/graph`、`/workflows/collaborative-workflows/` 等变体）均返回 **`link dead`**（疑似客户端路由/ slug 变更）。**子页面正文标记「未获取」，不臆造其参数表。**

### 5c. 实际可用编排组件（来自 [BASE-ADK] 真实 import，强于文档转述）

证据：`[BASE-ADK]/integrations/[PRODUCT]/app.py` 的 import 段：

```python
from google.adk.agents import LoopAgent, ParallelAgent, RunConfig, SequentialAgent
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.run_config import StreamingMode
from google.adk.apps.app import App
from google.adk.cli.api_server import RunAgentRequest
from google.adk.runners import Runner as AdkRunner
```

- 编排组件：**`SequentialAgent`、`ParallelAgent`、`LoopAgent`、`RemoteA2aAgent`、`Supervisor`**（collaborative 协调器；本次未直接在 app.py 见到其 import，但属 ADK 标准协作编排组件，按页面归类列出）。
- 运行时对象：**`Runner`**（`google.adk.runners.Runner`）、**`RunConfig`**、**`StreamingMode.SSE / StreamingMode.NONE`**、**`App(name, root_agent, plugins)`**、**`RunAgentRequest`**。
- `_agent_type()` 实际识别：`loop / sequential / parallel / a2a / llm`（LLM agent 即 `LlmAgent`，不在编排三件套里就归 `llm`）。
- 动态 A2A：`build_remote_a2a_agent_tools(prompt, registry_config)` + `base_agent.clone(update={})`，按 prompt 动态挂载远程 agent 工具。

> 对适配的含义：这些编排组件都以 `BaseAgent` 为节点类型。[BASE-AGENT] 若要被它们编排，需要包一层「长得像 `BaseAgent` 的 wrapper」（方案 B）；但若 [DELIVERY] 自己用 [BASE-AGENT] loop 做主、仅在边缘调 [BASE-ADK] 工具，则不强制走这些编排。

---

## 6. grill-with-docs 及其子 skill（grilling / domain-modeling）可用性

证据：本地 `/home/user/.agents/skills/grill-with-docs/`、`/home/user/.agents/skills/grilling/`、`/home/user/.agents/skills/domain-modeling/`。

### 6a. grill-with-docs 入口

`SKILL.md`（全文仅 7 行有效内容）：

```
---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

Call the Skill tool twice, for "grilling" and "domain-modeling".
```

`agents/openai.yaml`：

```yaml
interface:
  display_name: "Grill with Docs"
  short_description: "Grill a design and write its docs"
policy:
  allow_implicit_invocation: false
```

### 6b. grilling 子 skill 本体（已读取全文）

`/home/user/.agents/skills/grilling/SKILL.md`（无 `agents/` 外其他文件）：

- **触发方式**：frontmatter `description` 声明 "Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases."——按宿主 Skill 加载机制，由描述触发（model-invocation 默认开启，未设 `disable-model-invocation`）。
- **输入**：用户的计划/决策/想法（自然语言）。
- **输出**：分轮次的 design tree 访谈——每轮把 frontier（前置条件已满足的决策点）全部提出，编号问题 + 推荐答案，等用户回答后重新计算 frontier。
- **核心机制**：
  - 把决策映射为 **design tree**（每个决策分支挂依赖它的决策）。
  - **frontier = 前置条件已 settled 的决策**，一轮问完。
  - 依赖未决问题的决策延后到下一轮。
  - **事实查找是 skill 的职责**：需要环境/文件系统事实时 dispatch sub-agent，不阻塞其余 frontier。
  - frontier 为空 = 共享理解达成，等用户确认后才行动。
- **依赖**：无代码依赖、无 import。纯 prompt/流程型。需要宿主支持"dispatch sub-agent 找事实"的能力（[BASE-AGENT] 的 skill/sub-agent 机制支持）。

### 6c. domain-modeling 子 skill 本体（已读取全文）

`/home/user/.agents/skills/domain-modeling/` 目录含 3 文件：`SKILL.md`、`ADR-FORMAT.md`、`CONTEXT-FORMAT.md`。

- **触发方式**：frontmatter `description` 声明 "Use when discussing codebase terminology, writing or editing a CONTEXT.md, or recording or editing an ADR."
- **输入**：设计讨论中的术语/模糊语言/领域关系陈述。
- **输出**：
  - 实时维护 `CONTEXT.md`（术语表，非实现细节）。
  - 按需创建 `docs/adr/NNNN-slug.md`（架构决策记录）。
  - 支持多 context（`CONTEXT-MAP.md` 指向各 context 的 `CONTEXT.md` 位置）。
- **核心机制**：
  - **对 glossary 质询**：用户用词与 `CONTEXT.md` 冲突时立即指出。
  - **锐化模糊语言**：提出精确术语（"account 指 Customer 还是 User？"）。
  - **具体场景压测**：发明 edge-case 场景逼用户明确概念边界。
  - **与代码交叉验证**：发现陈述与代码矛盾时 surface。
  - **内联更新 CONTEXT.md**：术语一旦确定立即写入，不攒批。
  - **克制地提议 ADR**：三条件全满足才提议（难逆转 / 无 context 令人困惑 / 真实 trade-off）。
- **文件依赖**：引用同目录 `./CONTEXT-FORMAT.md`（术语表格式）和 `./ADR-FORMAT.md`（ADR 格式：单段式，可选 status/options/consequences 段）。
- **依赖**：无代码依赖。纯 prompt/流程型，读写 `CONTEXT.md` / `docs/adr/` 文件。

### 6d. [BASE-AGENT] 如何原样执行

- [BASE-AGENT] 的 skill 机制（`~/.[BASE-AGENT]/skills/`、`get_bundled_skills_dir`，见 §1e）天然支持按目录加载 SKILL.md + 附属 md 文件。把 `grilling/`、`domain-modeling/`、`grill-with-docs/` 三个目录放入 `~/.[BASE-AGENT]/skills/` 即可被 [BASE-AGENT] 原生 skill loader 识别。
- **grill-with-docs 是编排层**：它自身无逻辑，只指示"调用 Skill 工具两次"。在 [BASE-AGENT] 中，这对应 skill 内提示模型先后触发 `grilling`（访谈）和 `domain-modeling`（边谈边写文档）两个子 skill。
- **grilling 的 dispatch sub-agent 找事实**：依赖 [BASE-AGENT] 的 sub-agent/dispatch 能力（[BASE-AGENT] 有 `dispatching-parallel-agents` 等 skill 模式）；若 [BASE-AGENT] 宿主不支持子 agent，可降级为 skill 自身用工具查文件系统，但 frontier 计算不受影响。
- **domain-modeling 的文件读写**：直接读写 `CONTEXT.md` / `docs/adr/`，不依赖运行时特殊接口。
- **不能把其他宿主 Skill 工具指令默认当 [BASE-AGENT] 原生**：`grill-with-docs/SKILL.md` 中的 "Call the Skill tool" 是对宿主 skill dispatcher 的通用指令；在 [BASE-AGENT] 中对应 [BASE-AGENT] 的 skill 触发机制，不是某个名为 `Skill` 的 MCP 工具或 API。集成时须在 [BASE-AGENT] 的 skill loader 层面验证这三个目录能被正确发现和触发。

### 结论

- 这三个 skill **全是纯 prompt/流程型**：自身没有代码、没有 Python 依赖、没有运行时 SDK import。
- `grill-with-docs` 的 `disable-model-invocation: true` + `allow_implicit_invocation: false` → **不能被模型隐式自动触发**，必须显式调用。`grilling` 和 `domain-modeling` 未设该标志，可由描述触发。
- **可在 [BASE-AGENT] 中原样执行**：三个目录放入 `~/.[BASE-AGENT]/skills/` 即可，[BASE-AGENT] skill loader 读 SKILL.md frontmatter + 正文 prompt + 附属 md 文件。grill-with-docs 的"调用 Skill 工具两次"映射为 [BASE-AGENT] 内先后触发两个子 skill。
- [BASE-ADK] 侧集成：因无代码依赖，可当作文档产出流程/提示词直接嵌入 [DELIVERY] Step1，不依赖 [BASE-ADK] 运行时；但 sub-agent dispatch 能力需在 [DELIVERY] harness 层补齐。

---

## 7. [BASE-AGENT] 作为 [DELIVERY] 底座的可行适配方案（≥2 种）

> 共同前提：[PRODUCT] Runtime 要求容器监听端口 + 实现 Runtime HTTP 协议 + 接受 KeyAuth/JWT。[BASE-AGENT] 的 loop（`AIAgent.run_conversation`）本身与该协议无关，需要在它外面加一层 HTTP 适配。

### 方案 A（推荐起步）：[BASE-AGENT] 原生进程 + 薄 FastAPI 协议 shim

- **做法**：镜像里跑 [BASE-AGENT]（`[BASE-AGENT]`/`[BASE-AGENT]-agent`），另写一个小 FastAPI 层满足**层 1**（监听 8000、启动命令、健康检查端点、鉴权透传、`POST /invoke` 调用入口，把 `/invoke` 映射到进程内 `AIAgent.run_conversation(...)`）；层 2 的 `/run`、`/run_sse`、`/sessions` 仅在需要兼容 [PRODUCT] CLI/Studio 时再补；**不需要** `/web/harness-sidecar/status`（那是 [BASE-ADK] `create_[PRODUCT]_app` 的 sidecar，[BASE-AGENT] 主路径不用它）。
- **优点**：
  - 完全保留 [BASE-AGENT] 原生 loop、工具、skills、多平台 gateway、自进化（self-improving skills）——**[BASE-AGENT] 是真正的底座，未被替换**。
  - 不要求 [BASE-AGENT] 继承 `LlmAgent`/`BaseAgent`，绕开「不能直接传 LlmAgent」的问题。
  - Runtime 侧只要 `ArtifactUrl=<自己的镜像>` + `Envs` + KeyAuth 即可，容器须满足层 1（端口/启动命令/健康检查/鉴权），层 2 路由按工具链需要选做。
- **缺点/工作量**：
  - 需要自己实现层 1 细节（鉴权 header、健康检查端点、`/invoke` 入参出参格式），以及按需复刻层 2 的 `/run_sse` SSE 事件格式——这部分语义正是 `[PRODUCT]AgentServerApp`/ADK 约定的，**不是 Runtime 网关强制**。
  - [BASE-AGENT] 的 session 模型（`state.db`）与调用方传入的 `user_id`/`session_id` 需对齐。
- **待验证点**：
  1. Runtime 网关对容器**具体探活路径**与**调用转发路径**（打 `/ping` 还是 `/health`？打 `/invoke` 还是 `/run`？鉴权 header 名 `ApiKeyName` 自定义）——需用一次真实 CreateRuntime + 看 `FailedLogFileUrl`/webshell 验证（**层 1 中标待 POC 的两点**）。
  2. [BASE-AGENT] `api_server` surface（gateway/run.py 里的 `api_server`）对外协议是否已接近可用，可减少 shim 工作量（本次未深读其路由表，标记待验证）。
  3. `run_conversation` 是否支持流式回调直接转 SSE（证据里有 `stream_delta_callback`/`thinking_callback` 等回调钩子，**倾向支持**，待实测）。

### 方案 B：[BASE-AGENT] 包成「类 BaseAgent」wrapper，复用 [BASE-ADK] 的 create_[PRODUCT]_app

- **做法**：写一个 `[BASE-AGENT]BaseAgentAdapter`，实现 `BaseAgent` 的最小接口（`name / description / instruction / run_async(...)` 等），内部持有 `AIAgent`；把它作为 `root_agent` 传给 `create_[PRODUCT]_app(root_agent=..., harness_extension=<[BASE-AGENT]状态对象>)`。这样直接复用 [BASE-ADK] 已经实现好的 Runtime 协议、`/run`/`/run_sse`/`/invoke`、Studio 工具路由、short-term memory。
- **优点**：
  - **零手写 Runtime 协议**——白捡 [BASE-ADK] 的 HTTP/SSE/鉴权/session 全套。
  - 可被 ADK 编排（Sequential/Parallel/Loop/Supervisor）包裹，[DELIVERY] 要做多 agent 编排时顺滑。
  - `harness_extension` 接口第 4 节已证实极窄，[BASE-AGENT] 易满足。
- **缺点/工作量**：
  - 需要把 `AIAgent` 的 turn 语义翻译成 ADK `Runner` 的 event stream（`event.model_dump_json`、content parts、artifact_delta）——这是主要工程量。
  - [BASE-AGENT] 的工具/skills 是否要暴露成 ADK toolset，需决定边界（只跑 [BASE-AGENT] loop，还是把 [BASE-AGENT] 工具也注册给 ADK）。
  - 耦合 [BASE-ADK] 版本（`[PRODUCT]-sdk-python>=0.8.2` 才支持 identity）。
- **待验证点**：
  1. `BaseAgent` 抽象基类的确切抽象方法清单（本次未读 `google.adk.agents.base_agent` 源码，wrapper 需实现哪些方法待补）。
  2. [BASE-ADK] 是否允许「非 google LlmAgent 的自定义 BaseAgent 子类」正常跑通 `Runner.run_async`（从 `_agent_type()` 把未知类型归为 `"llm"` 看，**倾向允许**，待实测）。

### 方案 C（对照，不推荐为主）：[BASE-AGENT] 当 sidecar，主进程仍是 [BASE-ADK]

- 即「[BASE-ADK] 主 + [BASE-AGENT] MCP sidecar」。**不符合原需求约束（[BASE-AGENT]为底座），不采用此方案**，此处仅作对照记录：它把底座让给 [BASE-ADK]，[BASE-AGENT] 退化为工具提供方，违背「[BASE-AGENT] 是 [DELIVERY] 底座」的要求。

---

## 8. 能力分级结论（严格区分）

| 命题 | 结论 | 证据 |
|---|---|---|
| [BASE-AGENT] 不能直接把 `AIAgent` 当作 [BASE-ADK] 的 `LlmAgent` 传入 `create_[PRODUCT]_app(root_agent=...)` | **不能直接传入 LlmAgent** | `create_[PRODUCT]_app` 要求 `root_agent: BaseAgent`（google.adk）；`AIAgent` 是 [BASE-AGENT] 自有类，不继承 `BaseAgent`。需 wrapper（方案 B）。 |
| [BASE-AGENT] 因不继承 LlmAgent 就无法在 [PRODUCT] Runtime 运行 | **不成立 / 可以自定义适配** | Runtime CreateRuntime 不强制镜像基于 [BASE-ADK]（[SHARD-1] line 119-130），但容器须满足**层 1**（端口/启动命令/健康检查/鉴权）；[BASE-AGENT] 可做成容器 + 薄 shim（方案 A）。 |
| Runtime 只能托管 [BASE-ADK]/ADK 应用 | **不成立（API 层框架无关，但容器须满足层 1，非零改造）** | ArtifactUrl 任意镜像；Tool 维度 `ImageUrl/Command/Port` 均为自定义一等公民；真正约束是端口/启动命令/健康检查/鉴权；`/run` `/run_sse` `/sessions` 是 [BASE-ADK]/ADK 应用层路由（SDK 最精简 `[PRODUCT]SimpleApp` 不含），非 Runtime 强制。 |
| `[BASE-AGENT] mcp serve` 能当「发 prompt→跑 loop→回答案」的 agent RPC | **不能（它是 messaging bridge，读 state.db + 出站发消息）** | `mcp_serve.py`：10 个工具全是会话/历史/事件/审批/出站消息；无注入 prompt 跑 loop 的工具。 |
| [BASE-AGENT] 支持作为长期运行服务进程 | **可以** | `gateway/run.py` `start_gateway()`/`GatewayRunner` + agent cache + cron。 |
| [BASE-AGENT] 有 HTTP API 模式 | **有（dashboard/api_server/webhook/ACP/OpenAI bridge），但非 [PRODUCT] 协议** | fastapi+uvicorn 核心依赖；`_GATEWAY_RAW_TEXT_PLATFORMS` 含 `api_server/webhook`。 |
| `harness_extension` 是完整 MCP 路由/自进化契约 | **不是（仅 `sidecar_status_payload()`+`close()`）** | app.py `_configure_harness_extension_lifecycle`。 |
| grill-with-docs 可在 [BASE-AGENT]/[BASE-ADK] 用 | **可以（纯 prompt 流程，无运行时依赖；需显式调用）** | 本地 SKILL.md/openai.yaml。 |
| ADK 子页面（graph/dynamic/collaborative/template/agent-routing）正文 | **未获取**（子链 link dead；组件名以 [BASE-ADK] 真实 import 为准） | adk.dev/workflows/ 已读，子页未拉到。 |
| [PRODUCT] SDK 的 `Annotation` 机制 | **未获取**（本次读取路径未见） | app.py 内无引用。 |

---

## 9. 需用户决策的阻断点（如实报告）

1. **协议复刻 vs wrapper**：方案 A（自写 HTTP shim）与方案 B（包 BaseAgent wrapper 复用 [BASE-ADK] 协议）二选一，工程量与耦合度不同。建议先 A 做最小可用，再按需 B。
2. **Runtime 层 1 细节未实测**：本报告基于 API 文档与 SDK/[BASE-ADK] 源码静态推断「非 [BASE-ADK] 镜像可跑（须满足层 1）」，但 Runtime 网关的**具体探活路径**（`/ping` vs `/health`）、**调用转发路径**（`/invoke` vs `/run`）、鉴权 header 名、SSE 事件格式尚未用一次真实 CreateRuntime 验证。**这是上线前必须跑通的验证点**，不是文档能替代的。
3. **[BASE-AGENT] `api_server` surface 复用度未知**：若 gateway 已有接近可用的 HTTP API，方案 A 的 shim 可大幅简化；本次未深读其路由表，列为待验证。
4. 本次**未发现**「[BASE-AGENT] 与 [PRODUCT] Runtime 存在原生适配层」的代码证据——即没有「[BASE-AGENT] 官方原生讲 [PRODUCT] 协议」的现成物。这是**缺乏原生适配**，需自建适配层（上述 A/B），而非「做不到」。

---

### 附：本次固定证据来源
- [BASE-AGENT] `pyproject.toml` v0.21.1 / commit `e83b1d51...`：console_scripts、依赖、packages。
- [BASE-AGENT] `run_agent.py`：`AIAgent` + `run_conversation` 用法。
- [BASE-AGENT] `agent/conversation_loop.py`：单轮循环职责。
- [BASE-AGENT] `mcp_serve.py`：10 个 MCP 工具清单与 bridge 性质。
- [BASE-AGENT] `gateway/run.py`：`start_gateway()`、`api_server`/`webhook` surface。
- [BASE-AGENT] `[BASE-AGENT]_constants.py`：`~/.[BASE-AGENT]` 结构与 marker 文件。
- [BASE-ADK] `[BASE-ADK]/integrations/[PRODUCT]/app.py`：`create_[PRODUCT]_app` 签名、`harness_extension` 两方法契约、编排组件 import。
- 本地 `docs/volcengine-official/[SHARD-1]-results.md`：CreateRuntime/GetRuntime/Tool/CreateSession 参数（Version 2025-10-30）。
- 本地 `grill-with-docs/SKILL.md` 与 `agents/openai.yaml`。


---

## 措辞与契约修正记录（2026-09-18）

- 结论先行段、§3b 标题与结论、§3c 结论分级由「托管任意 OCI 容器」改为「API 层不强制镜像基于 [BASE-ADK]，但容器须满足运行时契约」。
- §3c 新增「Runtime 托管容器的真实契约清单」8 条。
- §8 分级表两行、§9 阻断点 2、方案 A 优点中「任意容器结论」同步修正。
- 方案 C（对照）「用户已明确否决此方向」改为「不符合原需求约束（[BASE-AGENT]为底座），不采用此方案」。

---

## 三层契约修正记录（2026-09-18，二次核验）

> 触发：§3c 原把 `/run` `/run_sse` `/invoke` `/sessions` `/ping` `harness_extension` 列为"Runtime 强制契约"，证据不支持。本次直接读 [PRODUCT]-sdk 与 [BASE-ADK]-python 源码后重分三层。

1. **§3c 整节重写为三层区分**：
   - **层 1（Runtime 强制，有 API 证据）**：监听端口（默认 8000）、启动命令 `Command`（默认 `./run.sh`）、存在健康检查（错误码 `function_health_check_failed`）、鉴权（KeyAuth Header / CustomJwt 二选一）、资源/网络/IAM/Envs、框架无关。
   - **层 2（[BASE-ADK]/SDK 应用层可选兼容路由，非 Runtime 强制）**：`/run` `/run_sse` `/sessions`（ADK `AdkWebServer`/[BASE-ADK] dynamic）、`/invoke`（SDK 最小调用端点，但 AgentServerApp 注释 "Compatibility route for [PRODUCT] CLI invoke"）、`/ping`（[BASE-ADK] 固定返回 `{"status":"ok"}`，兼作身份豁免路由）、`/health` `/readiness` `/liveness`、`/web/*` 自省路由、`/web/harness-sidecar/status`（[BASE-ADK] harness_extension）。
   - **层 3（[DELIVERY] 自研业务 API，设计选择）**：薄 shim 只须满足层 1；`/run` `/run_sse` `/sessions` 按需补；不需要 `/web/harness-sidecar/status`。
2. **关键反证**：SDK 最精简 `[PRODUCT]SimpleApp`（`[PRODUCT]/apps/simple_app/simple_app.py` L40-46）只注册 `GET /ping` `/health` `/readiness` `/liveness` + `POST /invoke`，**无 `/run` `/run_sse` `/sessions`**——证明后者不是 Runtime 普遍强制项。
3. **降级为"待 POC"**：Runtime 网关**具体探活路径**（`/ping` vs `/health`）与**调用转发路径**（`/invoke` vs `/run`）[SHARD-1] 未写明，不再写"必须实现 `/ping`/`/run`"。
4. **同步**：开头结论段、方案 A 做法/优点/待验证点、§8 分级表两行、§9 阻断点 2 均改为"层 1/层 2/层 3"口径；明确 [BASE-AGENT] 主路径**不需要** `/web/harness-sidecar/status`。
