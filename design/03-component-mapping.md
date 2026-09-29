# 03 — 14 个 [PRODUCT] 组件映射表

> 版本：v0.2（设计稿）
> 撰写日期：2026-09-18
> 修订日期：2026-09-18（v0.2：ADK workflow 改用真实 import 组件；[BASE-ADK] 角色重定位；API 事实修正；详见文末「修订记录」）
> 说明：每行回答「这个组件在 [DELIVERY] 自身扮演什么角色 / 目标 Agent 什么时候该选它 / 对应哪个 Skill 文件 / 前置依赖 / 验证状态」。
> 验证状态图例：✅=SKILL.md 已完成；🟡=目录已建、SKILL.md 创建中；🔧=尚需新建。

---

## 1. 总览矩阵

| # | 组件 | [DELIVERY] 自身角色 | 目标 Agent 可选角色 | 对应 Skill 文件 | 前置依赖 | 验证状态 |
|---|---|---|---|---|---|---|
| 1 | **SDK** | [DELIVERY] 入口代码用 `[PRODUCT]SimpleApp` 写 | 所有高代码目标 Agent 的入口骨架 | `skills/[PRODUCT]-sdk/SKILL.md` | 火山账号+AK/SK、Python≥3.10（推荐3.12） | ✅ |
| 2 | **[BASE-ADK]** | [DELIVERY] 自身底座为 [BASE-AGENT] 原生（见 `01-architecture.md` §4）；[BASE-ADK] 作为**目标 Agent 的高代码框架选项**，且方案 B 下可作 wrapper 的协议复用方 | 高代码目标 Agent 的 Agent/Runner 本体；或 [BASE-AGENT] 包成 `BaseAgent` wrapper 时复用其 Runtime 协议 | `skills/[BASE-ADK]/SKILL.md` | `[BASE-ADK]-python`（与 [PRODUCT]-sdk-python 分两个包装） | 🟡 |
| 3 | **ADK workflow** | [DELIVERY] 引导状态机可借 Sequential/Parallel/Loop/Supervisor 表达（仅方案 B wrapper 场景下编排 [BASE-AGENT] 节点） | 多步编排（顺序/并行/循环/A2A/Supervisor） | `skills/adk-workflow/SKILL.md` | [BASE-ADK] Agent；需多 Agent 拓扑 | 🟡 |
| 4 | **知识库 (VikingDB RAG)** | [DELIVERY] 自演化沉淀的文档可入知识库供检索 | 文档问答 / RAG 类目标 | `skills/[PRODUCT]-knowledge-base/SKILL.md` | VikingDB 知识库已建并导入；`DATABASE_VIKING_COLLECTION` | ✅ |
| 5 | **A2A Registry** | [DELIVERY] 与目标 Agent 互相发现时注册 | 多 Agent 互相调用（Provider/Consumer） | `skills/[PRODUCT]-a2a-registry/SKILL.md` | 已建 A2aSpace；Runtime 开启注册 | ✅ |
| 6 | **Skills** | [DELIVERY] 自身组件能力全部 Skill 化 | 把业务方法/SOP 沉淀为可复用 Skill | `skills/[PRODUCT]-skills/SKILL.md` | Skills Space；Skill 三种挂载方式 | 🟡 |
| 7 | **网关 / MCP** | [DELIVERY] 调企业存量 API 经此接入 | 目标 Agent 调企业系统 / 模型代理 | `skills/[PRODUCT]-gateway-mcp/SKILL.md` | 已建 MCPService/MCPToolset；入站 Auth | 🟡 |
| 8 | **身份权限** | [DELIVERY] 自身受 UserPool+Cedar 保护 | 目标 Agent 上线真人用户前的 AuthN/AuthZ | `skills/[PRODUCT]-identity-permission/SKILL.md` | UserPool/WorkloadPool/Credential Provider | ✅ |
| 9 | **安全围栏** | [DELIVERY] 自身防注入/防滥用 | 目标 Agent 对公网/敏感数据场景必开 | `skills/[PRODUCT]-guardrails/SKILL.md` | Runtime 勾选开启（大模型应用防火墙） | 🟡 |
| 10 | **评测** | [DELIVERY] 用评测集回归「引导质量」 | 目标 Agent 准出门禁 + 评测集回流 | `skills/[PRODUCT]-evaluation/SKILL.md` | 必须先开启观测；评测集/评估器/实验 | 🟡 |
| 11 | **观测** | [DELIVERY] Step4 真实取数的唯一数据源 | 所有目标 Agent 排障与 trace 来源 | `skills/[PRODUCT]-observability/SKILL.md` | Runtime 开启 APMPlus+TLS | 🟡 |
| 12 | **沙箱 Sandbox** | [DELIVERY] 让 Codex 在隔离环境生成/验证代码与 Skill | 目标 Agent 跑代码/不可信逻辑/并行子任务 | `skills/[PRODUCT]-sandbox/SKILL.md` | 沙箱模板；`[PRODUCT]_TOOL_ID` | 🟡 |
| 13 | **Runtime** | [DELIVERY] 自身部署载体；也承载目标 Agent | 目标 Agent 的托管服务实例 | `skills/[PRODUCT]-runtime/SKILL.md` | CR 镜像、模型 Key、观测、关联组件 | ✅ |
| 14 | **会话记忆管理** | [DELIVERY] 跨会话记住用户项目状态 | 目标 Agent 多轮/跨会话体验 | `skills/[PRODUCT]-session-memory/SKILL.md` | 会话资源(PG/Serverless PG)+记忆库(mem0/viking) | 🟡 |

---

## 2. 逐组件使用决策逻辑（什么时候选 / 不选）

### 2.1 SDK
- **选**：任何要写 Python 入口代码的目标 Agent（几乎所有高代码场景）。
- **不选**：纯 Studio 可视化搭建、不写代码的场景。
- **证据**：`20-sdk-ref.md` 装饰器式 API；`03-[PRODUCT]-sdk.md` §1 两包独立安装。

### 2.2 [BASE-ADK]
- **选**：目标 Agent 需要火山引擎深度集成（记忆/知识库/工具/A2A/tracer），或方案 B 下要复用 [BASE-ADK] 的 Runtime 协议。
- **不选**：仅做纯 HTTP 壳；或 [DELIVERY] 自身底座（[DELIVERY] 用 [BASE-AGENT] 原生 loop，见 `01-architecture.md` §4）。
- **证据**：`18-[BASE-ADK].md`；`02-[BASE-ADK]-verification.md` 声明 a（Agent 继承 LlmAgent）；`05-...verification.md` §7（方案 B wrapper）。

### 2.3 ADK workflow
- **选**：目标 Agent 需多步/多 Agent 编排。
- **不选**：单轮问答、单工具调用。
- **组件清单以 [BASE-ADK] 真实 import 为准**（证据：`05-...verification.md` §5c，来自 `[BASE-ADK]/integrations/[PRODUCT]/app.py` 的 import 段）：
  - 编排节点：`SequentialAgent`、`ParallelAgent`、`LoopAgent`、`RemoteA2aAgent`（远程 A2A）、`Supervisor`（collaborative 协调器；本次未在 app.py 直接见到其 import，按 ADK 标准协作组件归类）。
  - 运行时对象：`Runner`（`google.adk.runners.Runner`）、`RunConfig`、`StreamingMode.SSE / StreamingMode.NONE`、`App(name, root_agent, plugins)`、`RunAgentRequest`。
  - `_agent_type()` 实际识别：`loop / sequential / parallel / a2a / llm`（LLM agent 即 `LlmAgent`，不在编排三件套里就归 `llm`）。
- **不用「Graph/Dynamic/Collaborative/Template 四模式」概括**：`adk.dev/workflows/` 页面本体确认四大类 + 实验特性 Agent Routing，但 **graph/dynamic/collaborative/template/agent-routing 子页面多次尝试均 `link dead`（疑似客户端路由/slug 变更），子页面正文「未获取」，不臆造其参数表**。组件名以上述 [BASE-ADK] 真实 import 为准。
- **注意**：这些编排组件都以 `BaseAgent` 为节点类型。[BASE-AGENT] 若要被它们编排，需包一层「长得像 `BaseAgent` 的 wrapper」（方案 B，见 `01-architecture.md` §4.3）；若 [DELIVERY] 自己用 [BASE-AGENT] loop 做主、仅在边缘调 [BASE-ADK] 工具，则不强制走这些编排。

### 2.4 知识库 (VikingDB)
- **选**：目标是「基于企业文档回答」，且有可入库的语料。
- **不选**：纯工具调用、无文档问答诉求；语料过少时先不建库。
- **证据**：`10-knowledge-base.md`；`09-session-memory.md` 区分「知识库=知道什么事实」vs「记忆=用户画像/偏好」。

### 2.5 A2A Registry
- **选**：有≥2 个 Agent 需要互相发现调用、跨团队协作。
- **不选**：单 Agent；任务能在单 Agent 内完成。
- **证据**：`08-a2a.md`；`doc04.md` A2A 网关；`[SHARD-2]-results.md` §38 SearchAgentCards。
- **SearchAgentCards 入参（已核验）**：`SpaceId`（A2A 空间 ID，必选）+ `Prompt`（自然语言意图，必选）+ `TopK`（返回前 K 个，必选）；返回 `TotalCount` + `AgentCards`（JSON 文本）。**前置条件**：需先在 CreateA2aSpace/UpdateA2aSpace 开启 `IntentEnabled=true`（语义检索）。
- **注意**：复杂 Agent Mesh/Team 仍 POC 非现网（`doc04.md`）。

### 2.6 Skills
- **选**：业务有可复用 SOP/方法论，要跨场景沉淀。
- **不选**：一次性临时脚本。
- **证据**：`07-skills.md`；`doc01.md` 三种挂载（Hub slug / Space 全量 / space:skill 精准）。
- **坑**：Skill Hub 只发内容不分发其声明的 MCP，MCP 需自配（`doc01.md`）。

### 2.7 网关 / MCP
- **选**：目标 Agent 要调企业存量 API / 已有 MCP Server / 需统一模型代理。
- **不选**：仅用平台内置工具、不接外部系统。
- **证据**：`11-gateway.md`；`doc04.md`（OpenAPI 转 MCP、凭据托管、语义检索降本 60%）。
- **坑**：Runtime 网关与 MCP 网关是两套独立实例、分别计费（`11-gateway.md`）。

### 2.8 身份权限
- **选**：目标 Agent 要给真人用户用、或调受保护后端。**生产必选**。
- **不选**：纯离线沙箱 POC、单用户 demo（可临时用 API Key，但不得冒充 Workload Identity）。
- **证据**：`12-identity-permission.md`；`doc06.md` 八步身份链、四职责分离、负向测试。
- **坑**：API Key ≠ Workload Identity；Allowed Clients 空=允许所有人；ID Token 不能当 Bearer（`doc06.md`）。

### 2.9 安全围栏
- **选**：目标 Agent 暴露公网、处理 PII、防提示词注入。
- **不选**：纯内网受控环境且无外部输入风险。
- **证据**：`13-guardrails.md`（OWASP LLM Top10：注入/滥用/敏感数据/算力）。

### 2.10 评测
- **选**：任何要迭代/上线的目标 Agent（Eval-driven 的核心）。
- **不选**：一次性 demo、无回归诉求。
- **证据**：`15-evaluation.md`；`doc07.md`（trace 回流、评估器、准出门禁）。
- **前置硬约束**：必须先开观测（`05-runtime.md`「在线评测必须开启」）。

### 2.11 观测
- **选**：几乎必选——Step4 取数依赖、评测依赖、排障依赖。
- **不选**：无（设计上所有目标 Agent 默认开）。
- **证据**：`14-observability.md`（APMPlus+TLS）；`doc07.md`（同一条 trace 排障）。

### 2.12 沙箱 Sandbox
- **选**：目标 Agent 要执行代码/跑测试/验证不可信逻辑/并行子任务。
- **不选**：纯问答、不执行代码。
- **证据**：`06-sandbox.md`；`doc02.md` 沙箱选型矩阵（AIO/Skills/Code/ArkClaw/[BASE-AGENT]）；`[SHARD-1]-results.md` CreateTool。
- **ToolType 取值（已核验）**：`All-in-one / Skill / Private / CodeEnv / PersonalAssistant / VibeSkill`（CreateTool 必选；UpdateTool/GetTool 返回同枚举）。自定义工具需 `Command`（默认 `./run.sh`）、`Port`（默认 8000）、`ImageUrl`。
- **坑**：TOS 只挂产物/工作空间，别全量挂；session 隔离（`doc02.md`）。

### 2.13 Runtime
- **选**：目标 Agent 要成为在线服务。
- **不选**：纯本地脚本。
- **证据**：`05-runtime.md`；`skills/[PRODUCT]-runtime/SKILL.md`。
- **配额**：单地域 Runtime ≤20、实例 ≤20、最低 0.5 vCPU（`01-overview.md` §4）。

### 2.14 会话记忆管理
- **选**：目标 Agent 需要多轮连续、或跨会话记住用户偏好/项目状态。
- **不选**：严格单轮无状态问答。
- **证据**：`09-session-memory.md` 三层架构（Session/短期/长期）。
- **坑**：长期记忆约 1 分钟抽取后才可读出；`viking_mem` 已废弃转 `viking`（`03-[PRODUCT]-sdk.md` §2.2）。

---

## 3. 组件间依赖拓扑（[DELIVERY] 引导时按此顺序）

```
SDK / [BASE-ADK]  (写代码骨架)
   │
   ├─► Runtime          (部署载体，几乎一切的底座)
   │      ├─► 观测      (必须先开，否则评测/排障瞎)
   │      ├─► 评测      (依赖观测)
   │      ├─► 安全围栏  (公网/PII 场景)
   │      └─► 身份权限  (真人用户/受保护后端)
   ├─► 知识库           (RAG 语料)
   ├─► 会话记忆         (多轮/跨会话)
   ├─► Skills           (沉淀 SOP)
   ├─► 沙箱             (代码执行)
   ├─► 网关/MCP         (外部系统接入)
   └─► A2A Registry     (多 Agent 协作，最后接)
```

引导顺序原则：**先 Runtime+观测（能跑能看）→ 再业务组件（知识库/记忆/沙箱/网关）→ 最后治理（身份/围栏/评测门禁）→ 多 Agent（A2A）**。

---

## 4. 验证状态与缺口

| 状态 | 组件 | 说明 |
|---|---|---|
| ✅ 已完成 SKILL.md | SDK、Runtime、知识库、A2A Registry、身份权限 | 可直接被 [DELIVERY] 调用 |
| 🟡 SKILL.md 创建中 | [BASE-ADK]、ADK workflow、Skills、网关/MCP、安全围栏、评测、观测、沙箱、会话记忆 | 设计文档已引用其路径；内容完成后 [DELIVERY] 即可加载 |
| 🔧 需新建 | `grill-with-docs`（[DELIVERY] 访谈引导）、[BASE-AGENT] 薄 FastAPI shim（讲 Runtime HTTP 协议，见 `01-architecture.md` §4.2） | 非 [PRODUCT] 组件，属 [DELIVERY] 自研；自进化是 [BASE-AGENT] 原生能力，不需单独「[BASE-AGENT]-sidecar」桥接 Skill |

> 注：本文所有「验证状态」指 **Skill 文档是否完成**，**不代表**对应云资源已部署接通。云资源接通状态统一在 `01-architecture.md` §8 待核验清单中跟踪。

---

## 修订记录

### v0.2（2026-09-18）

1. **ADK workflow 去四模式概括**：不再用「Graph/Dynamic/Collaborative/Template」概括，改用 [BASE-ADK] 真实 import 的组件（`SequentialAgent / ParallelAgent / LoopAgent / RemoteA2aAgent / Supervisor / RunConfig / Runner / App / StreamingMode`）；标注 `adk.dev/workflows/` 子页面 `link dead`、正文「未获取」，不臆造参数表。
2. **[BASE-ADK] 角色重定位**：[DELIVERY] 自身底座改为 [BASE-AGENT] 原生（见 `01-architecture.md` §4），[BASE-ADK] 降为「目标 Agent 高代码框架选项 / 方案 B wrapper 的协议复用方」；§2.2「不选」措辞同步修正。
3. **API 事实修正**：补充 SearchAgentCards 入参（`SpaceId+Prompt+TopK`，前置 `IntentEnabled=true`）；补充 ToolType 取值枚举（`All-in-one/Skill/Private/CodeEnv/PersonalAssistant/VibeSkill`）。
4. **验证状态表**：删除「[BASE-AGENT]-sidecar（[BASE-AGENT] MCP 桥接）」这一需新建项——自进化是 [BASE-AGENT] 原生能力，改为新增「[BASE-AGENT] 薄 FastAPI shim」自研项。
5. **保留正确部分**：14 组件矩阵、逐组件选/弃决策逻辑、依赖拓扑引导顺序、验证状态图例——均保留。
