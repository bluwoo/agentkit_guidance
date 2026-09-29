# observability 深度参考：Span 字段表 / APMPlus 查询 OpenAPI / 日志字段

> 本文件是 `agentkit-observability` SKILL.md 的**渐进披露展开**：把层1 观测字段（gen_ai 属性/Metrics）、层2 APMPlus 查询 OpenAPI、层1 日志字段三张大表整体下沉到此。
> SKILL.md 只保留「三层分离铁律」「可观测对象概览」「核心概念」与跳转。所有字段/参数/示例均为浏览器 DOM / API Explorer 实测（2026-09-18），未删改。

---

## A. 单次 trace 的 span 数据（层1：观测字段文档，浏览器 DOM 已验证）

### A.1 两套埋点方案

官方将埋点分为两套：
- **AI应用监控（AgentKit）**：在 AgentKit SDK 内部接入 OpenTelemetry，涵盖分布式追踪 Tracing + 指标监控 Metrics。
- **VeADK**：在 VeADK SDK 内部接入 OpenTelemetry，涵盖通用类 / LLM 类 / Tool 类三大模块。

### A.2 AgentKit 侧 Span Attributes（每次调用 AgentKit Runtime 产生一条 Span）

| Attribute | 类型 | 描述 | 示例 |
|---|---|---|---|
| `gen_ai.system` | string | 大模型系统标识，固定为 `agentkit` | `"agentkit"` |
| `gen_ai.func_name` | string | 具体调用的函数 | `"run"` |
| `gen_ai.user.id` | string | 调用用户 ID | `"user_#a3f9b2"` |
| `gen_ai.session.id` | string | 调用会话 ID | `a2b1ee10-22df-42d9-8daa-986a609b1686` |
| `gen_ai.span.kind` | string | Gen AI 埋点 Span 类型，如 `workflow`/`llm` | `"workflow"` |
| `gen_ai.operation.name` | string | Runtime 执行的操作，如 `invoke_agent`、`tool` | `"invoke_agent"` |
| `gen_ai.operation.type` | string | 操作类型，如 `agent`、`a2a_agent` | `"agent"` |
| `gen_ai.input` | string | 调用的输入 | `{"prompt": "你好"}` |
| `gen_ai.output` | string | 调用的返回 | `"你好！很高兴为你提供帮助..."` |

> 注：trace_id 由 OTel 标准 traceparent 承载。**单次 trace 的 duration 由 span 的 `start_time`→`end_time` 差值计算（APMPlus GetTraceDetail 返回 `DurationMicroseconds`），不是 Metrics Histogram。**

### A.3 AgentKit 侧 Metrics 指标（聚合观测用，不归属单次调用）

| Metric | 类型 | 说明 | 指标维度 | 用途 |
|---|---|---|---|---|
| `agentkit_runtime_operation_latency` | Histogram | 调用耗时 | `error_type`（非空=失败）、`gen_ai_operation_name`、`gen_ai_operation_type` | **聚合面板**：P50/P95 时延（时间窗统计） |
| `agentkit_runtime_operation_latency_count` | Counter | 调用次数 | 同上三个维度 | **聚合面板**：QPS/总调用次数（时间窗统计） |

> ⚠️ 这两个 Metrics 是**集群聚合指标**，用于「近 N 小时聚合」面板。**绝不用于单次 trace 节点/边的次数/耗时/错误率。**

### A.4 VeADK 侧 Span 名（打点时机）

| 时机 | 打点函数 | Span 名称 |
|---|---|---|
| 调用 Agent | Runner 的 `_run_with_trace` | `invocation` |
| 运行 Agent | Agent 的 `run_async` | `invoke_agent {agent.name}` |
| 调用模型 | BaseLlmFlow 的 `_call_llm_with_tracing` | `call_llm` |
| 调用工具 | BaseLlmFlow 的 `_execute_single_function_call_async` | `execute_tool {tool.name}` |

> 内容采集开关：`observability.opentelemetry.trace_content` 或环境变量 `OBSERVABILITY_OPENTELEMETRY_TRACE_CONTENT`。设为 `false` 后，标记"受内容采集开关控制"的字段（输入/输出内容）不写入 Span；普通链路、模型参数、Token 用量、工具名等仍保留。

### A.5 VeADK 通用类字段（所有 Span，15 个）

| # | 字段名 | 含义 |
|---|---|---|
| 1 | `gen_ai.system` | 生成式 AI 系统提供方（缺省 `<unknown_model_provider>`） |
| 2 | `gen_ai.system.version` | VeADK 框架版本号 |
| 3 | `gen_ai.agent.name` | Agent 名称 |
| 4 | `openinference.instrumentation.veadk` | OpenInference 标准化埋点版本 |
| 5 | `gen_ai.app.name` | app_name |
| 6 | `gen_ai.user.id` | user_id |
| 7 | `gen_ai.session.id` | session_id |
| 8 | `agent_name` | Agent 名称（CozeLoop 别名） |
| 9 | `agent.name` | Agent 名称（TLS 平台别名） |
| 10 | `app_name` | app_name（CozeLoop 别名） |
| 11 | `app.name` | app_name（TLS 别名） |
| 12 | `user.id` | user_id（CozeLoop/TLS 别名） |
| 13 | `session.id` | session_id（CozeLoop/TLS 别名） |
| 14 | `cozeloop.report.source` | Trace 数据来源（固定 `veadk`） |
| 15 | `cozeloop.call_type` | CozeLoop 调用类型 |

### A.6 VeADK LLM 类字段（call_llm Span，23 个）

| # | 字段名 | 含义 |
|---|---|---|
| 1 | `gen_ai.request.model` | 模型名称 |
| 2 | `gen_ai.request.type` | LLM 请求类型（固定 `chat`） |
| 3 | `gen_ai.request.max_tokens` | 最大生成 token 数 |
| 4 | `gen_ai.request.temperature` | 采样温度 |
| 5 | `gen_ai.request.top_p` | top-p 参数 |
| 6 | `gen_ai.request.functions` | 函数/工具元数据 |
| 7 | `gen_ai.response.model` | 实际响应模型 |
| 8 | `gen_ai.response.stop_reason` | 停止原因 |
| 9 | `gen_ai.response.finish_reason` | 完成原因 |
| 10 | `gen_ai.is_streaming` | 是否流式 |
| 11 | `gen_ai.operation.name` | 操作名称（固定 `chat`） |
| 12 | `gen_ai.span.kind` | Span 类型（固定 `llm`） |
| 13 | `gen_ai.prompt` | 请求输入结构化（受内容采集开关控制） |
| 14 | `gen_ai.completion` | 响应输出结构化（受内容采集开关控制） |
| 15 | `gen_ai.usage.input_tokens` | 输入 token 数 |
| 16 | `gen_ai.usage.output_tokens` | 输出 token 数 |
| 17 | `gen_ai.usage.total_tokens` | 总 token 数 |
| 18 | `gen_ai.usage.cache_creation_input_tokens` | 缓存创建 token |
| 19 | `gen_ai.usage.cache_read_input_tokens` | 缓存读取 token |
| 20 | `gen_ai.messages` | 完整对话消息事件（受内容采集开关控制） |
| 21 | `gen_ai.choice` | 模型选择事件（受内容采集开关控制） |
| 22 | `input.value` | 完整 LLM 请求体（调试用） |
| 23 | `output.value` | 完整 LLM 响应体（调试用） |

### A.7 VeADK Tool 类字段（execute_tool Span，9 个）

| # | 字段名 | 含义 |
|---|---|---|
| 1 | `gen_ai.operation.name` | 操作名称（固定 `execute_tool`） |
| 2 | `gen_ai.tool.name` | 工具名称 |
| 3 | `gen_ai.tool.input` | 工具输入（受内容采集开关控制） |
| 4 | `gen_ai.tool.output` | 工具输出（受内容采集开关控制） |
| 5 | `cozeloop.input` | 工具输入（CozeLoop 别名） |
| 6 | `cozeloop.output` | 工具输出（CozeLoop 别名） |
| 7 | `gen_ai.span.kind` | Span 类型（固定 `tool`） |
| 8 | `gen_ai.input` | 工具输入（APMPlus 别名） |
| 9 | `gen_ai.output` | 工具输出（APMPlus 别名） |

---

## B. 平台查询 API（层2：APMPlus OpenAPI，已核验）

> 来源：火山引擎 API Explorer `https://api.volcengine.com/api-docs/view?action=GetTraceDetail&serviceCode=apmplus_server&version=2026-01-01` 等页面实测读取（2026-09-18）。

### B.1 API 接入信息

| 项 | 值 |
|---|---|
| **服务端监控 OpenAPI 域名** | `https://apmplus-server.<region>.volcengineapi.com`（华北2北京） |
| **API Version** | `2026-01-01` |
| **Service Code** | `apmplus_server` |
| **鉴权方式** | 火山引擎签名 V4（AK/SK HMAC-SHA256），通过 volcengine SDK 的 `Sign(req)` 签名 |
| **BusinessCarrier** | `agentkit_runtime`——配置此值时自动按 AgentKit 业务载体过滤 |

### B.2 三个核心查询接口

**GetTraceDetail**——按 TraceId 查询单条 trace 的完整 span 树：

| 项 | 值 |
|---|---|
| 用途 | 单次 trace 详情查询（Step4 测试验证核心路径） |
| 请求参数 | `TraceId`（必选）、`SuggestTime`（必选，时间戳或 0 加速查询） |
| 响应结构 | `Result.Trace.SpanList[]`（每个 span 含 SpanId/ParentSpanId/OperationName/ServiceName/Status/DurationMicroseconds/StartTimeMillisecond/GenAISpanKind/ErrorInfoList/EventList/TotalTokens/OutputTokens/CacheReadTokens/CallServiceName/CallServiceType/CallResourceName） |
| 摘要统计 | `Result.Summary`（SpanNums/ServiceNums/ErrorSpanIds） |
| 请求示例 | `POST https://apmplus-server.<region>.volcengineapi.com?Action=GetTraceDetail&Version=2026-01-01` Body: `{"TraceId":"<trace-id>","SuggestTime":1767196800}` |

**ListSpan**——按时间范围查询 span 列表（聚合/浏览用）：

| 项 | 值 |
|---|---|
| 用途 | 聚合浏览/趋势查询（配合 BusinessCarrier=agentkit_runtime） |
| 请求参数 | `StartTime`（秒）/`EndTime`（秒）、`Filters[]`（key/op/value）、`TagFilters[]`、`Offset`/`Limit`、`Order`/`OrderBy`、`MinCallCostMillisecond`/`MaxCallCostMillisecond`、`BusinessCarrier=agentkit_runtime` |
| 响应结构 | `Result.SpanList[]`（同 GetTraceDetail span 字段 + GenAIInput/GenAIOutput/ContainerId/InstanceId/CallApiName/CallResourceName） |
| 请求示例 | `POST https://apmplus-server.<region>.volcengineapi.com?Action=ListSpan&Version=2026-01-01` Body: `{"StartTime":1767196800,"EndTime":1767200400,"BusinessCarrier":"agentkit_runtime",...}` |

**ListSession**——按时间范围查询会话列表（含 token 统计）：

| 项 | 值 |
|---|---|
| 用途 | 会话级浏览（含 InputTokens/OutputTokens/TotalTokens/SessionStartTime/SessionEndTime） |
| 请求参数 | `StartTime`（毫秒）/`EndTime`（毫秒）、`Filters[]`（支持 session_id/user_id/service/trace_count/input_tokens/output_tokens/total_tokens/duration）、`TagFilters[]`、`PageNo`/`PageSize`、`OrderBy`/`Order`、`BusinessCarrier=agentkit_runtime` |
| 响应结构 | `Result.TotalCount`、`Result.SessionBriefs[]`（SessionId/UserId/TraceIds[]/InputTokens/OutputTokens/TotalTokens/SessionStartTime/SessionEndTime） |
| 请求示例 | `POST https://apmplus-server.<region>.volcengineapi.com?Action=ListSession&Version=2026-01-01` Body: `{"StartTime":...,"EndTime":...,"PageNo":1,"PageSize":20,...}` |

> **关键区分**：GetTraceDetail 用于**单次 trace 详情**（Step4 测试验证）；ListSpan 用于**聚合浏览**（时间窗内 span 列表）；ListSession 用于**会话级 token 统计**。三者均为 POST + AK/SK 签名鉴权。

---

## C. 日志字段（已核验，10 个）

AgentKit 专用日志存储在 **apmplus-server** 项目下的 **apmplus-server-log** 日志主题。已从官方"日志字段说明"页完整提取，共 10 个字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `attribute` | JSON 对象 | 日志其他属性（含 exception.message/type、span_id 等） |
| `file_line` | String | 日志对应文件行数 |
| `file_name` | String | 日志对应文件名 |
| `hostname` | String | 打印日志的容器/虚拟机主机名 |
| `log_level` | 枚举 | DEBUG/INFO/WARN/ERROR（未设置时呈现 `???`） |
| `message` | String | 日志原文 |
| `resource` | JSON 对象 | 资源属性（container_id/instance_id/host.arch/service.version 等） |
| `service` | String | 服务名 |
| `source` | String | 上报来源（如 otl-collector） |
| `trace_id` | String | TraceId，定位唯一请求 |
