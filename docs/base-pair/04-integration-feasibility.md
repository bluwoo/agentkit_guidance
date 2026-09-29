# [BASE-AGENT] + [BASE-ADK] + [PRODUCT] SDK 集成可行性判断

> 核验时间：2026-09-18
> 基于对 [BASE-AGENT] Agent 源码结构、[BASE-ADK] 实际代码、[PRODUCT] SDK 文档的逐项核验
>
> **底座决策更新（2026-09-18 v0.2）**：本文原以「[BASE-ADK] 为 [DELIVERY] 底座、[BASE-AGENT] 为 sidecar/被集成方」为前提做可行性分析，其中「[BASE-AGENT] 自进化机制移植到 [BASE-ADK]」等结论对应**旧方案 C / 旧底座假设**，现已**不采用**。最终底座决策见 `05-[BASE-AGENT]-as-base-verification.md` 与 `design/01-architecture.md`：**[DELIVERY] 底座 = [BASE-AGENT] 原生主循环（`AIAgent.run_conversation`）+ 薄 FastAPI shim**，自进化是 [BASE-AGENT] 原生能力，**不需要移植到 [BASE-ADK]**。本文保留作为技术可行性证据，不代表当前推荐架构。

---

## 总体判断

| 集成场景 | 可行性 | 说明 |
|---|---|---|
| [BASE-ADK] Agent 运行在 [PRODUCT] Runtime 上 | ✅ **完全可行** | 已有成熟模板和文档 |
| [BASE-ADK] LongTermMemory 连接 [PRODUCT] 平台记忆资源 | ✅ **完全可行** | mem0/VikingDB 后端已实现 |
| [BASE-AGENT] Agent 作为 [BASE-ADK] Agent 运行 | ❌ **不可行** | 架构不兼容（非 ADK LlmAgent 子类） |
| [BASE-AGENT] 自进化机制移植到 [BASE-ADK] | ⚠️ **需要额外开发** | 概念可移植，代码需重写 |
| [BASE-AGENT] 作为 [PRODUCT] Studio 管理的外部 Agent Session | ⚠️ **平台侧已支持，Runtime 侧需适配** | README 已声明，[BASE-ADK] 提供 harness_extension 通用接口 |
| [BASE-AGENT] 与 [BASE-ADK] 通过 MCP 互操作 | ✅ **可行** | 双方都支持 MCP 协议 |

---

## 1. 已验证可行的集成

### 1.1 [BASE-ADK] + [PRODUCT] Runtime（已验证）

**证据**：
- Runtime quickstart 文档展示完整的 `[PRODUCT]SimpleApp` + [BASE-ADK] `Agent` + `Runner` 示例
- `create_[PRODUCT]_app` 工厂函数已完整实现（`[BASE-ADK]/integrations/[PRODUCT]/app.py`，9664 行）
- 支持两种部署路径：`[PRODUCT]SimpleApp`（轻量）和 `create_[PRODUCT]_app`（全功能 Studio 集成）

**集成方式**：
```python
from [BASE-ADK] import Agent, Runner
from [PRODUCT].apps import [PRODUCT]SimpleApp

app = [PRODUCT]SimpleApp()
agent = Agent(name="my_agent", instruction="...")
runner = Runner(agent=agent, app_name="my_app")

@app.entrypoint
async def run(payload, headers):
    # 业务逻辑
    ...

app.run(host="0.0.0.0", port=8000)
```

### 1.2 [BASE-ADK] LongTermMemory + [PRODUCT] 平台记忆（已验证）

**证据**：
- Memory quickstart 文档展示 mem0 和 VikingDB 两种后端的完整配置
- `LongTermMemory` 类继承 ADK `BaseMemoryService`，后端工厂支持 8 种存储
- 通过 `[PRODUCT].yaml` 中的 `runtime_envs` 注入连接信息

### 1.3 [BASE-AGENT] ↔ [BASE-ADK] 通过 MCP 互操作（可行，未验证但协议兼容）

**分析**：
- [BASE-AGENT] 有原生 MCP 客户端（stdio + HTTP + OAuth 2.1），支持连接任意 MCP server
- [BASE-ADK] 支持 MCP 工具集（通过 Google ADK 的 MCP 集成，且 patched MCP session retry）
- **集成路径 A**：[BASE-ADK] 作为 MCP server 暴露工具，[BASE-AGENT] 连接使用
- **集成路径 B**：[BASE-AGENT] 的 `mcp_serve.py` 可启动为 MCP server，[BASE-ADK] 连接使用

**限制**：这是工具级互操作，不是 Agent 级集成。[BASE-AGENT] 和 [BASE-ADK] Agent 各自独立运行，仅通过 MCP 共享工具。

---

## 2. 需要额外开发的集成

### 2.1 [BASE-AGENT] 自进化机制移植到 [BASE-ADK]

**现状**：
- [BASE-AGENT] 的自进化 = 后台审查 Fork + 自主记忆管理 + 自主技能创建/改进
- [BASE-ADK] 有 `auto_save_session`（自动保存到长期记忆）和 `skills` 系统，但**无后台审查、无自主技能创建、无技能自改进**

**移植方案分析**：

| [BASE-AGENT] 机制 | [BASE-ADK] 对应 | 移植难度 | 说明 |
|---|---|---|---|
| 后台审查 Fork | 无 | **高** | 需要在 `Runner` 或 `Agent` 层添加 after_agent_callback 触发后台审查进程，重放对话并调用记忆/技能管理工具 |
| memory 工具（add/replace/remove） | `LongTermMemory` + `load_memory` 工具 | **中** | [BASE-ADK] 的长期记忆是 ADK BaseMemoryService 接口，存储到外部后端（mem0/VikingDB）。需要封装为 [BASE-AGENT] 风格的 add/replace/remove 操作 |
| 自主技能创建 | `skills: list[str]` + `load_skills()` | **高** | [BASE-ADK] 的技能是预加载的，不支持运行时自主创建新技能。需要新增技能管理工具 |
| 技能自改进 | 无 | **高** | 需要 patch 现有 SKILL.md 的能力 |
| FTS5 跨会话搜索 | 无（[BASE-ADK] 有 session_service 但无全文搜索） | **中** | 可在 ShortTermMemory 层添加 FTS5 索引 |
| 写入审批（write_approval） | 无 | **低** | 可通过 `run_processor` 或 callback 机制实现 |

**结论**：概念可移植，但需要在 [BASE-ADK] 中开发约 2000-3000 行新代码，包括：
1. 后台审查 Fork 调度器
2. 记忆 curation 工具（add/replace/remove 语义）
3. 技能自主创建/改进工具
4. 写入审批队列 UI/API

### 2.2 [BASE-AGENT] 作为 [PRODUCT] Studio 管理的外部 Agent

**现状**：
- [BASE-ADK] 提供 `harness_extension` 通用接口（`create_[PRODUCT]_app(harness_extension=...)`）
- 要求扩展对象提供 `sidecar_status_payload()` 和 `close()` 方法
- README 声明 "Studio manages user-owned Codex, OpenClaw, and [BASE-AGENT] [PRODUCT] Sessions"
- **但 [BASE-ADK] 代码中无 [BASE-AGENT] 专属实现**（GitHub code search 零结果）

**需要的开发工作**：
1. 实现一个 `[BASE-AGENT]HarnessExtension` 类，封装 [BASE-AGENT] 的启动/停止/状态查询
2. [BASE-AGENT] 需要以 sidecar 方式运行在 [PRODUCT] Runtime 环境中
3. Studio BFF 侧需要实现 [BASE-AGENT] session 的创建/管理/删除（闭源平台侧）
4. [BASE-AGENT] 的 UI/Terminal 需要通过 Studio 嵌入（可能需要 iframe 或 WebSocket 代理）

**可行性**：技术上可行（`harness_extension` 接口已就绪），但需要：
- [BASE-AGENT] 适配 [PRODUCT] Runtime 的容器环境
- Studio BFF 侧的 [BASE-AGENT] session 管理逻辑（不在开源仓库中）

---

## 3. 不可行的集成

### 3.1 [BASE-AGENT] Agent 直接作为 [BASE-ADK] Agent 运行

**原因**：
- [BASE-ADK] `Agent` 继承 `google.adk.agents.LlmAgent`，依赖 ADK 的 event/session/tool 抽象
- [BASE-AGENT] 有完全独立的 agent loop、状态管理和工具系统
- [BASE-AGENT] 不实现 `BaseAgent` 接口，无法被 `Runner` 或 `[PRODUCT]AgentServerApp` 接受

**结论**：[BASE-AGENT] 不能直接替换 [BASE-ADK] Agent。它是一个独立的完整 Agent 框架。

### 3.2 [BASE-AGENT] 记忆系统直接替换 [BASE-ADK] LongTermMemory

**原因**：
- [BASE-AGENT] 记忆是 `MEMORY.md` + `USER.md` 文件 + SQLite FTS5，注入 system prompt
- [BASE-ADK] LongTermMemory 实现 ADK `BaseMemoryService` 接口，存储到外部后端
- 两者接口和数据模型完全不同

**替代方案**：
- 可以实现一个 `[BASE-AGENT]MemoryBackend` 类，将 [BASE-ADK] 的记忆操作路由到 [BASE-AGENT] 的文件/SQLite 系统
- 但这需要额外的桥接层，且 [BASE-AGENT] 的记忆是进程本地的，不适合多实例 Runtime

---

## 4. 推荐的集成架构

### 方案 A：[BASE-ADK] 为主，[BASE-AGENT] 为 MCP 工具提供方（推荐，可行性最高）

```
┌─────────────────────────────────────────┐
│  [PRODUCT] Studio / Runtime              │
│  ┌───────────────────────────────────┐  │
│  │  [BASE-ADK] Agent (LlmAgent 子类)      │  │
│  │  ├── LongTermMemory (mem0/Viking)│  │
│  │  ├── ShortTermMemory              │  │
│  │  ├── KnowledgeBase                │  │
│  │  └── MCP Client ──────┐          │  │
│  └───────────────────────┼──────────┘  │
│                          │ MCP stdio   │
│  ┌───────────────────────▼──────────┐  │
│  │  [BASE-AGENT] Agent (mcp_serve.py)     │  │
│  │  ├── 技能库 (SKILL.md)           │  │
│  │  ├── 终端工具                     │  │
│  │  └── 自主记忆（[BASE-AGENT] 本地）      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**优点**：
- 不需要修改 [BASE-AGENT] 或 [BASE-ADK] 核心代码
- [BASE-AGENT] 的技能库和终端能力通过 MCP 暴露给 [BASE-ADK] Agent
- [BASE-ADK] 仍管理会话、长期记忆和 Runtime 部署

**缺点**：
- [BASE-AGENT] 的自进化（后台审查、自主技能创建）在 [BASE-ADK] 对话流中不会自动触发
- 需要手动管理 [BASE-AGENT] sidecar 进程

### 方案 B：[BASE-AGENT] 为主，[BASE-ADK] 能力为 MCP 工具（适合已有 [BASE-AGENT] 部署）

```
┌─────────────────────────────────────────┐
│  [BASE-AGENT] Agent (主 Agent)                 │
│  ├── 自进化学习循环                      │
│  ├── MEMORY.md / USER.md                │
│  ├── 技能系统（自主创建/改进）           │
│  ├── MCP Client ──────┐                 │
│  └── Gateway (Telegram/Discord)       │ │
└────────────────────────┼───────────────┘
                         │ MCP HTTP
┌────────────────────────▼───────────────┐
│  [BASE-ADK] Agent (作为 MCP server)          │
│  ├── KnowledgeBase RAG                  │
│  ├── 火山引擎工具                       │
│  └── LongTermMemory (mem0)              │
└─────────────────────────────────────────┘
```

**优点**：
- [BASE-AGENT] 的自进化能力完全保留
- [BASE-ADK] 的火山引擎集成能力通过 MCP 暴露

**缺点**：
- 需要开发 [BASE-ADK] → MCP server 的桥接层（[BASE-ADK] 原生不是 MCP server）
- 不使用 [PRODUCT] Runtime 部署

### 方案 C：Studio Harness Extension 集成（平台级，需平台侧开发）

```
┌─────────────────────────────────────────┐
│  [PRODUCT] Studio (Web UI)              │
│  ├── [BASE-AGENT] Session 管理               │
│  ├── Codex Session 管理                │
│  └── [BASE-ADK] Runtime 管理                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  [PRODUCT] Runtime ([BASE-ADK] 进程)          │
│  ├── [BASE-ADK] Agent + Runner               │
│  ├── create_[PRODUCT]_app()              │
│  │   └── harness_extension ──┐         │
│  └── /web/harness-sidecar/status       │
└──────────────────────────────┼─────────┘
                               │
                    ┌──────────▼──────────┐
                    │  [BASE-AGENT] sidecar     │
                    │  (独立进程)          │
                    └─────────────────────┘
```

**需要的开发**：
1. [BASE-ADK] 侧：实现 `[BASE-AGENT]HarnessExtension`（~200 行）
2. Studio BFF 侧：[BASE-AGENT] session CRUD 管理（闭源）
3. [BASE-AGENT] 侧：适配 Runtime 容器环境，暴露 status API

---

## 5. 待核验项

| 项目 | 原因 |
|---|---|
| [PRODUCT] SDK 的 Skills 文档具体内容 | 文档页链接失效，未能读取 |
| [PRODUCT] SDK 的 Observability 文档具体内容 | 文档页链接失效，未能读取 |
| [BASE-ADK] `harness_extension` 的实际使用示例 | 仓库中无 [BASE-AGENT] 专属扩展代码 |
| Studio BFF 侧 [BASE-AGENT] session 管理实现 | 闭源，不在开源仓库中 |
| [BASE-ADK] 是否有 [BASE-AGENT] 兼容的 MCP server 模式 | 未在代码中发现 |
| [BASE-AGENT] `mcp_serve.py` 的实际 MCP 工具暴露范围 | 未深入核验源码 |

---

## 6. 总结

1. **[BASE-ADK] + [PRODUCT] SDK 的集成已成熟**：有完整的工厂函数、模板和文档，可直接用于生产部署。

2. **[BASE-AGENT] 是独立框架，与 [BASE-ADK]/[PRODUCT] 无代码级集成**：[BASE-AGENT] 不继承 ADK LlmAgent，不使用 [PRODUCT] SDK，[BASE-ADK] 代码中无 [BASE-AGENT] 引用。

3. **"[BASE-AGENT] [PRODUCT] Sessions" 是 Studio 平台功能**：README 描述的是 Studio 管理外部 Agent session 的产品能力，Runtime 侧仅提供通用的 `harness_extension` 接口。[BASE-AGENT] 专属的 session 管理在闭源 Studio BFF 中。

4. **最可行的集成路径是 MCP 互操作**：双方都支持 MCP 协议，可通过 MCP server 桥接共享工具和能力，无需修改核心框架。

5. **[BASE-AGENT] 自进化机制移植到 [BASE-ADK] 需大量开发**：概念可移植（后台审查、记忆 curation、技能创建），但需要在 [BASE-ADK] 中新建约 2000-3000 行代码。


---

## 措辞与契约修正记录（2026-09-18）

- 文首新增底座决策更新说明：原「[BASE-AGENT] 自进化移植到 [BASE-ADK]」对应旧方案 C/旧底座假设，现已不采用；最终底座为 [BASE-AGENT] 原生主循环 + 薄 FastAPI shim，自进化为原生能力。本文保留为可行性证据，不代表当前推荐架构。
