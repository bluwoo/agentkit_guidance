# [BASE-AGENT] Agent 架构摘要与自进化机制

> 核验时间：2026-09-18
> 仓库：https://github.com/NousResearch/[BASE-AGENT]-agent
> 证据来源：GitHub 仓库页面、官方文档站 [BASE-AGENT]-agent.nousresearch.com

---

## 1. 定位与本质

[BASE-AGENT] Agent 是由 **Nous Research** 开发的**自托管、自改进 AI Agent**，MIT 许可证。

**它不是基于 Google ADK 或 [BASE-ADK] 构建的。** 它是一个完全独立的 Agent 框架，拥有自己的 agent loop、状态管理、工具系统和记忆系统。

核心定位（来自 README）：
> "The self-improving AI agent built by Nous Research. It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions."

---

## 2. 代码架构

### 2.1 仓库顶层结构

| 目录/文件 | 职责 |
|---|---|
| `agent/` | 核心 agent 循环、prompt 构建、工具调度 |
| `apps/` | 应用层（gateway、bot 模式等） |
| `[BASE-AGENT]_cli/` | CLI 命令实现 |
| `gateway/` | 消息平台网关（Telegram/Discord/Slack 等 20+ 平台） |
| `skills/` | 内置技能目录 |
| `tools/` | 内置工具实现 |
| `plugins/` | 插件系统 |
| `providers/` | LLM 提供商适配 |
| `cron/` | 定时任务调度器 |
| `acp_adapter/` | ACP（Agent Communication Protocol）编辑器集成 |
| `tui_gateway/`, `ui-tui/` | TUI 界面 |
| `optional-mcps/` | 官方审核的 MCP 服务器目录 |
| `optional-skills/` | 可选技能目录 |
| `evals/` | 评估与轨迹生成 |
| `[BASE-AGENT]_state*.py`（~20 个文件） | SQLite 状态管理（会话、消息、FTS5 搜索、WAL、压缩等） |
| `mcp_serve.py` | MCP 服务器模式 |
| `cli.py` | CLI 入口 |
| `batch_runner.py` | 批量轨迹生成 |

### 2.2 关键技术栈

- **语言**：Python 3.11+（核心），Node.js（部分工具/TUI）
- **LLM 抽象**：自研，支持 40+ 提供商（Nous Portal、OpenRouter、OpenAI、Anthropic、DeepSeek 等），**不使用 LiteLLM 或 Google ADK**
- **状态存储**：SQLite（`~/.[BASE-AGENT]/state.db`），含 FTS5 全文索引
- **MCP 客户端**：原生实现，支持 stdio 和 HTTP/SSE 服务器，OAuth 2.1 自动完成
- **终端后端**：7 种（local、Docker、SSH、Singularity、Modal、Daytona、Vercel Sandbox）
- **技能标准**：兼容 [agentskills.io](https://agentskills.io) 开放标准

---

## 3. 自进化（自改进）机制详解

[BASE-AGENT] 的"自进化"不是单次训练微调，而是一个**运行时闭环学习循环**，由以下子系统组成：

### 3.1 后台审查 Fork（Background Review Fork）

这是自进化的核心引擎。

- **触发时机**：每轮对话结束后自动 fork 一个后台审查进程
- **机制**：重放完整对话（利用 prompt cache 降低成本），判断哪些内容值得持久化
- **可配置**：
  - `auxiliary.background_review.enabled: false` 可关闭自动审查
  - `auxiliary.background_review.model` 可指定更便宜的模型（如 gemini-3-flash）
  - `auxiliary.background_review.defer: auto` 在本地 GPU 模式下延迟到空闲时执行
- **审查权限**：默认可使用 memory、skill-management、只读文件工具；可通过 `extra_tools` 窄范围扩展
- **手动触发**：`/refine` 命令可手动触发

> 证据来源：https://[BASE-AGENT]-agent.nousresearch.com/docs/user-guide/features/memory （"Background review notifications" 和 "Running the review on a cheaper model" 章节）

### 3.2 代理管理的持久记忆

| 文件 | 用途 | 字符上限 |
|---|---|---|
| `MEMORY.md` | 代理个人笔记（环境事实、约定、学到的经验） | 2,200 字符（~800 tokens） |
| `USER.md` | 用户画像（偏好、沟通风格、期望） | 1,375 字符（~500 tokens） |

- **存储位置**：`~/.[BASE-AGENT]/memories/`
- **注入方式**：会话开始时作为冻结快照注入 system prompt
- **管理工具**：`memory` 工具，支持 `add` / `replace` / `remove` 操作
- **容量管理**：超限时工具返回错误，代理需自行合并/删除条目后重试
- **安全扫描**：写入前检测 prompt injection、凭证泄露、SSH 后门等模式
- **写入审批**：`memory.write_approval: true` 时，写入进入暂存队列，用户通过 `/memory pending` → `/memory approve/reject` 审批

### 3.3 自主技能创建与自改进

- **技能本质**：`SKILL.md` 格式的按需知识文档，遵循渐进式披露（progressive disclosure）
- **自动创建**：后台审查在复杂任务后自主创建新技能
- **自主改进**：后台审查可以 patch 现有技能（`skill_manage` 工具）
- **`/learn` 命令**：用户可引导代理从任意来源（文档、URL、工作流、PDF）创建技能
- **技能写入审批**：`skills.write_approval: true` 时，技能写入暂存为 diff，用户通过 `/skills diff` → `/skills approve/reject` 审批
- **技能目录**：`~/.[BASE-AGENT]/skills/`，2558+ 社区技能，90 内置，84 可选

> 证据来源：https://[BASE-AGENT]-agent.nousresearch.com/docs/user-guide/features/skills

### 3.4 FTS5 跨会话搜索

- 所有 CLI 和消息平台会话存储在 SQLite（`~/.[BASE-AGENT]/state.db`）
- FTS5 全文索引，~20ms 查询延迟
- 代理通过 `session_search` 工具搜索历史对话
- 支持发现/滚动/浏览三种调用模式
- 无 LLM 摘要、无截断——直接返回原始消息

### 3.5 外部记忆提供商

8 个外部记忆插件与内置记忆并行运行：Honcho（辩证用户建模）、Mem0、Hindsight、Holographic、RetainDB、ByteRover、Supermemory、OpenViking。

### 3.6 自进化机制总结

```
用户对话 → 执行工具 → 任务完成
     ↓
  后台审查 Fork（重放对话）
     ├── 判断值得记忆 → memory 工具写入 MEMORY.md/USER.md
     ├── 判断值得复用 → skill_manage 创建/改进 SKILL.md
     └── 周期 nudge → 提醒代理整理记忆/创建技能
     ↓
  下一会话启动 → 冻结快照注入 system prompt
     ↓
  代理带着更新后的记忆和技能继续工作
```

**关键结论**：[BASE-AGENT] 的自进化是**提示词工程层面的运行时学习**，不涉及模型权重更新。它通过：
1. 后台审查进程自主决策写入记忆/技能
2. 记忆和技能在下次会话时注入 system prompt
3. 技能通过渐进式披露按需加载，不占用固定 token

---

## 4. 与 ADK / [PRODUCT] 的关系

### 4.1 与 Google ADK 的关系

**无直接关系。** [BASE-AGENT] 不依赖、不继承、不兼容 Google ADK 的任何组件：
- 不使用 `google.adk.agents.LlmAgent`
- 不使用 `google.adk.runners.Runner`
- 不使用 ADK 的 event/session/memory service 抽象
- 有自己的 agent loop、自己的 SQLite 状态管理、自己的工具系统

### 4.2 与 [BASE-ADK] 的关系

**无直接代码依赖。** [BASE-ADK] 仓库中搜索 "[BASE-AGENT]" 无任何代码结果（GitHub code search 验证）。

[BASE-ADK] README 中提到的 "[BASE-AGENT] [PRODUCT] Sessions" 是 **[PRODUCT] Studio 平台侧的功能描述**，不是 [BASE-ADK] 代码中集成了 [BASE-AGENT]。详见 `02-[BASE-ADK]-verification.md`。

### 4.3 与 [PRODUCT] SDK 的关系

**无直接关系。** [BASE-AGENT] 不使用 `[PRODUCT]-sdk-python`，不提供 `[PRODUCT]SimpleApp` 或 `[PRODUCT]AgentServerApp` 兼容接口。

---

## 5. 集成点分析

| 集成维度 | [BASE-AGENT] 现状 | 与 [BASE-ADK]/[PRODUCT] 的对接可能性 |
|---|---|---|
| Agent 运行时 | 自研 agent loop，不继承 ADK | **不可直接集成**：[BASE-ADK] Agent 是 ADK LlmAgent 子类，[BASE-AGENT] 不是 |
| 工具系统 | 自研工具系统 + MCP 客户端 | **可通过 MCP 桥接**：[BASE-AGENT] 可作为 MCP server 暴露工具给 [BASE-ADK]，或反之 |
| 记忆系统 | MEMORY.md/USER.md + FTS5 + 外部 provider 插件 | **架构完全不同**：[BASE-ADK] 用 ADK BaseMemoryService 后端，[BASE-AGENT] 用文件+SQLite |
| 技能系统 | SKILL.md 格式，兼容 agentskills.io | **格式兼容**：[BASE-ADK] 也支持 skills（`Agent(skills=[...])`），但加载机制不同 |
| 会话管理 | SQLite state.db，自定义 session | **不兼容**：[BASE-ADK] 用 ADK SessionService |
| 部署模型 | 自托管 CLI/Gateway，7 种终端后端 | **可作为 sidecar/harness 运行**：通过 `harness_extension` 机制接入 Studio |
| 自进化 | 后台审查 Fork + 自主技能创建 | **[BASE-ADK] 无对应机制**：[BASE-ADK] 有 `auto_save_session` 但无自主技能创建/改进 |
