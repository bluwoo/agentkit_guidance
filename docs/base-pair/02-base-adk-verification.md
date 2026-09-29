# [BASE-ADK] 实现核验报告

> 核验时间：2026-09-18
> 仓库：https://github.com/volcengine/[BASE-ADK]-python
> 核验方法：直接读取 GitHub raw 源文件，不依赖 README 声明

---

## 声明 a：[BASE-ADK] Agent 是否继承 Google ADK LlmAgent

### 结论：✅ 已核验

### 证据

**文件**：`[BASE-ADK]/agent.py`
**URL**：https://raw.githubusercontent.com/volcengine/[BASE-ADK]-python/main/[BASE-ADK]/agent.py

**导入语句**（文件头部）：
```python
from google.adk.agents import LlmAgent
from google.adk.agents.base_agent import BaseAgent
```

**类定义**：
```python
class Agent(LlmAgent):
    """LLM-based Agent with Volcengine capabilities.
    This class represents an intelligent agent powered by LLMs (Large Language Models),
    integrated with Volcengine's AI framework. It supports memory modules, sub-agents,
    tracers, knowledge bases, and other advanced features for A2A (Agent-to-Agent)
    or user-facing scenarios.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")
```

**验证要点**：
- [BASE-ADK] `Agent` 类直接继承 `google.adk.agents.LlmAgent`
- 它通过 Pydantic 模型扩展添加了火山引擎特有能力（long_term_memory、knowledgebase、skills、tracers 等）
- 它覆写了 `_run_async_impl` 以支持多运行时后端（`runtime: Literal["adk", "codex", "piagent"]`）
- 它覆写了 `_llm_flow` 属性以支持 Supervisor 模式

---

## 声明 b：create_[PRODUCT]_app 工厂函数的实际实现和参数

### 结论：✅ 已核验

### 证据

**文件**：`[BASE-ADK]/integrations/[PRODUCT]/app.py`
**URL**：https://raw.githubusercontent.com/volcengine/[BASE-ADK]-python/main/[BASE-ADK]/integrations/[PRODUCT]/app.py

**导出路径**：`[BASE-ADK]/integrations/[PRODUCT]/__init__.py`
```python
"""Public helpers for serving [BASE-ADK] agents on [PRODUCT]."""
from [BASE-ADK].integrations.[PRODUCT].app import (
    create_[PRODUCT]_app,
    run_[PRODUCT]_app,
)
__all__ = ["create_[PRODUCT]_app", "run_[PRODUCT]_app"]
```

**函数签名**：
```python
def create_[PRODUCT]_app(
    root_agent: BaseAgent | None = None,
    display_names: Mapping[str, str] | None = None,
    *,
    app: App | None = None,
    agent_draft: Mapping[str, Any] | None = None,
    enable_feishu: bool = False,
    enable_studio_tools: bool = False,
    enable_studio_routes: bool = False,
    identity: RuntimeIdentity | None = None,
    harness_extension: Any | None = None,
) -> FastAPI:
```

**参数说明**（来自代码 docstring）：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `root_agent` | `BaseAgent \| None` | `None` | 根 ADK Agent，与 `app` 互斥 |
| `display_names` | `Mapping[str, str] \| None` | `None` | 技术名→用户友好名映射 |
| `app` | `App \| None` | `None` | 可选 ADK App，保留其 plugins |
| `agent_draft` | `Mapping \| None` | `None` | 只读编辑元数据 |
| `enable_feishu` | `bool` | `False` | 是否启动飞书 channel |
| `enable_studio_tools` | `bool` | `False` | 是否挂载 Studio BFF 动态工具 |
| `enable_studio_routes` | `bool` | `False` | 是否挂载 Studio BFF 动态 HTTP 路由 |
| `identity` | `RuntimeIdentity \| None` | `None` | [PRODUCT] Runtime 身份边界 |
| `harness_extension` | `Any \| None` | `None` | 托管的 Harness Extension（外部 agent sidecar） |

**内部实现要点**：
1. 创建 `[PRODUCT]AgentServerApp`（来自 `[PRODUCT].apps`，即 [PRODUCT] SDK），传入 `agent` 或 `app`
2. 获取其 FastAPI 实例：`fastapi_app = cast(FastAPI, agent_server.app)`
3. 配置动态 A2A 路由（`/run`、`/run_sse`、`/invoke`）
4. 配置 Studio 工具路由（如果 `enable_studio_tools=True`）
5. 配置飞书 channel 生命周期（如果 `enable_feishu=True`）
6. 配置 Harness Extension 状态路由和关闭逻辑（如果 `harness_extension` 不为 None）
7. 添加内省路由（`/ping`、`/web/agent-info/{app_name}`、`/web/agent-graph`、`/web/search`）
8. 挂载内置 Web UI
9. 挂载 Studio 路由主机

**配套函数**：
```python
def run_[PRODUCT]_app(
    app: FastAPI,
    *,
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Run an app returned by create_[PRODUCT]_app."""
```

---

## 声明 c：README 中 "[BASE-AGENT] [PRODUCT] Sessions" 是否有对应代码实现

### 结论：⚠️ 与 README 部分不符 — README 描述的是 Studio 平台侧功能，[BASE-ADK] 代码中无 [BASE-AGENT] 专属实现

### README 原文

来自 https://github.com/volcengine/[BASE-ADK]-python （GitHub 仓库首页 README）：

> "Studio also manages user-owned Codex, OpenClaw, and **[BASE-AGENT] [PRODUCT] Sessions**. Users can create, reopen, inspect, and explicitly delete each Agent; leaving a Codex conversation only disconnects it, while OpenClaw and [BASE-AGENT] expose their main interface and Terminal through Studio."

### 代码核验

#### 1. GitHub 代码搜索

搜索 `repo:volcengine/[BASE-ADK]-python [BASE-AGENT]`（code search）→ **零结果**。

[BASE-ADK]-python 仓库中没有任何文件包含 "[BASE-AGENT]" 字符串。

#### 2. `harness_extension` 机制

`create_[PRODUCT]_app` 的 `harness_extension` 参数是**唯一可能与外部 agent session 管理相关的代码点**：

```python
def _configure_harness_extension_lifecycle(
    app: FastAPI,
    harness_extension: Any,
) -> None:
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
        return {str(key): value for key, value in payload.items()}
```

**分析**：
- 这是一个**通用的 sidecar 扩展接口**，要求扩展对象提供 `sidecar_status_payload()` 和 `close()` 方法
- 代码中**没有任何 [BASE-AGENT] 专属逻辑**
- 这是 Runtime 侧（[BASE-ADK]）的契约，实际的 [BASE-AGENT] session 管理在 **Studio BFF / 平台侧** 实现

#### 3. Studio Channel 模块

`[BASE-ADK]/integrations/[PRODUCT]/studio_channel/` 目录包含：
- `protocol.py` — 工具清单协议（`StudioToolManifest`、`CatalogSnapshot`）
- `routes.py` — WebSocket 反向通道路由
- `tool.py` — `StudioExternalToolset`、`StudioRemoteTool`

这些是 **Studio 动态工具通道**，与 [BASE-AGENT] session 管理无关。

### 判定

| README 声明 | 代码核验结果 |
|---|---|
| "Studio manages [BASE-AGENT] [PRODUCT] Sessions" | **Runtime 侧无 [BASE-AGENT] 专属代码**。[BASE-ADK] 仅提供 `harness_extension` 通用 sidecar 接口和 `/web/harness-sidecar/status` 状态路由。[BASE-AGENT] session 的创建/管理/删除在 Studio BFF 平台侧实现，不在 [BASE-ADK]-python 开源仓库中。 |
| "OpenClaw and [BASE-AGENT] expose their main interface and Terminal through Studio" | **Runtime 侧无对应代码**。这是 Studio 前端 + 平台 BFF 的功能描述。 |
| "create, reopen, inspect, and explicitly delete each Agent" | **Runtime 侧无对应代码**。Runtime 只暴露 `/web/agent-info/{app_name}` 等内省端点，不管理外部 agent 生命周期。 |

**结论**：README 描述的 "[BASE-AGENT] [PRODUCT] Sessions" 是 **[PRODUCT] Studio 平台产品功能**，不是 [BASE-ADK]-python 开源库中的代码实现。[BASE-ADK] 提供了 `harness_extension` 这个通用集成点，但 [BASE-AGENT] 专属的 session 管理逻辑在闭源的 Studio BFF 中。

---

## 补充核验：[BASE-ADK] Agent 核心能力清单

基于 `[BASE-ADK]/agent.py` 源码，Agent 类实际支持的特性：

| 特性 | 代码证据 |
|---|---|
| 多模型 fallback | `model_fallbacks: list[ModelFallbackConfig]`，通过 LiteLLM fallback 实现 |
| 模型切换 | `update_model(model_name)` 方法 |
| 知识集成 | `knowledgebase: Optional[KnowledgeBase]`，自动挂载 `LoadKnowledgebaseTool` |
| 短期记忆 | `short_term_memory: Optional[ShortTermMemory]` |
| 长期记忆 | `long_term_memory: Optional[LongTermMemory]`，自动挂载 `load_memory` 工具 |
| 技能系统 | `skills: list[str]`，`skills_mode: Literal["skills_sandbox", "aio_sandbox", "local"]` |
| 动态技能加载 | `enable_dynamic_load_skills: bool`，通过 `check_skills` before_agent_callback |
| 技能检查清单 | `enable_skills_checklist: bool` |
| 追踪/可观测性 | `tracers: list[BaseTracer]`，支持 APMPlus/Cozeloop/TLS 导出器 |
| 授权检查 | `enable_authz: bool`，通过 `before_agent_callback` 注入 |
| 自动会话保存 | `auto_save_session: bool`，通过 `after_agent_callback` 注入 |
| 多运行时 | `runtime: Literal["adk", "codex", "piagent"]` |
| A2UI | `enable_a2ui: bool`，agent 驱动的声明式 UI |
| Tunnel | `enable_tunnel: bool`，本地 MCP 服务器隧道 |
| 飞书 channel | `enable_feishu` 参数在 `create_[PRODUCT]_app` 中启用 |
| 数据集生成 | `enable_dataset_gen: bool`，通过 after_agent_callback |
| Ghostchar | `enable_ghostchar: bool`，角色前缀工具 |
| Supervisor 模式 | `enable_supervisor: bool`，使用 `SupervisorSingleFlow`/`SupervisorAutoFlow` |
| 示例存储 | `example_store: Optional[BaseExampleProvider]` |
| Run Processor | `run_processor: Optional[BaseRunProcessor]`，支持认证/日志/错误处理 |
