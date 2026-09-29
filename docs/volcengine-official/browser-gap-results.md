# 浏览器补读结果（browser-gap-results.md）

> 生成时间：2026-09-18
> 方法：使用浏览器 DOM 读取（bu plane），不使用 web.fetch。
> 结论：上一轮报告的"用户访问阻塞/重定向失败"大多是 **web.fetch 无法渲染 JS 动态页面** 导致的误判，公开文档在浏览器中均可正常读取，**未遇到任何登录/权限阻塞**。

---

## 任务1：[PRODUCT] / [BASE-ADK] 观测埋点字段

### 1.1 导航页（埋点字段与指标说明）

- **URL**：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Trackingfieldsandmetricsdescription?lang=zh
- **标题**：埋点字段与指标说明--[PRODUCT]-火山引擎
- **读取状态**：✅ 成功（纯导航概述页，本身不含字段表）
- **页面内容**：
  - 分为两套埋点方案：
    - **AI应用监控**（[PRODUCT]）：在 [PRODUCT] SDK 内部接入 OpenTelemetry，涵盖分布式追踪 Tracing + 指标监控 Metrics。
    - **[BASE-ADK]**：在 [BASE-ADK] SDK 内部接入 OpenTelemetry，涵盖通用类 / LLM 类 / Tool 类三大模块。
- **两个子页面真实链接（从正文内联 `<a>` 提取，非 sidebar）**：
  - [PRODUCT] 埋点字段与指标说明 → `https://<INTERNAL_HOST>.com/docs/86845/1963487`
  - [BASE-ADK] 埋点与字段说明 → `https://volcengine.github.io/[BASE-ADK]-python/cn/docs/framework/span-attributes/`

### 1.2 子页A：[PRODUCT] 埋点字段与指标说明

- **真实 URL**（浏览器打开后跳转）：`https://<INTERNAL_HOST>.com/docs/ObservabilityPlatform/[PRODUCT]trackingfieldsandmetricsdescription?lang=zh`
- **标题**：[PRODUCT] 埋点字段与指标说明--全栈可观测平台-火山引擎
- **最近更新**：2026.01.27
- **读取状态**：✅ 成功

#### Span Attributes 表（每次调用 [PRODUCT] Runtime 产生一条 Span）

| Attribute | 类型 | 描述 | 示例 |
|---|---|---|---|
| `gen_ai.system` | string | 大模型系统标识，固定为 `[PRODUCT]` | `"[PRODUCT]"` |
| `gen_ai.func_name` | string | 具体调用的函数 | `"run"` |
| `gen_ai.user.id` | string | 调用用户 ID | `"user_#a3f9b2"` |
| `gen_ai.session.id` | string | 调用会话 ID | `a2b1ee10-22df-42d9-8daa-986a609b1686` |
| `gen_ai.span.kind` | string | Gen AI 埋点 Span 类型，如 `workflow`/`llm` | `"workflow"` |
| `gen_ai.operation.name` | string | Runtime 执行的操作，如 `invoke_agent`、`tool` | `"invoke_agent"` |
| `gen_ai.operation.type` | string | 操作类型，如 `agent`、`a2a_agent` | `"agent"` |
| `gen_ai.input` | string | 调用的输入 | `{"prompt": "你好"}` |
| `gen_ai.output` | string | 调用的返回 | `"你好！很高兴为你提供帮助..."` |

#### Metrics 指标表

| Metric | 类型 | 说明 | 指标维度 |
|---|---|---|---|
| `[PRODUCT]_runtime_operation_latency` | Histogram | 调用耗时 | `error_type`（非空=失败）、`gen_ai_operation_name`、`gen_ai_operation_type` |
| `[PRODUCT]_runtime_operation_latency_count` | Counter | 调用次数 | 同上三个维度 |

> 注：该站 Span 命名遵循 OpenTelemetry GenAI 语义约定；**未单独列出 trace_id / latency / token_usage 字段**（trace_id 由 OTel 标准 traceparent 承载，latency 走 Metrics Histogram，token_usage 在此 [PRODUCT] 侧页面未出现——token 用量在 [BASE-ADK] 侧 LLM 类字段中）。

### 1.3 子页B：[BASE-ADK] 埋点与字段说明（span-attributes）

- **URL**：`https://volcengine.github.io/[BASE-ADK]-python/cn/docs/framework/span-attributes/`
- **标题**：埋点字段说明（Volcengine ADK）
- **读取状态**：✅ 成功

#### 埋点时机（与 Google ADK 对齐）

| 时机 | 打点函数 | Span 名称 |
|---|---|---|
| 调用 Agent | Runner 的 `_run_with_trace` | `invocation` |
| 运行 Agent | Agent 的 `run_async` | `invoke_agent {agent.name}` |
| 调用模型 | BaseLlmFlow 的 `_call_llm_with_tracing` | `call_llm` |
| 调用工具 | BaseLlmFlow 的 `_execute_single_function_call_async` | `execute_tool {tool.name}` |

#### 内容采集开关

- `observability.opentelemetry.trace_content` 或环境变量 `OBSERVABILITY_OPENTELEMETRY_TRACE_CONTENT`。
- 设为 `false` 后，标记"受内容采集开关控制"的字段（输入/输出内容）不写入 Span；普通链路、模型参数、Token 用量、工具名等仍保留。

#### 通用类字段（所有 Span）

| # | 字段名 | 含义 | 注释 |
|---|---|---|---|
| 1 | `gen_ai.system` | 生成式 AI 系统提供方 | 缺省 `<unknown_model_provider>` |
| 2 | `gen_ai.system.version` | [BASE-ADK] 框架版本号 | 固定 `[BASE-ADK].version.VERSION` |
| 3 | `gen_ai.agent.name` | Agent 名称 | 缺省 `<unknown_agent_name>` |
| 4 | `openinference.instrumentation.[BASE-ADK]` | OpenInference 标准化埋点版本 | 固定 `[BASE-ADK].version.VERSION` |
| 5 | `gen_ai.app.name` | app_name | 缺省 `<unknown_app_name>` |
| 6 | `gen_ai.user.id` | user_id | 缺省 `<unknown_user_id>` |
| 7 | `gen_ai.session.id` | session_id | 缺省 `<unknown_session_id>` |
| 8 | `agent_name` | Agent 名称（CozeLoop） | 同 `gen_ai.agent.name` |
| 9 | `agent.name` | Agent 名称（TLS 平台） | 同 `gen_ai.agent.name` |
| 10 | `app_name` | app_name（CozeLoop） | 同 `gen_ai.app.name` |
| 11 | `app.name` | app_name（TLS） | 同 `gen_ai.app.name` |
| 12 | `user.id` | user_id（CozeLoop/TLS） | 同 `gen_ai.user.id` |
| 13 | `session.id` | session_id（CozeLoop/TLS） | 同 `gen_ai.session.id` |
| 14 | `cozeloop.report.source` | Trace 数据来源 | 固定 `[BASE-ADK]` |
| 15 | `cozeloop.call_type` | CozeLoop 调用类型 | 缺省 `None` |

#### LLM 类字段（call_llm Span）

| # | 字段名 | 含义 | 注释 |
|---|---|---|---|
| 1 | `gen_ai.request.model` | 模型名称 | 从 `params.llm_request.model`；缺省 `<unknown_model_name>` |
| 2 | `gen_ai.request.type` | LLM 请求类型 | 固定 `chat` |
| 3 | `gen_ai.request.max_tokens` | 最大生成 token 数 | 从 `params.llm_request.config.max_output_tokens` |
| 4 | `gen_ai.request.temperature` | 采样温度 | 从 `params.llm_request.config.temperature` |
| 5 | `gen_ai.request.top_p` | top-p 参数 | 从 `params.llm_request.config.top_p` |
| 6 | `gen_ai.request.functions` | 函数/工具元数据 | 提取 name/description/parameters（CozeLoop） |
| 7 | `gen_ai.response.model` | 实际响应模型 | 与请求一致表示正常 |
| 8 | `gen_ai.response.stop_reason` | 停止原因 | 当前占位符 `<no_stop_reason_provided>` |
| 9 | `gen_ai.response.finish_reason` | 完成原因 | 当前占位符 `<no_finish_reason_provided>` |
| 10 | `gen_ai.is_streaming` | 是否流式 | 返回 `None` |
| 11 | `gen_ai.operation.name` | 操作名称 | 固定 `chat` |
| 12 | `gen_ai.span.kind` | Span 类型 | 固定 `llm` |
| 13 | `gen_ai.prompt` | 请求输入结构化 | 受内容采集开关控制 |
| 14 | `gen_ai.completion` | 响应输出结构化 | 受内容采集开关控制 |
| 15 | `gen_ai.usage.input_tokens` | 输入 token 数 | `params.llm_response.usage_metadata.prompt_token_count` |
| 16 | `gen_ai.usage.output_tokens` | 输出 token 数 | `...candidates_token_count` |
| 17 | `gen_ai.usage.total_tokens` | 总 token 数 | `...total_token_count` |
| 18 | `gen_ai.usage.cache_creation_input_tokens` | 缓存创建 token | `...cached_content_token_count` |
| 19 | `gen_ai.usage.cache_read_input_tokens` | 缓存读取 token | （同来源） |
| 20 | `gen_ai.messages` | 完整对话消息事件 | 受内容采集开关控制 |
| 21 | `gen_ai.choice` | 模型选择事件 | 受内容采集开关控制 |
| 22 | `input.value` | 完整 LLM 请求体 | 调试用，序列化请求对象 |
| 23 | `output.value` | 完整 LLM 响应体 | 调试用，序列化响应对象 |

#### Tool 类字段（tool_call Span）

| # | 字段名 | 含义 | 注释 |
|---|---|---|---|
| 1 | `gen_ai.operation.name` | 操作名称 | 固定 `execute_tool` |
| 2 | `gen_ai.tool.name` | 工具名称 | 从 `params.tool.name`；缺省 `<unknown_tool_name>`（TLS） |
| 3 | `gen_ai.tool.input` | 工具输入 | JSON 含 name/description/parameters（TLS）；受开关控制 |
| 4 | `gen_ai.tool.output` | 工具输出 | JSON 含 id/name/response（TLS）；受开关控制 |
| 5 | `cozeloop.input` | 工具输入（CozeLoop） | 同 `gen_ai.tool.input`；受开关控制 |
| 6 | `cozeloop.output` | 工具输出（CozeLoop） | 同 `gen_ai.tool.output`；受开关控制 |
| 7 | `gen_ai.span.kind` | Span 类型 | 固定 `tool`（APMPlus） |
| 8 | `gen_ai.input` | 工具输入（APMPlus） | 同 `gen_ai.tool.input`；受开关控制 |
| 9 | `gen_ai.output` | 工具输出（APMPlus） | 同 `gen_ai.tool.output`；受开关控制 |

---

## 任务2：ADK（adk.dev）Workflow 子页面

> 站点为 Google ADK 官方文档。所有子页均公开可读，无登录阻塞。

### 2.1 Workflows 总览

- **URL**：`https://adk.dev/workflows/`
- **标题**：Workflows: multi-agent, multi-node applications - Agent Development Kit (ADK)
- **读取状态**：✅ 成功
- **要点**：ADK 支持把多个 Agent 和可执行节点组合成 workflow，提供可预测性、可靠性、结构化。三种编排方式：Graph-based（声明式节点+边路由）、Dynamic（代码内循环/分支/递归）、Prebuilt template（Sequential/Parallel/Loop 高阶积木）。

### 2.2 Graph-based Workflows

- **URL**：`https://adk.dev/graphs/`
- **支持版本**：Python v2.0.0 / TypeScript v2.0.0 / Go v2.0.0
- **读取状态**：✅ 成功
- **核心 API**：
  - `from google.adk import Agent, Workflow, Event`
  - `Workflow(name=..., edges=[("START", node_a, node_b, ...)])` 链式顺序边。
  - 节点类型可混合：AI Agent、Tool、自定义函数（普通 Python 函数，入参 `node_input`）、甚至子 workflow。
  - 路由函数返回 `Event(...)`，可携带 `routes` 用于条件路由。
  - Go 等价物：`workflow.NewFunctionNode` / `workflow.NewAgentNode`、`workflow.Chain` / `workflow.Concat` + `[]workflow.Edge`、`workflowagent.New` 包装；条件路由 `workflow.StringRoute/IntRoute/BoolRoute` 匹配 `event.Routes`；fan-in 用 `workflow.NewJoinNode`。
- **代码骨架**：
  ```python
  root_agent = Workflow(
      name="root_agent",
      edges=[("START", city_generator_agent, lookup_time_function,
               city_report_agent, completed_message_function)]
  )
  ```
- **限制**：与部分第三方集成不兼容；Go 为 graph API 等价物。

### 2.3 Dynamic Workflows

- **URL**：`https://adk.dev/graphs/dynamic/`
- **支持版本**：Python v2.0.0 / TypeScript v2.0.0 / Go v2.0.0
- **读取状态**：✅ 成功
- **核心 API**：
  - 装饰器 `@node`（Python）或构造函数（Go）。
  - 在 `async def xxx(ctx: Context, node_input)` 中用 `await ctx.run_node(node, ...)` 调用子节点，**返回值即子节点输出**（类型化，无需手动读写 session state）。
  - `@node(rerun_on_resume=True)` 控制恢复时是否重跑；**自动 checkpointing**——成功的子节点恢复时自动跳过。
  - 可在 workflow 内写 while/for 循环、if/else、递归。
- **代码骨架**：
  ```python
  @node(name="hello_node")
  def my_node(node_input: Any):
      return "Hello World"

  @node(rerun_on_resume=True)
  async def my_workflow(ctx: Context, node_input: str) -> str:
      result = await ctx.run_node(my_node, node_input="hello")
      return result

  root_agent = Workflow(name="root_agent", edges=[("START", my_workflow)])
  ```
- **数据传递**：`ctx.run_node` 直接返回子节点输出；也可用 Pydantic `BaseModel` 定义 input/output schema（如 `CityTime`）。

### 2.4 Collaborative Workflows（协作 / Supervisor 等价）

- **URL**：`https://adk.dev/workflows/collaboration/`
- **支持版本**：Python v2.0.0 / Go v2.0.0
- **读取状态**：✅ 成功
- **核心概念**：一个 **coordinator（协调者，即 Supervisor 角色）** LlmAgent 通过 `sub_agents=[...]** 委派任务给子 Agent；子 Agent 完成后自动返回协调者。协调者会**自动注入以子 Agent 命名的委派工具**。
- **子 Agent 三种 mode（这是该页核心配置）**：

| Topic \ Mode | chat（默认） | task | single_turn |
|---|---|---|---|
| Human in the Loop | 完全交互 | 仅澄清提问 | 禁止 |
| 用户交互 | 自由对话 | 按需提问 | 无 |
| 控制流 | 人工 handoff | 任务完成自动返回 | 任务后立即返回 |
| 并行执行 | 不支持 | 不支持 | 可多任务并行 |
| 返回父级 | 手动（transfer） | 自动（`finish_task`） | 自动（带结果） |

- **代码骨架**：
  ```python
  weather_agent = Agent(name="weather_checker", mode="single_turn",
                        tools=[get_weather, user_info, geocode_address])
  flight_agent = Agent(name="flight_booker", mode="task",
                       input_schema=FlightInput, output_schema=FlightResult,
                       tools=[search_flights, book_flight])
  root = Agent(name="travel_planner",        # coordinator = Supervisor
               sub_agents=[weather_agent, flight_agent])
  ```
- **传输行为**：作为 workflow graph node 时完成后自动推进下一节点；作为 LlmAgent transfer 目标时，task agent 跑到 `finish_task` 自动返回发起者。
- **上下文隔离**：task/single_turn agent 各自在独立 session 分支，并行时互不可见，全部完成后父 Agent 汇总结果。
- **已知限制**：task mode agent 必须是叶子节点，不能有 sub_agents；graph workflow 中 task 模式在 Python v2.0.0 暂时禁用（后续恢复）。

### 2.5 Template Workflows（预置模板）

#### 2.5.1 SequentialAgent（顺序）

- **URL**：`https://adk.dev/agents/workflow-agents/sequential-agents/`
- **支持**：Python v0.1.0 / TS v0.2.0 / Go v0.1.0 / Java v0.2.0
- **读取状态**：✅ 成功
- **核心**：按列表顺序依次执行 `run_async`；确定性，不受 AI 模型控制。
- **共享上下文**：向每个子 Agent 传递**同一个 InvocationContext**，共享 session state（含 `temp:` 命名空间），便于同轮内传数据。
- **代码**：`SequentialAgent(name=..., sub_agents=[code_writer, code_reviewer, code_refactorer])`
- **子 Agent 常用参数**：`output_key="refactored_code"`（把输出写回 state 的指定 key）。

#### 2.5.2 LoopAgent（循环）

- **URL**：`https://adk.dev/agents/workflow-agents/loop-agents/`
- **支持**：同上
- **读取状态**：✅ 成功
- **核心参数 `max_iterations`**：
  ```python
  refinement_loop = LoopAgent(
      name="RefinementLoop",
      sub_agents=[critic_agent_in_loop, refiner_agent_in_loop],
      max_iterations=5   # 限制最大循环次数
  )
  ```
- **终止机制（关键）**：LoopAgent 自身**不会判断何时停止**，必须自己实现：
  1. `max_iterations` 硬上限；
  2. 子 Agent 主动升级信号——定义工具，函数内设置 `tool_context.actions.escalate = True`（并通常 `skip_summarization = True`），例如：
     ```python
     def exit_loop(tool_context: ToolContext):
         tool_context.actions.escalate = True
         tool_context.actions.skip_summarization = True
         return {}
     ```
- **执行顺序**：按 `sub_agents` 列表依次执行一轮；critic 先、refiner 后。

#### 2.5.3 ParallelAgent（并行）

- **URL**：`https://adk.dev/agents/workflow-agents/parallel-agents/`
- **支持**：同上
- **读取状态**：✅ 成功
- **核心**：并发启动每个子 Agent 的 `run_async()`；各自独立分支，**执行期间不自动共享对话历史/state**；结果收集顺序不确定。
- **通信方式**：需显式实现——共享 InvocationContext（注意并发锁防 race），或用 `output_key` 把结果写入 state，再由后续合并 Agent（通常用 SequentialAgent 把 ParallelAgent 放在前面）读取。
- **代码**：
  ```python
  gather = ParallelAgent(name="ConcurrentFetch",
                         sub_agents=[fetch_api1, fetch_api2])
  overall = SequentialAgent(name="FetchAndSynthesize",
                            sub_agents=[gather, synthesizer])
  ```

### 2.6 Agent Routing（路由，实验性）

- **URL**：`https://adk.dev/agents/routing/`
- **支持**：TypeScript v1.0.0（Experimental）
- **读取状态**：✅ 成功
- **核心类**：`RoutedAgent` / `RoutedLlm`，共享同一路由工具。
- **router 函数签名（TS）**：
  ```typescript
  type AgentRouter = (
    agents: Readonly<Record<string, BaseAgent>>,
    context: InvocationContext,
    errorContext?: { failedKeys: ReadonlySet<string>; lastError: unknown },
  ) => Promise<string | undefined> | string | undefined;
  ```
  返回要运行的 agent key（`agents` 也可传数组，用 agent.name 作 key）。
- **Failover 行为**：首次无 errorContext；若所选 agent 在产出任何事件前抛错，带 `failedKeys`/`lastError` 再次调用；已失败 key 不能再选；返回 `undefined` 则停止并抛出最后错误。
- **代码**：
  ```typescript
  const routedAgent = new RoutedAgent({
    name: 'my_routed_agent',
    agents: { basic: basicAgent, planning: planningAgent },
    router: () => (planningMode ? 'planning' : 'basic'),
  });
  ```
  router 可 async，内部可调轻量分类模型做按复杂度自动路由。

### 2.7 Workflow Patterns（模式总览，含 Supervisor 等价）

- **URL**：`https://adk.dev/workflows/patterns/`
- **读取状态**：✅ 成功
- **Coordinator and dispatcher（= Supervisor 模式）**：中央 LlmAgent 作 Coordinator，`sub_agents=[billing_agent, support_agent]`，靠 LLM-Driven Delegation（`transfer_to_agent(agent_name='Billing')`）或 AgentTool 显式委派。
- **其他模式**：Sequential pipeline、Parallel fan-out + synthesize、Hierarchical task decomposition（多级树状委派）。

### 2.8 关于 RemoteA2aAgent

- 在上述 workflows 各子页中**未出现 `RemoteA2aAgent`**。它属于 A2A 协议消费侧（A2A Quickstart Consuming），不在 workflows 章节。如需其参数，应从 `https://adk.dev/a2a/` 的 Consuming 子页读取（本次任务范围为 workflows，未展开）。

---

## 任务3：核对 3 个"重定向失败"页的真实 URL

> 上一轮把这 3 页判为"持续重定向失败/仍未获取"。用浏览器 DOM 核对后结论：**URL 全部正确，页面在浏览器中完整可读**。失败原因是 web.fetch 对 JS 动态渲染页（或带 `?lang=zh` 的文档站）抓取时落到了落地页/发布记录页，**并非 URL 猜错，也非权限阻塞**。

### 3.1 GetSessionStore - 查询会话资源详情

- **核对 URL**：`https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSessionStore-Queriessessionresourcedetails?lang=zh`（与上一轮相同，未猜错）
- **标题**：GetSessionStore - 查询会话资源详情--[PRODUCT]-火山引擎
- **读取状态**：✅ 浏览器完整读取成功
- **提取要点**：
  - 请求参数：`Action=GetSessionStore`、`Version=2025-10-30`、`SessionStoreId`（必选，示例 `<RESOURCE_ID>****`）。
  - 返回参数：
    - `AssociatedAgents[]`（关联智能体：`Id` 运行时ID、`Name`、`UpdateTime`）
    - `CreateTime` / `UpdateTime`（RFC3339）
    - `DatabaseConfiguration`（`AccountName`、`Database`）
    - `EndpointConfiguration`（`EndpointId`、`PrivateEndpoint`、`PublicEndpoint`）
    - `InstanceId`（RDS_MYSQL / RDS_PG）
    - `Description`、`Managed(bool)`、`Name`、`ProjectName`
    - `ProviderType`：`RDS_MYSQL`（云数据库MySQL）/ `RDS_PG`（PostgreSQL）
    - `SessionStoreId`、`Trn`、`VpcId`
    - **`Status` 枚举**：`Creating` / `CreateFailed` / `Ready` / `Deleting` / `DeleteFailed` / `Deleted` / `Error`
  - 请求示例：`POST https://[PRODUCT].cn-beijing.volcengineapi.com?Action=GetSessionStore&Version=2025-10-30`，body `{"SessionStoreId":"ss-..."}`
  - 错误码：`400 MissingParameter.SessionStoreId`。

### 3.2 A2A 智能体 JSON 文件示例

- **核对 URL**：`https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SampleA2AagentJSONfile?lang=zh`
- **标题**：A2A 智能体 JSON 文件示例--[PRODUCT]-火山引擎（位于"附录"）
- **读取状态**：✅ 浏览器完整读取成功
- **提取要点**：
  - 示例按 **A2A 协议 0.3.0** 编写。
  - 完整 JSON 字段：`capabilities.streaming`、`defaultInputModes`、`defaultOutputModes`、`description`、`name`、`preferredTransport`（JSONRPC/GRPC/HTTP+JSON）、`protocolVersion`、`provider{organization,url}`、`security[]`、`securitySchemes{apiKeyAuth:{type,in,name,description}}`、`skills[]{id,name,tags,description}`、`url`、`version`。
  - 必填：`name`、`description`、`version`、`url`、`preferredTransport`、`protocolVersion`、`capabilities`、`skills`（至少1个）、`defaultInputModes`、`defaultOutputModes`；可选：`provider`、`security`、`securitySchemes`。
  - `securitySchemes.apiKeyAuth.in` 支持 `header`/`query`/`cookie`。

### 3.3 MCP 服务 API 文件规范与示例

- **核对 URL**：`https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPserviceAPIfilespecificationsandexamples?lang=zh`
- **标题**：MCP服务API文件规范与示例--[PRODUCT]-火山引擎（附录）
- **读取状态**：✅ 浏览器完整读取成功
- **提取要点（文件规范）**：
  - **语法**：无 Swagger/OpenAPI 3 语法错误；必须含 metadata、`info.title`、`info.version`；建议每个 operation 设 `operationId`。
  - **请求方法**：仅 `GET/POST/PUT/DELETE/PATCH`；`CONNECT/HEAD/OPTIONS/TRACE` 被忽略。
  - **请求类型**：支持 `application/json` 与 `application/x-www-form-urlencoded`；不支持 `application/xml`、`multipart/form-data`、`application/octet-stream`。
  - **请求参数**：array 类型在 path/query/header/formData(Swagger) 或 path/query/header/cookie(OpenAPI3) 位置序列化为 CSV；不支持 `file` 类型参数。
  - **响应**：仅解析 `200`、`201`、`default`，且只解析 1 个；优先级 `200 > 201 > default`。
  - 附完整 Swagger 2.0 与 OpenAPI 3.0.1 的 `/weather/{city}` GET 示例。

---

## 汇总结论

1. **无任何真实登录/权限阻塞**：所有目标页（火山引擎 [PRODUCT] 文档、APMPlus 观测站、[BASE-ADK]-python 独立站、adk.dev）均为公开文档，浏览器 DOM 读取全部成功。
2. **上一轮"用户访问阻塞/持续重定向失败"系误判**：根因是 web.fetch 无法渲染 JS 动态文档站，抓取落到落地页。**不应把 fetch 失败当作需要账号的依据。**
3. **3 个"重定向失败"页 URL 均未猜错**，浏览器可完整读取，内容已在本文件 3.1–3.3 提取。
4. **埋点字段已拿到数据契约**：
   - [PRODUCT] 侧：9 个 `gen_ai.*` Span 属性 + 2 个 Metrics（latency / count）。
   - [BASE-ADK] 侧：通用类 15 + LLM 类 23 + Tool 类 9 字段，含 token_usage 五项、model/tool/agent name、content 采集开关。
5. **ADK workflow API 已核对**：`Workflow/Event/Agent`、`@node`+`ctx.run_node`、`SequentialAgent/ParallelAgent/LoopAgent(max_iterations)`、协作 `Agent(mode=chat/task/single_turn)`、`RoutedAgent` TS 签名。`RemoteA2aAgent` 不在 workflows 章节，属 A2A Consuming 侧。
