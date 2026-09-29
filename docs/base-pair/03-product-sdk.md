# [PRODUCT] SDK 核验报告

> 核验时间：2026-09-18
> 文档站：https://volcengine.github.io/[PRODUCT]-sdk-python/
> 核验方法：直接读取文档页面内容，交叉验证代码级声明

---

## 1. Runtime Quickstart 核验

### 1.1 是否同时安装 [BASE-ADK]-python 与 [PRODUCT]-sdk-python

**结论：✅ 已核验**

**来源**：https://volcengine.github.io/[PRODUCT]-sdk-python/content/4.runtime/1.runtime_quickstart.html

文档原文：
```bash
uv pip install [BASE-ADK]-python
uv pip install [PRODUCT]-sdk-python
```

两个包是**独立的 PyPI 包**，需要分别安装。文档明确推荐先装 [BASE-ADK]-python 再装 [PRODUCT]-sdk-python。

### 1.2 [PRODUCT]SimpleApp 如何包装 [BASE-ADK] Agent/Runner

**结论：✅ 已核验**

**来源**：同上文档，代码示例：

```python
from [BASE-ADK] import Agent, Runner
from [PRODUCT].apps import [PRODUCT]SimpleApp
from [BASE-ADK].prompts.agent_default_prompt import DEFAULT_DESCRIPTION, DEFAULT_INSTRUCTION

app = [PRODUCT]SimpleApp()
agent = Agent(
    name=agent_name,
    description=description,
    instruction=system_prompt,
    tools=tools,
)
runner = Runner(agent=agent, app_name=app_name)

@app.entrypoint
async def run(payload: dict, headers: dict):
    prompt = payload["prompt"]
    user_id = headers["user_id"]
    session_id = headers["session_id"]
    # ... session management ...
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        sse_event = event.model_dump_json(exclude_none=True, by_alias=True)
        yield sse_event

@app.ping
def ping() -> str:
    return "pong!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

**包装机制分析**：

| 组件 | 角色 |
|---|---|
| `[PRODUCT]SimpleApp()` | SDK 提供的应用容器，提供 `@app.entrypoint`、`@app.ping` 装饰器和 `app.run()` 方法 |
| `Agent(...)` | [BASE-ADK] Agent（继承 ADK LlmAgent），定义业务逻辑 |
| `Runner(agent=agent, app_name=...)` | [BASE-ADK] Runner（继承 ADK Runner），管理会话和事件流 |
| `@app.entrypoint` | 标记入口函数，接收 `(payload, headers)`，返回 SSE 事件流 |
| `@app.ping` | 健康检查端点 |

**关键观察**：
- `[PRODUCT]SimpleApp` 是**薄包装层**，不修改 [BASE-ADK] Agent 或 Runner 的行为
- 开发者在 entrypoint 函数中**手动管理会话**（`session_service.get_session` / `create_session`）
- 事件通过 `runner.run_async()` 以 SSE 模式流式返回
- 这与 `create_[PRODUCT]_app`（工厂函数自动配置路由）是**两种不同的集成路径**：
  - `[PRODUCT]SimpleApp`：开发者完全控制 entrypoint 逻辑，SDK 只提供 HTTP 容器
  - `create_[PRODUCT]_app`：工厂自动配置 ADK 兼容路由 + Web UI + 内省端点

### 1.3 Runtime 平台特性

文档描述的 Runtime 核心能力：
- **Serverless 架构**：自动扩缩容，零基础设施管理
- **企业级安全隔离**：容器级隔离，与 Identity 和网关鉴权集成
- **框架无关**：深度融合 [BASE-ADK]，兼容主流 Python Agent 框架
- **多协议**：HTTP、MCP、A2A
- **一键部署**：`[PRODUCT] config` + `[PRODUCT] launch`

---

## 2. Memory 指南核验

### 2.1 [BASE-ADK] LongTermMemory 如何连接平台资源

**结论：✅ 已核验**

**来源**：https://volcengine.github.io/[PRODUCT]-sdk-python/content/6.memory/1.memory_quickstart.html

**代码示例**：
```python
from [BASE-ADK] import Agent, Runner
from [BASE-ADK].memory.long_term_memory import LongTermMemory
from [PRODUCT].apps import [PRODUCT]SimpleApp

app = [PRODUCT]SimpleApp()
long_term_memory = LongTermMemory(
    backend=backend,  # "mem0" 或 "viking_mem"
    index=index
)
agent = Agent(
    name="simple_app_agent",
    instruction="You are a helpful assistant.",
    long_term_memory=long_term_memory
)
runner = Runner(agent=agent)

@app.entrypoint
async def run(payload: dict, headers: dict) -> str:
    # ...
    await runner.save_session_to_long_term_memory(session_id=session_id, user_id=user_id)
    return response
```

**平台连接方式**：通过环境变量配置，在 `[PRODUCT].yaml` 中声明：

```yaml
# mem0 后端
launch_types:
  cloud:
    runtime_envs:
      DATABASE_MEM0_BASE_URL: <your mem0 url>
      DATABASE_MEM0_API_KEY: <your mem0 api key>

# VikingDB 后端
launch_types:
  cloud:
    runtime_envs:
      DATABASE_VIKINGMEM_COLLECTION: <your vikingdb collection name>
      DATABASE_VIKINGMEM_MEMORY_TYPE: <your vikingdb memory type>
```

### 2.2 LongTermMemory 源码核验

**文件**：`[BASE-ADK]/memory/long_term_memory.py`
**URL**：https://raw.githubusercontent.com/volcengine/[BASE-ADK]-python/main/[BASE-ADK]/memory/long_term_memory.py

**类定义**：
```python
class LongTermMemory(BaseMemoryService, BaseModel):
    """Manages long-term memory storage and retrieval for applications."""
```

- 继承 Google ADK 的 `BaseMemoryService`，因此与 ADK 的 `memory_service` 接口兼容
- 后端工厂函数 `_get_backend_cls(backend)` 支持：

| 后端 | 类 |
|---|---|
| `"local"` | `InMemoryLTMBackend` |
| `"opensearch"` | `OpensearchLTMBackend` |
| `"viking"` | `VikingDBLTMBackend` |
| `"viking_mem"` | 已废弃，转发到 `"viking"` |
| `"redis"` | `RedisLTMBackend` |
| `"mem0"` | `Mem0LTMBackend` |
| `"openviking"` | `OpenVikingLTMBackend` |
| `"tos_context"` | `TosContextBucketLTMBackend` |

**自动保存策略**：`MemoryAutoSavePolicy` 控制哪些事件被写入长期记忆，支持 `default` / `all` / `custom` 三种预设。

**Agent 集成方式**（来自 `[BASE-ADK]/agent.py`）：
```python
if self.long_term_memory is not None:
    from google.adk.tools import load_memory
    if hasattr(load_memory, "custom_metadata"):
        load_memory.custom_metadata["backend"] = self.long_term_memory.backend
    self.tools.append(load_memory)
```

---

## 3. SDK 其他关键模块发现

### 3.1 文档站点结构

基于已成功访问的页面和站点首页，[PRODUCT] SDK 文档站包含以下主要章节：

| 章节路径 | 内容 | 状态 |
|---|---|---|
| `1.quickstart/` | 快速开始 | 链接失效（目录页），但 `[PRODUCT] init` 命令在 Runtime quickstart 中提及 |
| `4.runtime/` | Runtime 部署 | ✅ 已核验 quickstart |
| `5.skills/` | 技能系统 | 目录链接失效（待核验具体页面） |
| `6.memory/` | 记忆系统 | ✅ 已核验 quickstart |
| `7.observability/` | 可观测性 | 目录链接失效（待核验具体页面） |

### 3.2 从代码和文档中发现的模块

#### Skills 模块
- **[BASE-ADK] 侧**：`Agent(skills=[...])`、`skills_mode`（local/aio_sandbox/skills_sandbox）、`enable_dynamic_load_skills`
- **[PRODUCT] 侧**：Studio 可浏览 account-scoped Skill Spaces，按 region 和 project 分页
- **代码证据**：`[BASE-ADK]/agent.py` 中 `load_skills()` 方法通过 `[PRODUCT]_TOOL_ID` 环境变量查询平台工具类型，决定 sandbox 模式

#### Tools 模块
- 内置工具：web_search、knowledgebase 加载、agent_authorization、video_generate 等
- MCP 工具：[BASE-ADK]  patched MCP session retry（`patch_mcp_session_retry`）
- Studio 动态工具：`StudioExternalToolset` 通过 WebSocket 反向通道接入

#### MCP 模块
- [BASE-ADK] 支持 MCP 工具集（通过 Google ADK 的 MCP 集成）
- [BASE-ADK] 有 `patch_mcp_session_retry` 补丁
- [BASE-AGENT] 有独立的 MCP 客户端（stdio + HTTP + OAuth 2.1）

#### Observability 模块
- **[BASE-ADK] 侧**：`tracers: list[BaseTracer]`，OpenTelemetry 导出器：
  - APMPlus（`ENABLE_APMPLUS=true`）
  - CozeLoop（`ENABLE_COZELOOP=true`）
  - TLS（`ENABLE_TLS=true`）
- **[PRODUCT] 侧**：平台内建监控与日志系统

#### A2A（Agent-to-Agent）
- `create_[PRODUCT]_app` 配置动态 A2A 路由（`/run`、`/run_sse`）
- 支持 `RemoteA2aAgent`、`LoopAgent`、`SequentialAgent`、`ParallelAgent`
- `_spawn_dynamic_a2a_agent` 克隆根 Agent 并动态挂载远程 A2A 工具

#### Tunnel 模块
- `enable_tunnel: bool` — 本地资源服务器（如 MCP server）通过隧道暴露为 Agent 工具
- 云端应用需通过 `[BASE-ADK].tunnel.mount_tunnel` 挂载隧道路由

#### A2UI 模块
- `enable_a2ui: bool` — Agent 驱动的声明式 UI
- 需要 `a2ui-agent-sdk` 依赖

---

## 4. 两种集成路径对比

| 维度 | `[PRODUCT]SimpleApp` 路径 | `create_[PRODUCT]_app` 路径 |
|---|---|---|
| **适用场景** | 简单单 Agent，开发者完全控制入口 | 需要 Studio 集成、Web UI、拓扑展示 |
| **路由配置** | 开发者手动定义 `/invoke` 等端点 | 工厂自动配置 `/run`、`/run_sse`、`/invoke`、`/web/*` |
| **会话管理** | 开发者手动管理 session_service | 工厂通过 `[PRODUCT]AgentServerApp` 自动管理 |
| **Web UI** | 无 | 内置 [BASE-ADK] Web UI（`/`、`/webui`） |
| **内省端点** | 无 | `/web/agent-info/{app_name}`、`/web/agent-graph`、`/web/search` |
| **Studio 工具** | 无 | `enable_studio_tools=True` 可挂载 |
| **飞书 channel** | 无 | `enable_feishu=True` 可启用 |
| **身份绑定** | 无 | `identity=RuntimeIdentity(...)` 可启用 |
| **Harness 扩展** | 无 | `harness_extension=...` 可接入外部 agent sidecar |
| **代码复杂度** | 低（~50 行） | 中（工厂自动处理，~100 行配置） |
