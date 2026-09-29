# 前后端接口与观测集成（03）

> 文档性质：**接口设计规格**。**本阶段未执行云联调，火山引擎凭据可用性尚未核验**，Wizard 后端（Hermes + 薄 FastAPI shim）、目标 Runtime、APMPlus 观测、评测服务**均为设计目标**；本文定义契约与降级策略，不暗示已联通。
> 证据：`docs/hermes-veadk/05-hermes-as-base-verification.md`（Wizard 后端 = Hermes 原生主循环 `AIAgent.run_conversation` + 薄 FastAPI shim；**三层契约区分**——层 1 Runtime 强制：端口/启动命令/健康检查/鉴权/`POST /invoke`；层 2 VeADK/SDK 应用层可选路由 `/run` `/run_sse` `/sessions` `/ping`；Hermes 主路径不实现 `/web/harness-sidecar/status`，见 05 §3c）、`docs/volcengine-official/shard1-results.md`（CreateRuntime/GetRuntime/Tool 参数，Version 2025-10-30）、`shard2-results.md`（Runtime/会话资源操作）、`shard4-results.md`（日志字段 10 个）、`docs/volcengine-official/browser-gap-results.md`（**浏览器 DOM 补读成功：AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool 字段**）、`15-evaluation.md`（评测三件套）、`doc07.md`（trace 数据真实来源、回流）。

> **修订基线（2026-09-18，v1.3）**：① Wizard 后端**不是 veADK Agent**，而是 Hermes 原生主循环 + 薄 FastAPI shim；② **三层契约修正**：薄 shim 只须实现**层 1**（端口/启动命令/健康检查/鉴权/`POST /invoke`），`/run` `/run_sse` `/sessions` `/ping` 是 VeADK/SDK **应用层可选路由**（SDK 最精简 `AgentkitSimpleApp` 不含 `/run` `/run_sse` `/sessions`），按需补；**Hermes 主路径不实现 `/web/harness-sidecar/status`**；③ 测试调用可经 Wizard 后端透传到目标 Runtime `/invoke`，或前端直连目标 Runtime；④ **观测数据契约已升级为基于浏览器补读的真实埋点字段**（AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool），节点对齐依据 VeADK Span 名；日志 10 字段保留为 TLS 日志行数据源。

---

## 1. 总体分层

```
Wizard 前端
  │
  ├─(A)─ Wizard 后端：Hermes Agent (AIAgent.run_conversation) + 薄 FastAPI shim
  │        —— shim 满足层1：端口/启动命令/健康检查/鉴权/POST /invoke（调用入口）
  │        —— 层2 按需补：/run /run_sse /sessions /ping（VeADK/SDK 应用层路由，非 Runtime 强制）
  │        —— 不实现 /web/harness-sidecar/status（veADK 层，Hermes 主路径不用 create_agentkit_app）
  │        —— 其上叠加 Wizard 业务路由：业务目标访谈/草稿、智能推荐、草稿持久化
  ├─(B)─ 目标 Runtime /invoke（或 /run_sse 流式）
  │        —— 透传测试调用：可由 Wizard 后端转发，亦可前端直连
  ├─(C)─ 观测服务（APMPlus，日志主题 apmplus-server-log）
  │        —— 拉取本次调用日志/trace（覆盖层数据来源；仅 10 字段已核验）
  └─(D)─ AgentKit 评测服务 —— 评测集/评估器/评测实验结果
```

> **关键事实（据 05 核验 §3c 三层区分）**：AgentKit Runtime 的 API 层**不强制镜像必须基于 veADK/create_agentkit_app**，框架无关；但容器并非「任意无约束」——必须满足**层 1**（监听端口默认 8000 / 启动命令 `Command` / 存在健康检查 / 鉴权 KeyAuth 或 CustomJwt / 资源网络 IAM）。**`/run` `/run_sse` `/sessions` `/ping` 是 VeADK/ADK 应用层路由**（SDK 最精简 `AgentkitSimpleApp` 只含 `/invoke`+四个健康探针，无 `/run` `/run_sse` `/sessions`），非 Runtime 强制。Wizard 后端自身即按此形态运行：Hermes 进程为底座，FastAPI shim 满足层 1。当前**本阶段未执行云联调，火山引擎凭据可用性尚未核验**，上述所有跨层调用均为设计目标。

所有跨层调用原则上经 Wizard 后端**代理**（避免在浏览器暴露凭证），后端负责签名；测试调用 (B) 允许前端直连目标 Runtime（见 §3）。

---

## 2. (A) Wizard 前端 ↔ Wizard 后端（Hermes + 薄 FastAPI shim）

Wizard 后端 = Hermes 原生主循环（`run_agent.AIAgent` + `agent/conversation_loop.run_conversation`）+ 一层薄 FastAPI shim。shim 对外讲 Runtime HTTP 协议，其上再挂 Wizard 业务路由。

### 2.0 shim 暴露的端点（三层区分，设计目标）

**层 1（Runtime 强制，必须实现）**：

| 端点 | 方法 | 语义 |
|---|---|---|
| `/invoke` | POST | 调用入口；shim 内部映射到 `AIAgent.run_conversation(...)`（SDK 最精简 `AgentkitSimpleApp` 的调用端点） |
| 健康检查端点 | GET | **具体路径待 POC**（Runtime 网关打 `/ping` 还是 `/health` shard1 未写明）；先同时提供 `/ping`+`/health` 以兼容 SDK 习惯 |
| 端口 / 启动命令 / 鉴权 | — | 监听 8000、`Command`、KeyAuth Header 透传（层 1 强制项） |

**层 2（VeADK/SDK 应用层可选路由，按需实现，非 Runtime 强制）**：

| 端点 | 方法 | 语义 |
|---|---|---|
| `/run` | POST | 非流式调用（ADK 约定，SDK 最精简应用无；仅当要兼容 AgentKit CLI 再补） |
| `/run_sse` | POST | SSE 流式（依赖 Hermes `stream_delta_callback` 等回调钩子转 SSE，**待实测**；按需补） |
| `/sessions` | — | 会话 CRUD（ADK session service 路由，按需补） |

> **不实现**：`/web/harness-sidecar/status`——它是 veADK `create_agentkit_app` 的 harness_extension sidecar（仅当 `harness_extension is not None` 才注册），Hermes 主路径不用 `create_agentkit_app`，故不需要（见 05 §3c 层 2）。

> 注意区分：Wizard 后端**自己**的 `/invoke` 是打 Hermes 底座；§3 的 `/invoke` 是打**用户设计的目标 Runtime**。两者同名不同靶，前端在调用时必须带 `runtime_id` 区分。

### 2.1 Wizard 业务路由（叠加在 shim 之上）

负责引导式对话、草稿生成、智能推荐、草稿持久化：

- **POST** `/api/wizard/biz-goal/chat`
  - 请求：`{ session_id, message }`
  - 响应（SSE 流式）：Wizard 追问文本 + 抽取到的"待确认要点"事件流。
- **POST** `/api/wizard/biz-goal/points/confirm`：用户确认/修改要点。
- **POST** `/api/wizard/biz-goal/adr`、`/glossary`：基于已确认要点生成 ADR / 术语表草稿（对应 grill-with-docs 流程内 `grilling` + `domain-modeling` 两个子 skill 的产出）。
- **POST** `/api/wizard/biz-goal/generate`（prompt 快速模式）：`{ name, description, ... }` → 返回业务目标草稿。
- **GET/PUT** `/api/wizard/biz-goal`：读取/保存结构化业务目标草稿。
- **GET/PUT** `/api/wizard/evaluation/cases`：验收用例 CRUD。
- **POST** `/api/wizard/evaluation/recommend`：基于业务目标给判断方式建议。
- **GET** `/api/wizard/components`：组件卡片元数据（用途/前置/权限/配置 schema）。
- **POST** `/api/wizard/architecture/recommend`：`{ biz_goal, cases }` → 推荐组件组合。
- **GET/PUT** `/api/wizard/architecture`：保存/读取拓扑（节点 + 边 + 节点配置）。
- **POST** `/api/wizard/architecture/validate`：实时校验（依赖缺失/权限缺失/配置不完整）→ 问题清单。

> 设计原则：接口**只返回真实存在的资源**；后端无法给出推荐时返回空数组，前端显示引导文案，不编造推荐。grill-with-docs 为 `disable-model-invocation: true` 的显式流程型 skill，前端须由用户显式触发后再调 `/api/wizard/biz-goal/chat` 进入访谈（见 01 §2.2）。

---

## 3. (B) 测试调用接口（目标 Runtime `/invoke` / `/run_sse`）

目标 Runtime 同样按 Runtime HTTP 协议对外提供 `/invoke`（同步）与 `/run_sse`（流式），并接受 KeyAuth（Header 中指定 `ApiKeyName` 的鉴权头）或 CustomJwt 鉴权。两条调用路径（设计目标，当前未联调）：

**路径一：经 Wizard 后端透传**
- **POST** `/api/wizard/runtime/invoke`（Wizard 后端转发到目标 Runtime `/invoke` 或 `/run_sse`）
  - 请求：
    ```
    {
      runtime_id,
      input: "<测试 prompt>",
      user_id, session_id,
      stream: true|false
    }
    ```
  - 响应：`stream=false` 一次性 JSON；`stream=true` SSE 逐 token/逐事件转发。
  - 响应须回传本次调用的 `trace_id`（若观测已埋点），供覆盖层拉取观测数据。

**路径二：前端直连目标 Runtime**
- 在目标 Runtime 已配置浏览器可达的公网/私网域名 + KeyAuth Header 时，前端可直接 `POST {runtime_endpoint}/invoke`（或 `/run_sse`）。此时鉴权 Header 由用户在测试面板一次性填写并仅存于会话内存，不落盘。
- 选择哪条路径由用户在 Step3 目标 Runtime 配置里指定；默认走路径一（代理），避免把凭证长期暴露在前端。

- 失败：透传 Runtime 错误码与 message（映射到 UI 状态 S4）。
- **本阶段未执行云联调，火山引擎凭据可用性尚未核验**：以上调用未做任何真实联调；Runtime 网关确切探活路径 / 鉴权 header 名 / SSE 事件格式尚需一次真实 CreateRuntime 验证（05 核验 §9 阻断点 2）。

---

## 4. (C) 观测数据获取接口

> **⚠️ 核心修正（v1.3，2026-09-18）**：此前版本把集群聚合 Metrics（`agentkit_runtime_operation_latency` Histogram 的 P50/P95、`agentkit_runtime_operation_latency_count` Counter 的调用次数）误用于单次 trace 节点/边的次数/耗时/错误率，违背「单次测试调用与聚合观测严格分离」的要求。本节已重写，严格区分：
> - **单次 trace 数据**（一次 run_id/trace_id 范围内）：仅用该 trace 内的真实 span 数据——duration 由 span `start_time`→`end_time` 差值计算；错误来自 span `status=ERROR` 或 error 事件；调用次数按操作语义计数。
> - **聚合观测数据**（选定时间窗）：P50/P95/QPS 等是 Histogram/Counter 在时间窗内的聚合统计，**独立展示在「近 N 小时聚合」面板中，不归属到任何一次调用**。
> - APMPlus trace 查询 API 已通过火山引擎 API Explorer 核验（见 §4.0），不再臆造接口。

### 4.0 APMPlus 查询 API 核验结果（已验证）

> 来源：火山引擎 API Explorer `https://api.volcengine.com/api-docs/view?action=GetTraceDetail&serviceCode=apmplus_server&version=2026-01-01` 等页面实测读取（2026-09-18）。

| 项 | 核验结果 |
|---|---|
| **服务端监控 OpenAPI 域名** | `https://apmplus-server.cn-beijing.volcengineapi.com`（华北2北京）；上海 `apmplus-server.cn-shanghai.volcengineapi.com` |
| **API Version** | `2026-01-01` |
| **Service Code** | `apmplus_server` |
| **鉴权方式** | 火山引擎签名 V4（AK/SK HMAC-SHA256），通过 volcengine SDK 的 `Sign(req)` 签名；**不使用 API Key** |
| **BusinessCarrier 特殊值** | `agentkit_runtime`——配置此值时，`ProjectName` 和 `TagFilters` 不生效，自动按 AgentKit 业务载体过滤 |

**三个核心查询接口：**

| API | 用途 | 关键请求参数 | 关键响应字段 |
|---|---|---|---|
| **GetTraceDetail** | 按 TraceId 查询单条 trace 的完整 span 树 | `TraceId`（必选）、`SuggestTime`（必选，时间戳或 0 加速查询） | `Trace.SpanList[]`（每个 span 含 `SpanId`/`ParentSpanId`/`OperationName`/`ServiceName`/`Status`/`DurationMicroseconds`/`StartTimeMillisecond`/`StartTimeMicrosecond`/`GenAISpanKind`/`ErrorInfoList`/`EventList`/`TotalTokens`/`OutputTokens`/`CacheReadTokens`/`CallServiceName`/`CallServiceType`/`CallResourceName`）、`Summary.SpanNums`/`ServiceNums`/`ErrorSpanIds` |
| **ListSpan** | 按时间范围查询 span 列表（聚合/浏览用） | `StartTime`（秒）/`EndTime`（秒）、`Filters[]`（key/op/value）、`TagFilters[]`、`Offset`/`Limit`、`Order`/`OrderBy`、`MinCallCostMillisecond`/`MaxCallCostMillisecond`、`BusinessCarrier=agentkit_runtime` | `SpanList[]`（同 GetTraceDetail 的 span 字段 + `GenAIInput`/`GenAIOutput`/`ContainerId`/`InstanceId`/`CallApiName`/`CallResourceName`） |
| **ListSession** | 按时间范围查询会话列表（含 token 统计） | `StartTime`（毫秒）/`EndTime`（毫秒）、`Filters[]`（支持 session_id/user_id/service/trace_count/input_tokens/output_tokens/total_tokens/duration）、`TagFilters[]`、`PageNo`/`PageSize`、`OrderBy`/`Order`、`BusinessCarrier=agentkit_runtime` | `TotalCount`、`SessionBriefs[]`（`SessionId`/`UserId`/`TraceIds[]`/`InputTokens`/`OutputTokens`/`TotalTokens`/`SessionStartTime`/`SessionEndTime`） |

> **关键结论**：单次 trace 详情走 **GetTraceDetail**（按 TraceId 查询）；聚合浏览/趋势走 **ListSpan**（按时间范围+过滤条件）；会话级 token 统计走 **ListSession**。三者均为 POST 到 `apmplus-server.cn-beijing.volcengineapi.com?Action=<Action>&Version=2026-01-01`，AK/SK 签名鉴权。

### 4.1 获取方式

#### 4.1.1 单次 trace 查询（Step4 测试验证核心路径）

- **GET** `/api/wizard/observability/trace`
  - 请求：`{ runtime_id, trace_id, service?, user_id?, session_id? }`
  - 后端内部调用 APMPlus **GetTraceDetail**：
    ```
    POST https://apmplus-server.cn-beijing.volcengineapi.com?Action=GetTraceDetail&Version=2026-01-01
    Body: { "TraceId": "<trace_id>", "SuggestTime": <调用时刻时间戳或0> }
    Auth: 火山引擎签名V4 (AK/SK HMAC-SHA256)
    ```
  - 响应：按 `02` §4 的 **Wizard 归一化 TraceOverlay schema** 返回（见 §4.2 单次 trace 数据结构）。

#### 4.1.2 聚合观测查询（独立面板，不归属单次调用）

- **GET** `/api/wizard/observability/metrics/aggregate`
  - 请求：`{ runtime_id, time_window: "1h"|"6h"|"24h"|"7d", service?, operation_name? }`
  - 后端内部调用 APMPlus **ListSpan**（按时间范围+过滤条件拉取 span 列表），后端自行聚合计算 P50/P95/调用次数/错误率：
    ```
    POST https://apmplus-server.cn-beijing.volcengineapi.com?Action=ListSpan&Version=2026-01-01
    Body: { "StartTime": <窗口起始秒>, "EndTime": <窗口结束秒>, "Filters": [...],
            "TagFilters": [...], "Offset": 0, "Limit": 100,
            "Order": "DESC", "OrderBy": "start_time_millisecond",
            "BusinessCarrier": "agentkit_runtime" }
    Auth: 火山引擎签名V4 (AK/SK HMAC-SHA256)
    ```
  - 响应：聚合统计面板数据（P50/P95/QPS/错误率/调用次数），**明确标注为「近 N 小时聚合」，不关联到任何单次调用**。
  - 也可直接使用 AgentKit 侧 Metrics（`agentkit_runtime_operation_latency` Histogram / `_count` Counter）的聚合查询接口获取 P50/P95/QPS——**但仅限聚合面板，绝不回写到单次 trace 覆盖层**。

#### 4.1.3 日志层查询

- **GET** `/api/wizard/observability/logs`
  - 请求：`{ runtime_id, trace_id?, service?, time_window?, log_level? }`
  - 日志层位于 `apmplus-server` 项目的 `apmplus-server-log` 日志主题（TLS），10 个字段已核验（shard4 §3/§41）。

### 4.2 单次 trace 数据结构（严格用 span 数据，不用聚合 Metrics）

```
TraceOverlay {
  trace_id: string              // OTel 标准 traceparent 承载
  spans: [                      // 来自 APMPlus GetTraceDetail 的 SpanList
    {
      span_id: string
      parent_span_id: string    // OTel 标准父子关系（APMPlus 返回 ParentSpanId）
      name: string               // = OperationName（VeADK Span 名：
                                 //   invocation / invoke_agent {agent.name} /
                                 //   call_llm / execute_tool {tool.name}）
      start_time_ms: number      // APMPlus 返回 StartTimeMillisecond
      end_time_ms: number        // = start_time_ms + DurationMicroseconds/1000
      duration_ms: number        // ⚠️ = DurationMicroseconds / 1000（span 起止差计算）
                                 //    不是 Histogram 的 P50/P95！
      status: {
        code: "OK" | "ERROR"    // APMPlus Status 字段；ErrorInfoList 非空=ERROR
        error_info?: {
          error_kind: string     // ErrorInfoList[].ErrorKind
          error_message: string  // ErrorInfoList[].ErrorMessage
          error_stack: string    // ErrorInfoList[].ErrorStack
        }
      }
      genai_span_kind: string    // APMPlus GenAISpanKind（llm / tool / workflow 等）
      service_name: string      // APMPlus ServiceName
      operation_name: string     // APMPlus OperationName
      call_service_name: string  // APMPlus CallServiceName（被调服务）
      call_service_type: string  // APMPlus CallServiceType
      call_resource_name: string // APMPlus CallResourceName
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
        genai_input: string               // ListSpan 返回的 GenAIInput
        genai_output: string              // ListSpan 返回的 GenAIOutput
        total_tokens: number              // TotalTokens
        output_tokens: number             // OutputTokens
        cache_read_tokens: number        // CacheReadTokens
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

### 4.3 单次 trace 的节点/边数据计算规则（严格分离聚合）

**节点着色与数据（基于单次 trace 内 span）：**

| 展示项 | 数据来源 | 计算方式 |
|---|---|---|
| **节点是否被调用** | 单次 trace 内是否存在对应 span | trace 中有匹配的 span → 已调用；无 span → 无数据（≠未调用） |
| **节点耗时 duration** | 单个 span 的 `start_time_ms` → `end_time_ms` 差值 | `duration_ms = DurationMicroseconds / 1000`（APMPlus GetTraceDetail 直接返回）。**不是 Histogram P50/P95** |
| **节点是否失败** | span 的 `Status` 字段 + `ErrorInfoList` | `Status=ERROR` 或 `ErrorInfoList` 非空 → 失败标红。**不是 error_type 维度聚合计数** |
| **节点调用次数** | 单次 trace 内该组件对应的 span 出现次数 | 按操作语义计数：`execute_tool {tool.name}` span 出现 3 次 = 该工具被调用 3 次（即使是同一工具的重试）。**不是 `_count` Counter** |

**边着色与数据（基于单次 trace 内 span 父子关系）：**

| 展示项 | 数据来源 | 计算方式 |
|---|---|---|
| **边是否发生** | span 的 `parent_span_id` 父子关系 | trace 中有 A→B 的父子 span 链 → 边已发生 |
| **边耗时** | 子 span 的 `duration_ms` | 同上，span 起止差计算 |
| **边调用次数** | 单次 trace 内 A→B 父子链出现次数 | 按 span 树遍历计数，含重试。**不是 Counter** |
| **边错误率** | 单次 trace 内该父子链中 ERROR span 占比 | 在单次 trace 内计算（如 3 次调用 1 次错 = 33%）。**不是 error_type 维度的跨调用聚合** |

**⚠️ 聚合观测指标（P50/P95/QPS/错误率趋势）——独立面板，绝不归属单次调用：**

| 展示项 | 数据来源 | 展示位置 |
|---|---|---|
| P50/P95 时延 | `agentkit_runtime_operation_latency` Histogram（选定时间窗聚合） | **独立的「近 N 小时聚合」面板**，不回写到单次 trace 覆盖层 |
| QPS | `agentkit_runtime_operation_latency_count` Counter / 时间窗 | 同上 |
| 错误率趋势 | `error_type` 维度聚合计数 / 总计数 | 同上 |
| 调用次数趋势 | Counter 聚合 | 同上 |

### 4.4 组件调用证据映射（证据字段 + 资源 ID，碰撞标 unknown）

**核心原则**：仅工具名或 span 名不能唯一证明某 Skill/MCP/KB 被调用。必须用 span 属性 + 资源 ID 做映射。

| 架构图节点类型 | 证据字段组合（用于映射到设计时 component_id） | 碰撞/缺失处理 |
|---|---|---|
| **Agent 节点** | `service.name` + `operation.name=invoke_agent` + `gen_ai.agent.name` | `gen_ai.agent.name` 精确匹配设计时 Agent 的 `component_id`；匹配不上标 `unknown` |
| **模型服务节点** | `operation.name=call_llm` + `gen_ai.request.model` | `gen_ai.request.model` 标识模型；同一模型被多 Agent 调用时，靠父子 span 链归属到调用方 Agent |
| **工具/Skill 节点** | `operation.name=execute_tool` + `gen_ai.tool.name` + `service.name` | `gen_ai.tool.name` 匹配设计时 Skill/MCP 的 `component_id`；**多个 Skill 同名**时靠 `service.name` + 资源 ID 消歧；匹配不上标 `unknown` |
| **MCP 服务节点** | `call_service_type` + `call_service_name` + `call_resource_name` | APMPlus 返回的 `CallServiceName`/`CallResourceName` 对应 MCP 服务/工具；靠资源 ID 映射 |
| **知识库节点** | span 属性中 KB 检索相关字段（待 POC 确认具体字段名） | 待 POC；当前标 `unknown` |
| **Runtime 入口** | `operation.name=invocation` + `service.name` | 根 span，对应 Runtime 节点 |

**observed-unmapped 节点**：trace 中发现但设计图中没有的节点（如 `operation.name`/`gen_ai.tool.name` 在设计时拓扑中找不到对应 component_id），在覆盖层上以「观测到但未在设计中」单独展示，**不强行塞进设计图，也不丢弃**。

**Skill 加载 vs 执行区分**：
- **Skill 被加载（mounted）**：仅在设计时拓扑中存在连接关系，trace 中无对应 `execute_tool` span → 显示「已挂载，本次未执行」。
- **Skill 被执行（executed）**：trace 中有对应 `execute_tool {tool.name}` span → 显示「已执行」，附耗时/错误状态。
- 两者**分开展示**，不混为一谈。

### 4.5 轮询 / 推送策略

- **测试完成后拉取**：`/invoke` 返回后立即请求一次 GetTraceDetail；因链路异步落库可能延迟，采用**有限轮询**：每 1.5s 拉一次，最多 ~10 次（约 15s），出现数据即停。
- 若轮询超时仍无数据 → 进入 UI 状态 **S3（完成但无观测数据）**，显示"无观测数据"（**不代表目标 Agent 未被调用**）。
- 不采用"前端常驻订阅"；后续可演进为 WebSocket/SSE 推送就绪事件（选型见 `04`）。

### 4.6 未接通 / 无数据的降级（关键约束）

| 情况 | 后端返回 | 前端表现 |
|---|---|---|
| 观测服务未配置（Runtime 未开观测/未重新发布） | `{ status: "not_configured" }` | 覆盖层开关置灰，显示"观测服务未配置" |
| APMPlus GetTraceDetail 接口报错/超时 | `{ status: "error", error }` | 显示"暂无法获取观测数据"+ 错误摘要 |
| 已接通但本次无数据（TraceId 查不到 span） | `{ status: "empty" }` | 显示"无观测数据（本次调用暂无数据）"，节点保持设计中性色；**不代表未调用** |
| 字段缺失 / 未核验 span 字段 | 对应指标返回 `null` | UI 显示"—"，不臆造数值 |
| APMPlus API 凭据未配置（AK/SK 未配置或无权限） | `{ status: "auth_error", error }` | 显示"观测 API 鉴权失败" |

**铁律**：以上任何一种，前端**都不得**用默认绿/红/灰伪造调用关系。覆盖层只渲染后端真实返回的 span 数据；未核验 span 字段一律 "—"。**单次 trace 绝不使用聚合 Metrics（P50/P95/QPS）的数据。**

---

## 5. (D) 评测结果获取接口

依据 `15-evaluation.md`：评测三件套（评测集/评估器/评测实验）。

- **GET** `/api/wizard/evaluation/datasets`：列出关联评测集（未连接时返回 `{ connected: false }`）。
- **POST** `/api/wizard/evaluation/import-cases`：把 Step2 本地用例导入评测集。
- **GET** `/api/wizard/evaluation/experiments/{id}/result`：拉评测实验结果（效果/性能/成本）。
- 线上 trace 回流评测集（`doc07.md`）：作为引导文案呈现，前端不展示未拉到的回流数据。

降级：评测服务未连接时，Step2 的"关联评测集"区域显示"评测服务未连接，可先在本地维护用例"，不展示假评测结果。

---

## 6. 接口鉴权与安全

- 前端 ↔ Wizard 后端：会话登录态。
- Wizard 后端 ↔ 目标 Runtime：按 Runtime 入站鉴权配置携带 **KeyAuth**（Header 中 `ApiKeyName` 指定的头）或 **CustomJwt**（DiscoveryUrl + AllowedClients）；凭证不出后端。前端直连目标 Runtime 路径（§3 路径二）除外，此时 KeyAuth Header 由用户在测试面板临时填写、仅存会话内存。
- Wizard 后端 ↔ 观测/评测：后端统一签名，凭证不出后端。
- trace/日志的 input/output 摘要默认脱敏；涉及身份与权限策略的资源，后端按权限策略决定能否取数，无权时返回 `forbidden`，前端提示"无权限查看该观测数据"。
- 当前**本阶段未执行云联调，火山引擎凭据可用性尚未核验**：以上鉴权链路均为设计目标。

---

## 7. 证据引用

- Wizard 后端形态（Hermes `AIAgent.run_conversation` + 薄 FastAPI shim）、**三层契约区分**（层 1 Runtime 强制：端口/启动命令/健康检查/鉴权/`POST /invoke`；层 2 VeADK/SDK 应用层可选路由 `/run` `/run_sse` `/sessions` `/ping`；Hermes 主路径不实现 `/web/harness-sidecar/status`）、未联调阻断点：`docs/hermes-veadk/05-hermes-as-base-verification.md`（§1b、§3c 三层、§4、§7、§9）。
- CreateRuntime/GetRuntime/Tool/会话资源参数（Version 2025-10-30）：`docs/volcengine-official/shard1-results.md`、`shard2-results.md`。
- 观测开启方式（需重新发布生效）、日志主题 `apmplus-server-log`、**已核验 10 个日志字段**：`docs/volcengine-official/shard4-results.md`（§3、§41、附录A）。
- **埋点字段与 Metrics（浏览器 DOM 补读，2026-09-18）**：`docs/volcengine-official/browser-gap-results.md`（任务1：AgentKit 9 Span 属性+2 Metrics、VeADK 4 Span 名+15 通用+23 LLM+9 Tool 字段）。
- **APMPlus trace 查询 API（火山引擎 API Explorer 核验，2026-09-18）**：GetTraceDetail（按 TraceId 查 span 树）、ListSpan（按时间范围+过滤条件）、ListSession（会话级 token 统计）。域名 `apmplus-server.cn-beijing.volcengineapi.com`，鉴权 AK/SK HMAC-SHA256 签名 V4，API Version `2026-01-01`，`BusinessCarrier=agentkit_runtime`。来源：`https://api.volcengine.com/api-docs/view?action=GetTraceDetail&serviceCode=apmplus_server&version=2026-01-01`、ListSpan、ListSession 同站。
- 评测集/评估器/评测实验：`15-evaluation.md`。
- trace 真实来源、回流、gen.ai 语义方向：`docs/lark-supplements/doc07.md`。

---

## 修订记录

| 日期 | 版本 | 修订内容 |
|---|---|---|
| 2026-09-18 | v1.3 | **观测数据契约重大修正**：① §4 整节重写——严格分离单次 trace 与聚合观测：单次 trace 的 duration 由 span `start_time`→`end_time` 差值计算（`DurationMicroseconds/1000`），错误来自 span `Status`/`ErrorInfoList`，调用次数按操作语义计数；P50/P95/QPS 等聚合指标独立展示在「近 N 小时聚合」面板，**绝不归属到一次调用**；② APMPlus 查询 API 已通过火山引擎 API Explorer 核验：GetTraceDetail（按 TraceId 查 span 树）、ListSpan（按时间范围+过滤条件）、ListSession（会话级 token 统计），域名 `apmplus-server.cn-beijing.volcengineapi.com`，鉴权 AK/SK HMAC-SHA256 签名 V4，API Version `2026-01-01`，`BusinessCarrier=agentkit_runtime`；③ 组件调用证据映射：用 `service.name`+`operation.name`+`gen_ai.agent.name`/`gen_ai.tool.name`+资源 ID 做映射，碰撞标 `unknown`，trace 中未设计节点标 `observed-unmapped`；Skill mounted vs executed 分开展示；④ §4.2 单次 trace 数据结构中 `duration_ms` 标注为 span 起止差计算而非 Histogram；⑤ 降级表新增 APMPlus API 鉴权失败行。 |
| 2026-09-18 | v1.2 | 浏览器 DOM 补读成功后更新观测数据契约：① §1 分层图 (C) 观测服务描述从"仅 10 字段已核验"更新为"Span 层真实字段+日志层 10 字段"；② §4.1 响应结构从"仅日志行"升级为"Span 树+Metrics+日志行"；③ §4.3 字段映射从"service 唯一对齐键、span 字段待核验"升级为"VeADK Span 名映射到节点 + OTel parent_span_id 构建父子树 + Metrics 维度做边徽章"；新增 `trace_content` 开关降级说明；④ §4.4 降级表"未核验 span 字段"行改为"内容采集开关关闭"；⑤ §7 证据引用更新。 |
| 2026-09-18 | v1.1 | 依据 Hermes 核验文档与 shard4 观测字段核验纠正：① 头部与 §1 分层图把 Wizard 后端从"veADK Agent"改为"Hermes Agent（`AIAgent.run_conversation`）+ 薄 FastAPI shim"，并新增"本阶段未执行云联调、火山引擎凭据可用性尚未核验、全部设计目标"声明；② §2 新增 shim Runtime 协议端点表（`/run`/`/run_sse`/`/invoke`/`/ping`/`/web/harness-sidecar/status`），并区分"Wizard 自身 /invoke"与"目标 Runtime /invoke"两个同名不同靶端点；业务路由保留；③ §3 测试调用改为"经 Wizard 后端透传目标 Runtime `/invoke`/`/run_sse` 或前端直连"两条路径，补充 KeyAuth/JWT 鉴权与未联调说明；④ §4 观测数据契约收紧为"仅 10 个已核验日志字段 + trace_id"，span 级字段全部标注为待 APMPlus/VeADK 核验的设计假设，核验前边徽章显示 "—"；降级表 S3 补"无数据不代表未调用"；⑤ §6 鉴权改为 Runtime KeyAuth/CustomJwt 语义；⑥ §7 证据引用更新。 |
| （初始版） | v1.0 | 首版接口设计规格。 |


---

## 措辞与契约修正记录（2026-09-18）

- 头部、§1 关键事实、§3、§6、§7、修订记录中「当前无云凭据/未联调」改为「本阶段未执行云联调，火山引擎凭据可用性尚未核验」。
- §1 关键事实与证据引用由「托管任意 OCI 容器但须讲协议+KeyAuth/JWT」补为完整运行时契约清单指引（端口/健康检查/调用协议/会话/鉴权/生命周期/网络与 IAM）。

---

## 三层契约修正记录（2026-09-18，v1.3）

> 触发：§2.0 原把 `/run` `/run_sse` `/invoke` `/ping` `/web/harness-sidecar/status` 列为"Runtime 协议端点"，证据不支持。源码实证后重分三层。

1. **§2.0 端点表改为三层**：层 1（`/invoke` 调用入口 + 健康检查端点，路径待 POC + 端口/启动命令/鉴权）；层 2（`/run` `/run_sse` `/sessions` `/ping`，VeADK/SDK 应用层可选路由，按需补）。
2. **关键反证**：SDK 最精简 `AgentkitSimpleApp` 只含 `/invoke`+四个健康探针，无 `/run` `/run_sse` `/sessions`。
3. **Hermes 主路径不实现 `/web/harness-sidecar/status`**（veADK harness_extension 层）。
4. **降级待 POC**：Runtime 网关具体探活路径（`/ping` vs `/health`）与调用转发路径（`/invoke` vs `/run`）shard1 未写明。
5. **同步**：头部修订基线 v1.3、§1 分层图与关键事实、§7 证据引用。
