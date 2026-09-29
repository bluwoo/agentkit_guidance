# 架构图规格（02）—— 可交互拓扑、Trace 覆盖层视觉编码

> 文档性质：**设计规格**，定义节点/边的视觉编码与数据映射，不产出渲染代码。
> 核心立场：架构图**不是静态图片，是可交互拓扑**；trace 着色**只反映观测 API 真实返回**，无数据即"无观测数据"，绝不编造调用关系。
> 证据：`docs/hermes-veadk/05-hermes-as-base-verification.md`（Wizard 底座 = Hermes Agent `AIAgent.run_conversation` + 薄 FastAPI shim；ADK 编排组件真实 import 名）、`docs/volcengine-official/shard4-results.md`（日志字段 10 个）、`docs/volcengine-official/browser-gap-results.md`（**浏览器 DOM 补读成功：AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool 字段**）、`00-directory.md`（组件清单）、`doc07.md`（APMPlus trace、Follow gen.ai 语义）。
>
> **修订基线（2026-09-18，v1.2）**：① Wizard 底座节点须标注为 Hermes Agent（`AIAgent.run_conversation`）+ FastAPI Shim（Runtime 协议），不是 veADK Agent；② 自进化链路为"后台审查 Fork → 提案队列 → 人工审批 → 生效"；③ 目标 Agent 节点框架由用户选择（veADK / Codex / 自定义 / ADK workflow 编排），ADK workflow 组件用真实名 `SequentialAgent`/`ParallelAgent`/`LoopAgent`/`RemoteA2aAgent`/`Supervisor`；④ **Trace 覆盖层数据契约已升级为基于浏览器补读的真实埋点字段**（AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool），节点着色依据 VeADK Span 名映射；日志 10 字段保留为 TLS 日志行数据源。

---

## 1. 节点类型定义（视觉编码：形状 / 颜色 / 图标）

> 颜色为语义建议（设计阶段），最终以设计系统 token 为准。形状用于色盲友好区分。

| 节点类型 | 形状 | 主色语义 | 图标建议 | 说明（来源 00-directory.md） |
|---|---|---|---|---|
| **Agent**（业务智能体） | 圆角矩形 | 蓝（主实体） | 机器人头像 | 被设计的目标 Agent / 子 Agent |
| **Runtime** | 圆柱/部署单元 | 靛蓝 | 服务器 | 托管 Agent 代码的运行实例，`/invoke` 入口 |
| **Skill** | 菱形/方块 | 青 | 拼图块 | 可复用技能单元 |
| **MCP 服务 / MCP 工具集** | 六边形 | 紫 | 插拔接口 | 经网关接入的外部工具能力 |
| **网关 Gateway** | 倒三角/菱形枢纽 | 灰紫 | 门/桥 | 统一入口、MCP 请求计数 |
| **知识库 KnowledgeBase (VikingDB RAG)** | 堆叠书本 | 绿 | 文档/数据库 | 语义检索切片 |
| **记忆库 Memory / Session** | 云/脑形 | 橙 | 记忆节点 | 长期记忆 + 会话状态 |
| **沙箱 Sandbox (工具)** | 立方体/容器 | 绿松石 | 容器 | 代码/浏览器沙箱工具 |
| **模型服务 Model Service** | 星/芯片 | 品红 | 芯片 | 推理、Token 消耗 |
| **函数服务 Function** | 小方块 | 灰蓝 | `ƒ` | 轻量函数计算 |
| **身份与权限 Identity/IAM** | 盾牌 | 深蓝 | 钥匙/盾牌 | 入站/出站授权 |
| **安全围栏 Guardrails** | 盾牌+纹章 | 红 | 栅栏 | 内容安全/攻击拦截 |
| **A2A Registry** | 网状节点 | 青灰 | 网络 | 跨 Agent 注册/发现 |
| **观测 Observability (APMPlus/TLS)** | 眼睛 | 黄 | 眼睛 | 指标/链路/日志采集点 |

**节点尺寸规则**：默认统一大小；Agent / Runtime 略大（视觉锚点）。

### 1.1 Wizard 自身的专用节点（修订新增）

下列节点表达"Wizard 这个产品自身的内部结构"，与上表"用户设计的目标 Agent 拓扑"区分开，建议在图例中单列一组"Wizard 内部"色系：

| Wizard 专用节点 | 标注文案（图上必须显示） | 语义（据 05 核验） |
|---|---|---|
| **Wizard 底座** | `Hermes Agent (AIAgent.run_conversation) + FastAPI Shim (Runtime 协议)` | 底座是 Hermes 原生主循环（模型调用→工具分发→重试/降级→压缩→turn 后钩子），外层薄 FastAPI shim 把 Runtime 协议 `/run`/`/run_sse`/`/invoke`/`/ping` 映射到进程内 `run_conversation(...)`。**不是 veADK Agent，也不是 LlmAgent 子类**。 |
| **自进化 Self-improving** | `后台审查 Fork → 提案队列 → 人工审批 → 生效` | Hermes 自进化能力的落地形态：后台审查产生 fork → 进入提案队列 → **必须人工审批**后方可生效（不自动生效）。`harness_extension` 契约仅 `sidecar_status_payload()` + `close()` 两方法，不是自进化路由契约。 |
| **目标 Agent（用户设计）** | `目标 Agent：框架可选（veADK / Codex / 自定义 / ADK workflow 编排）` | 用户在 Step3 选择的框架落点。选 ADK workflow 编排时，可用组件用**真实 import 名**：`SequentialAgent`、`ParallelAgent`、`LoopAgent`、`RemoteA2aAgent`、`Supervisor`（来源 `veadk/integrations/agentkit/app.py` 实际 import）。图上不得用未核验的虚构组件名。 |

> 上述三类节点在设计时拓扑中的视觉编码建议沿用 §1 的形状/主色，但加"内部"徽标（如小锁/盾牌角标），避免与"用户设计的目标系统组件"混为一谈。

---

## 2. 边类型定义

| 边类型 | 视觉 | 语义 | 举例 |
|---|---|---|---|
| **同步调用（sync call）** | 实线箭头，实色 | 运行时一次同步请求-响应 | Agent → Skill；Agent → 知识库 |
| **异步调用 / 流式（stream/async）** | 实线箭头 + 流动虚线动画点 | 流式/异步返回（SSE） | Runtime → Agent 的 `/invoke` 流式响应 |
| **数据流（data flow）** | 虚线箭头，箭头朝数据方向 | 数据被读取/写入 | 知识库 → Agent（检索结果）；Agent → 记忆库（写入记忆） |
| **配置依赖（config dependency）** | 点线，无箭头或双向 | 不产生运行时调用，仅配置挂载关系 | Agent 挂载 Guardrails；Runtime 关联 MCP |
| **运行时 trace 边（覆盖层叠加）** | 在已有边上叠加**粗高亮 + 数值标签** | 真实发生过的调用 | 调用次数/时延/错误率 |

> 设计时只定义前 4 类；第 5 类由 trace 覆盖层叠加，不参与设计时编辑。

---

## 3. 设计时拓扑 vs 运行时 trace 的视觉区分

这是本图最重要的区分，必须**分层**而非混为一体：

| 维度 | 设计时拓扑（Design-time） | 运行时 trace（Runtime overlay） |
|---|---|---|
| 来源 | 用户在 Step3 拖拽编辑的连接 | APMPlus trace API 真实返回 |
| 默认可见 | 始终可见（下层） | 默认隐藏，由"Trace 覆盖层"开关开启（上层） |
| 节点着色 | 中性组件色（见 §1） | 覆盖：成功=绿描边/光晕，失败=红描边，未命中=灰 |
| 边 | 设计边（§2 前 4 类） | 在边线上叠加数值徽章（次数/时延/错误率） |
| 关系表达 | "我打算这么连" | "实际刚才发生了什么" |
| 无数据时 | 正常显示 | 覆盖层区显示**"无观测数据"占位**，节点保持设计中性色 |

**叠加层状态**：
- 覆盖层关闭：纯设计时视图。
- 覆盖层开启且有 trace：节点/边按真实调用着色；设计了但 trace 未命中的边**变灰**，提示"设计了但本次未触发"。
- 覆盖层开启但无 trace：整层显示占位空状态，不出现任何绿/红。

---

## 4. Trace 覆盖层数据结构

> **⚠️ 核心修正（v1.3，2026-09-18）**：此前版本把聚合 Metrics（Histogram P50/P95、Counter 调用次数）误用于单次 trace 节点/边数据。本节已重写，严格分离单次 trace 与聚合观测。

### 4.0 数据契约来源（三层分离）

| 层 | 来源 | 字段 | 用途 | 验证状态 |
|---|---|---|---|---|
| **层1：观测字段文档** | 浏览器 DOM 读取 AgentKit/VeADK 埋点字段页 | AgentKit 9 个 `gen_ai.*` Span 属性 + 2 个 Metrics；VeADK 4 个 Span 名 + 15 通用 + 23 LLM + 9 Tool 字段 | 定义 span 属性有哪些字段 | ✅ 已验证（browser-gap-results.md 任务1） |
| **层2：平台查询 API** | 火山引擎 API Explorer 核验 | APMPlus GetTraceDetail / ListSpan / ListSession 三个 OpenAPI | 定义如何从 APMPlus 拉取 trace/span 数据 | ✅ 已验证（2026-09-18，见 §4.0.1） |
| **层3：Wizard 归一化 schema** | 设计定义 | 前端 Trace 覆盖层使用的统一数据结构，从层1+层2映射而来 | 前端渲染 | 🔧 设计定义，待 POC |

#### 4.0.1 APMPlus 查询 API 核验摘要

| API | 用途 | 关键参数 | 关键响应 |
|---|---|---|---|
| **GetTraceDetail** | 按 TraceId 查单条 trace 完整 span 树 | `TraceId`、`SuggestTime` | `Trace.SpanList[]`（含 SpanId/ParentSpanId/OperationName/ServiceName/Status/DurationMicroseconds/StartTimeMillisecond/GenAISpanKind/ErrorInfoList/TotalTokens 等） |
| **ListSpan** | 按时间范围查 span 列表（聚合/浏览） | `StartTime`/`EndTime`（秒）、`Filters[]`、`TagFilters[]`、`BusinessCarrier=agentkit_runtime` | `SpanList[]`（同 GetTraceDetail + GenAIInput/GenAIOutput/ContainerId） |
| **ListSession** | 按时间范围查会话列表 | `StartTime`/`EndTime`（毫秒）、`PageNo`/`PageSize`、`BusinessCarrier=agentkit_runtime` | `SessionBriefs[]`（SessionId/TraceIds[]/InputTokens/OutputTokens/TotalTokens） |

- 域名：`https://apmplus-server.cn-beijing.volcengineapi.com`
- 鉴权：AK/SK HMAC-SHA256 签名 V4（通过 volcengine SDK）
- API Version：`2026-01-01`

### 4.1 覆盖层数据结构（单次 trace，严格用 span 数据）

```
TraceOverlay {
  trace_id: string              // OTel 标准 traceparent 承载
  spans: [                      // 来自 APMPlus GetTraceDetail 的 SpanList
    {
      span_id: string           // APMPlus SpanId
      parent_span_id: string    // APMPlus ParentSpanId（OTel 标准父子关系）
      name: string               // = OperationName（VeADK Span 名：
                                 //   invocation / invoke_agent {agent.name} /
                                 //   call_llm / execute_tool {tool.name}）
      start_time_ms: number      // APMPlus StartTimeMillisecond
      duration_ms: number        // ⚠️ = DurationMicroseconds / 1000
                                 //    由 span 起止差计算，不是 Histogram P50/P95！
      status: {
        code: "OK" | "ERROR"    // APMPlus Status 字段；ErrorInfoList 非空=ERROR
        error_info?: {
          error_kind: string     // ErrorInfoList[].ErrorKind
          error_message: string
          error_stack: string
        }
      }
      genai_span_kind: string   // APMPlus GenAISpanKind（llm / tool / workflow）
      service_name: string      // APMPlus ServiceName
      operation_name: string     // APMPlus OperationName
      call_service_name: string  // APMPlus CallServiceName（被调服务）
      call_service_type: string
      call_resource_name: string
      attributes: {
        // —— AgentKit 侧（9 个 gen_ai.* Span 属性）——
        gen_ai.system: "agentkit"
        gen_ai.func_name: string
        gen_ai.user.id: string
        gen_ai.session.id: string
        gen_ai.span.kind: string
        gen_ai.operation.name: string
        gen_ai.operation.type: string
        gen_ai.input: string              // 受内容采集开关控制
        gen_ai.output: string             // 受内容采集开关控制

        // —— VeADK 通用类（15 个，关键字段）——
        gen_ai.agent.name: string
        gen_ai.app.name: string
        cozeloop.report.source: "veadk"

        // —— VeADK LLM 类（call_llm Span，关键字段）——
        // gen_ai.request.model / temperature / top_p / max_tokens
        // gen_ai.response.model / stop_reason / finish_reason
        // gen_ai.usage.input_tokens / output_tokens / total_tokens
        // gen_ai.usage.cache_creation_input_tokens / cache_read_input_tokens

        // —— VeADK Tool 类（execute_tool Span，关键字段）——
        // gen_ai.tool.name / tool.input / tool.output

        // —— APMPlus 额外 AI 字段 ——
        genai_input: string               // GenAIInput
        genai_output: string              // GenAIOutput
        total_tokens: number
        output_tokens: number
        cache_read_tokens: number
      }
    }
  ]
  summary: {
    span_nums: number           // APMPlus Summary.SpanNums
    service_nums: number        // APMPlus Summary.ServiceNums
    error_span_ids: [string]    // APMPlus Summary.ErrorSpanIds
  }
  logs: [                        // 日志层：TLS 日志行（10 字段）
    {
      service: string
      message: string
      log_level: enum
      trace_id: string
      attribute: object
      resource: object
      hostname: string
      file_name: string
      file_line: string
      source: string
    }
  ]
}
```

#### 4.1.1 聚合观测面板（独立，不归属单次调用）

```
AggregateMetricsPanel {
  time_window: "1h" | "6h" | "24h" | "7d"
  p50_latency_ms: number       // 来自 agentkit_runtime_operation_latency Histogram（时间窗聚合）
  p95_latency_ms: number       // 同上
  qps: number                  // 来自 _count Counter / 时间窗
  error_rate: number           // error_type 非空计数 / 总计数（时间窗聚合）
  total_calls: number          // _count Counter 聚合
  note: "近 N 小时聚合统计，不关联到任何单次调用"  // 明确标注
}
```

> **⚠️ 铁律**：P50/P95/QPS/错误率趋势**永远不回写到单次 trace 覆盖层的节点/边徽章**。它们只出现在独立的聚合面板中。

### 4.2 如何映射到设计时节点

#### 4.2.1 单次 trace 的节点着色与数据计算

**节点是否被调用**：trace 中有对应 span → 已调用；无 span → 无数据（≠未调用）。

**节点耗时**：单个 span 的 `duration_ms`（= `DurationMicroseconds / 1000`，span 起止差计算）。**不是 Histogram P50/P95**。

**节点是否失败**：span `Status=ERROR` 或 `ErrorInfoList` 非空 → 标红。**不是 error_type 维度聚合计数**。

**节点调用次数**：单次 trace 内该组件对应的 span 出现次数。按操作语义计数：`execute_tool {tool.name}` span 出现 3 次 = 该工具被调用 3 次（含重试）。**不是 `_count` Counter**。

#### 4.2.2 边着色与数据计算

**边是否发生**：依据 span `parent_span_id` 父子关系，在单次 trace 中有 A→B 父子 span 链 → 边已发生。

**边耗时**：子 span 的 `duration_ms`（span 起止差）。

**边调用次数**：单次 trace 内 A→B 父子链出现次数，按 span 树遍历计数，含重试。**不是 Counter**。

**边错误率**：单次 trace 内该父子链中 ERROR span 占比（如 3 次调用 1 次错 = 33%）。**不是跨调用聚合**。

#### 4.2.3 组件调用证据映射（证据字段 + 资源 ID）

| 架构图节点类型 | 证据字段组合（映射到设计时 component_id） | 碰撞/缺失处理 |
|---|---|---|
| **Agent 节点** | `service.name` + `operation.name=invoke_agent` + `gen_ai.agent.name` | `gen_ai.agent.name` 精确匹配设计时 component_id；匹配不上标 `unknown` |
| **模型服务节点** | `operation.name=call_llm` + `gen_ai.request.model` | `gen_ai.request.model` 标识模型；同一模型被多 Agent 调用时靠父子 span 链归属 |
| **工具/Skill 节点** | `operation.name=execute_tool` + `gen_ai.tool.name` + `service.name` | `gen_ai.tool.name` 匹配 component_id；多 Skill 同名时靠 `service.name`+资源 ID 消歧；匹配不上标 `unknown` |
| **MCP 服务节点** | `call_service_type` + `call_service_name` + `call_resource_name` | APMPlus 返回的 CallServiceName/CallResourceName 对应 MCP 服务/工具 |
| **Runtime 入口** | `operation.name=invocation` + `service.name` | 根 span |

**observed-unmapped 节点**：trace 中发现但设计图中没有的节点（span 的 `operation.name`/`gen_ai.tool.name` 找不到对应 component_id），在覆盖层上以「观测到但未在设计中」单独列出，**不强行塞进设计图，也不丢弃**。

**Skill 加载 vs 执行区分**：
- **Skill 被加载（mounted）**：设计时拓扑中有连接关系，trace 中无对应 `execute_tool` span → 显示「已挂载，本次未执行」。
- **Skill 被执行（executed）**：trace 中有对应 `execute_tool {tool.name}` span → 显示「已执行」，附耗时/错误状态。
- 两者**分开展示**。

#### 4.2.4 点击节点抽屉（调用详情面板）

- **LLM 调用**：`gen_ai.usage.input_tokens`/`output_tokens`/`total_tokens`、`cache_*_tokens`、`gen_ai.request.model`/`temperature`/`top_p`；
- **Agent 调用**：`gen_ai.operation.name`/`operation.type`、`gen_ai.func_name`、`gen_ai.input`/`output`（受内容采集开关控制）；
- **工具调用**：`gen_ai.tool.name`、`gen_ai.tool.input`/`output`；
- **时延与状态**：`duration_ms`（span 起止差）、`status.code`、`error_info`；
- **日志行**：该服务本次全部 TLS 日志（`message`/`log_level`/`file_name:file_line`/`hostname`）。

### 4.3 对齐失败与降级处理

- 若观测返回的 Span `gen_ai.agent.name`/`gen_ai.tool.name` 在设计时拓扑中**找不到对应节点**：在覆盖层上以「observed-unmapped（观测到但未在设计中）」单独列出，**不强行塞进设计图，也不丢弃**。
- 若 `trace_content` 开关关闭（`OBSERVABILITY_OPENTELEMETRY_TRACE_CONTENT=false`）：`gen_ai.input`/`output`/`prompt`/`completion` 等内容字段为空，抽屉对应位置显示"内容采集已关闭"，**不得**用空字符串编造。
- 观测服务未开启（开启/关闭观测需重新发布才生效）：覆盖层开关置灰，显示"观测服务未配置"。
- **trace 缺失 ≠ 未调用**：观测未开启或链路异步落库延迟时，显示"无观测数据"，节点保持设计中性色，**不代表目标 Agent 未被调用**。
- **单次 trace 绝不使用聚合 Metrics**（P50/P95/QPS）。聚合指标只出现在独立的「近 N 小时聚合」面板中。

---

## 5. 布局算法建议

| 方案 | 适用 | 说明 |
|---|---|---|
| **分层布局（Layered / DAG，默认）** | 设计时主视图 | 按调用层级自上而下：Runtime/Agent → 工具层（Skill/沙箱）→ 资源层（知识库/记忆/MCP）→ 外围（网关/身份/围栏/观测）。引导式开发下层次清晰、可读性最好。 |
| **力导向（Force-directed）** | 关系较松散、需要自由探索 | 用户点"自动布局"时可选；避免层级混乱，仅作辅助。 |
| **手动布局（Manual，用户最终掌控）** | 用户调整 | 所有自动布局结果都可手动拖拽固定；位置持久化保存。 |

建议默认分层 + 允许手动覆盖；trace 覆盖层开启时**不重新布局**，只在原节点上着色，避免用户视觉锚点漂移。

---

## 6. 交互细节（与 01 呼应）

- **缩放**：滚轮缩放（以光标为中心）；按钮缩放至 100% / 适应屏幕。
- **平移**：空白处拖拽平移；触屏单指平移、双指缩放。
- **点击节点**：右侧抽屉滑出，显示配置详情 + 对应 Skill 链接 +（有 trace 时）本次调用详情。
- **悬停节点**：tooltip 显示组件名、类型、（有 trace 时）本次时延与成功率。
- **框选**：空白拖拽框选多节点，支持批量删除/对齐。

---

## 7. 证据引用

- Wizard 底座（Hermes `AIAgent.run_conversation` + FastAPI shim）、Runtime 协议端点、自进化链路、ADK 编排组件真实 import 名：`docs/hermes-veadk/05-hermes-as-base-verification.md`（§1b、§3c、§4、§5c、§7）。
- 节点对应的组件：`docs/volcengine-official/00-directory.md`。
- 观测开启方式（需重新发布生效）、**已核验 10 个日志字段表**：`docs/volcengine-official/shard4-results.md`（§3、§41、附录A）。
- **埋点字段与 Metrics（浏览器 DOM 补读，2026-09-18）**：`docs/volcengine-official/browser-gap-results.md`（任务1：AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool 字段）。
- **APMPlus trace 查询 API（火山引擎 API Explorer 核验，2026-09-18）**：GetTraceDetail（按 TraceId 查 span 树）、ListSpan（按时间范围+过滤条件）、ListSession（会话级 token 统计）。域名 `apmplus-server.cn-beijing.volcengineapi.com`，鉴权 AK/SK HMAC-SHA256 签名 V4，API Version `2026-01-01`，`BusinessCarrier=agentkit_runtime`。来源：火山引擎 API Explorer 同站核验。
- trace 字段语义方向、同一条 trace、Follow gen.ai 标准：`docs/lark-supplements/doc07.md`。

---

## 修订记录

| 日期 | 版本 | 修订内容 |
|---|---|---|
| 2026-09-18 | v1.3 | **观测数据契约重大修正**：① §4 整节重写——严格分离单次 trace 与聚合观测：单次 trace 的 `duration_ms` 由 span `DurationMicroseconds/1000`（起止差计算）得出，**不再使用 Histogram P50/P95**；错误来自 span `Status`/`ErrorInfoList`，**不再使用 error_type 维度聚合计数**；调用次数按操作语义计数（span 出现次数），**不再使用 `_count` Counter**；P50/P95/QPS 等聚合指标独立为「聚合观测面板」（§4.1.1），**绝不回写到单次 trace 覆盖层**；② APMPlus 查询 API 已通过火山引擎 API Explorer 核验：GetTraceDetail/ListSpan/ListSession，域名/鉴权/参数/响应均已确认（§4.0.1）；③ 组件调用证据映射改为用 `service.name`+`operation.name`+`gen_ai.agent.name`/`gen_ai.tool.name`+资源 ID 做映射，碰撞标 `unknown`，trace 中未设计节点标 `observed-unmapped`；④ Skill mounted vs executed 分开展示；⑤ §7 证据引用更新。 |
| 2026-09-18 | v1.2 | 浏览器 DOM 补读成功后更新 Trace 覆盖层数据契约：① §4 整节重写——覆盖层数据结构从"仅 10 个日志字段 + trace_id，span 字段为设计假设"升级为**基于真实埋点字段的契约**（AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool）；② 节点着色依据从"log_level=ERROR 为唯一信号"升级为 VeADK Span 名（`invocation`/`invoke_agent {name}`/`call_llm`/`execute_tool {name}`）映射 + `status.code`/`error_type` 维度；③ 边徽章从"暂不做"升级为可依据 `agentkit_runtime_operation_latency_count`（调用次数）+ Histogram（P50/P95 时延）+ `error_type`（错误率）叠加；④ 调用详情面板字段定义：`gen_ai.usage.*` token 统计、`gen_ai.operation.name`/`operation.type`、`duration_ms`、`status`；⑤ 保留"trace 缺失 ≠ 未调用"和"无观测数据"占位；新增 `trace_content` 开关降级说明；⑥ §7 证据引用更新。 |
| 2026-09-18 | v1.1 | 依据 Hermes 核验文档与 shard4 观测字段核验纠正：① 头部证据与基线声明更新；② §1 新增"Wizard 专用节点"小节——底座标注为 `Hermes Agent (AIAgent.run_conversation) + FastAPI Shim (Runtime 协议)`、自进化标注为"后台审查 Fork → 提案队列 → 人工审批 → 生效"、目标 Agent 节点标注框架可选（veADK/Codex/自定义/ADK workflow 编排），ADK workflow 组件统一用真实 import 名 `SequentialAgent`/`ParallelAgent`/`LoopAgent`/`RemoteA2aAgent`/`Supervisor`；③ §4 整节重写：覆盖层数据结构从"完整 span 对象"收紧为"已核验 10 个日志字段 + trace_id"，span 级字段（span_id 父子、duration_ms、status、gen.ai attributes、call_count、P95/错误率徽章）全部标注为**待 APMPlus/VeADK 文档站核验的设计假设**，核验前一律显示 "—"；④ 节点着色规则改为以 `service`+`log_level=ERROR` 为当前唯一已核验信号，边徽章暂不做；明确"无日志 ≠ 未调用"；⑤ §7 证据引用更新。 |
| （初始版） | v1.0 | 首版设计规格。 |
