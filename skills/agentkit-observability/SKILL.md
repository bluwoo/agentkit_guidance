---
name: agentkit-observability
description: AgentKit 可观测性——APMPlus（指标/链路）+ TLS（日志），无侵入接入，AI 层与微服务/基础设施同一条 trace，Follow gen.ai 语义标准。覆盖 Runtime/工具沙箱/记忆库/MCP服务/MCP工具集/网关/模型服务七大对象。支持 Codex/Claude Code/Cursor/OpenClaw 无侵入接入，自研 veops agent 做 trace 诊断。当需要查看 Agent 运行指标、下钻 Trace、排查日志、做统一排障、或接入三方 Coding Agent 观测时使用本 Skill。
---

# AgentKit 可观测性 (Observability) Skill

## 1. 概述

AgentKit 可观测性 = **APMPlus（指标/链路）** + **TLS（日志）**，开启观测服务后自动开通 APMPlus 与 TLS，绘制观测大盘。核心价值是让"agent 看得见"——运行时总览、Trace、模型、工具、日志、洞察大盘全套，从指标到链路到日志一体化定位问题。最大特色是**无侵入接入、跨云采集**，AI 层与微服务/基础设施**同一条 trace**，完全 Follow gen.ai 语义标准。支持主流 Coding Agent（Codex、Claude Code、Cursor、OpenClaw）无侵入接入，并内置自研 **veops agent** 做 trace 诊断洞察。观测可独立于 Agent 托管单独售卖。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已创建 AgentKit Runtime
- [ ] 已在 Runtime 创建/编辑页面**开启观测服务**（开启后自动开通 APMPlus + TLS）
- [ ] 如需接入三方 Coding Agent：已安装对应插件并配置无侵入注入
- 依赖包：无侵入接入无需额外安装；VeADK 侧通过环境变量开启 tracer
- 环境变量（VeADK 侧）：
  - `ENABLE_APMPLUS=true` — 开启 APMPlus 导出
  - `ENABLE_TLS=true` — 开启 TLS 日志导出
  - `ENABLE_COZELOOP=true` — 开启 CozeLoop 导出（可选）

## 3. 快速上手

### 3.1 控制台操作路径

**开启观测**：
AgentKit 控制台 → 智能体运行时 → 创建/编辑运行时 → 勾选"观测服务" → 发布

**查看观测大盘**：
AgentKit 控制台 → 智能体运行时 → 选择 Runtime → 观测数据 → 查看各对象监控大盘

**查看日志**：
AgentKit 控制台 → 智能体运行时 → 日志 → 查看 TLS 日志（含日志字段说明）

**数据回流（trace → 评测集，已按企业内部 Demo 核证）**：
AgentKit 控制台 → 左侧导航「可观测」分组下的独立「数据回流」Tab →「创建导出任务」：
1. **数据过滤**：设置过滤条件（可套用「推荐配置」预置卡片，如 LLM 调用异常样本 / 长度截断样本 / 高 Token 消耗样本），并按 `service.name` 等字段锁定目标 Runtime；选择时间范围与重复频率（支持按天/按周持续回流新数据）。
2. **导出配置**：导出平台选「智能体评测」，指定目标评测集（新建或已有），做字段映射（如 `GenAIInput→input`、`GenAIOutput→output`）。
3. **预览后提交**：先预览确认能抽到有效输入/输出，再提交；任务运行后 trace 即回流到评测集。
- **上限与限制**：总量与单次上限均为 **10 万条**；**只回流新数据**，历史数据需走离线 Trace 导出；PII 脱敏默认开启（关闭后可导出完整 Input/Output 用于调试）。（来源：<internal-lark-doc>；<internal-lark-doc>）
- 其他回流去向：暴露原始 topic 给 TLS 加工 / 导出 Kafka / LAS / TOS。
- **云端未实测**：以上为控制台配置路径，需云凭据在真实 Runtime 上联调验证。

### 3.2 代码集成（VeADK 侧 tracer 开启）

> Runner 入口骨架与签名（`runner.run` / SSE `run_async` / `inspect` 验证）统一见 [`../references/runner-entrypoint.md`](../references/runner-entrypoint.md)。本节只保留观测相关的最小装配。

```python
# VeADK 侧通过环境变量开启观测导出（见下方 §3.3 agentkit.yaml）
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()

agent = Agent(
    name="my_observable_agent",
    instruction="你是一个企业助手。"
)
runner = Runner(agent=agent, app_name="obs_app")

# 非流式（推荐）：runner.run(messages=) 直接返回字符串（完整签名见共享 reference §3）
@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result

# 流式 SSE（run_async + types.Content + 先 create_session）写法见 ../references/runner-entrypoint.md §4，
# 本处不再复制注释块。

app.run(host="0.0.0.0", port=8000)
```

### 3.3 agentkit.yaml 观测配置

```yaml
launch_types:
  cloud:
    runtime_envs:
      ENABLE_APMPLUS: "true"
      ENABLE_TLS: "true"
      # ENABLE_COZELOOP: "true"  # 可选
```

## 4. 核心概念与 API

### 4.0 三层分离观测文档结构（关键架构约束）

观测相关文档必须分三层，各自标注来源与验证状态：

| 层 | 名称 | 内容 | 来源 | 验证状态 |
|---|---|---|---|---|
| **层1** | **观测字段文档** | AgentKit/VeADK 埋点有哪些 Span 属性和 Metrics 字段 | 浏览器 DOM 读取 AgentKit/VeADK 官方文档站 | ✅ 已验证（§4.1–4.2 概览；详表见 [references/span-attributes-and-query-api.md](references/span-attributes-and-query-api.md) A 节） |
| **层2** | **平台查询 API** | 如何从 APMPlus 拉取 trace/span 数据（URL/鉴权/参数/响应） | 火山引擎 API Explorer 核验 | ✅ 已验证（见 [references/span-attributes-and-query-api.md](references/span-attributes-and-query-api.md) B 节） |
| **层3** | **Wizard 归一化 schema** | 前端 Trace 覆盖层使用的统一数据结构，从层1+层2映射而来 | 设计定义 | 🔧 设计定义，待 POC |

> **核心铁律**：单次 trace（一次 run_id/trace_id 范围内）**只能用该 trace 内的真实 span 数据**——duration 由 span `start_time`→`end_time` 差值计算，不是 Histogram P50/P95；错误来自 span `Status=ERROR` 或 error 事件，不是 error_type 维度聚合计数；调用次数按操作语义计数。**P50/P95/QPS 是选定时间窗的聚合观测指标，必须独立展示，不能归属到一次调用。**

### 4.1 可观测对象与指标（聚合观测面板用，不归属单次调用）

| 对象 | 关键聚合指标维度 | 用途 |
|---|---|---|
| **智能体运行时（Runtime）** | QPS、错误率、时延（P50/P95）、CPU/内存、入/出带宽 | 聚合面板，时间窗统计 |
| **工具（沙箱）** | 调用次数（聚合）、时延（P50/P95）、成功率 | 同上 |
| **记忆库** | 调用量（聚合）、检索时延（P50/P95） | 同上 |
| **MCP 服务** | 请求次数（聚合）、错误码分布、平均时延、出/入向带宽 | 同上 |
| **MCP 工具集** | 带宽流量、请求调用、检索类型、性能时延、工具索引 | 同上 |
| **网关实例** | QPS、请求次数、入口/出口总带宽、访问日志 | 同上 |
| **模型服务** | 推理 Token 消耗、缓存效率、推理时延（P50/P95） | 同上 |

> 以上指标均为**选定时间窗内的聚合统计**（来自 Histogram/Counter），用于「近 N 小时聚合」面板展示。**绝不回写到单次 trace 覆盖层的节点/边徽章。**

### 4.2 核心概念

| 概念 | 说明 |
|---|---|
| **APMPlus** | 火山引擎应用性能监控，提供指标/链路（Trace）能力 |
| **TLS** | 火山引擎日志服务，提供日志采集/查询能力 |
| **Trace** | 一次请求的全链路追踪，AI 层与微服务同一条 trace |
| **trace attribute** | Follow gen.ai 标准的丰富属性字段 |
| **veops agent** | 自研 AI Agent 场景诊断 skill，对 trace 做自动诊断洞察 |
| **无侵入接入** | 无需修改业务代码即可采集遥测；支持 Codex/Claude Code/Cursor/OpenClaw |
| **OTLP** | gRPC + HTTP + Collector 全收，多云多语言 |
| **单次 trace vs 聚合观测** | 单次 trace 用 span 起止差算 duration/span 状态算错误/操作语义计数；P50/P95/QPS 是聚合指标独立展示 |

### 4.3 单次 trace 的 span 数据 / 平台查询 API / 日志字段（层1+层2 详表）

下列三类深度资料已整体下沉到渐进披露参考，字段/参数/示例均为实测原表，未删改：

- **A. 单次 trace 的 span 数据**：两套埋点方案、AgentKit 侧 Span Attributes（9 个）与 Metrics（2 个）、VeADK 侧 Span 名打点时机、VeADK 通用类 15 / LLM 类 23 / Tool 类 9 个字段表、内容采集开关 `OBSERVABILITY_OPENTELEMETRY_TRACE_CONTENT`。
- **B. 平台查询 API（层2，APMPlus OpenAPI 2026-01-01）**：接入信息（域名/Service Code/签名 V4/BusinessCarrier=agentkit_runtime）、GetTraceDetail / ListSpan / ListSession 三接口的请求参数、响应结构、请求示例与「单次 trace vs 聚合浏览 vs 会话级 token」关键区分。
- **C. 日志字段（10 个）**：apmplus-server-log 主题的 attribute/file_line/trace_id 等完整字段。

→ 完整表格见 [references/span-attributes-and-query-api.md](references/span-attributes-and-query-api.md)。

> 记法不变：**单次 trace 的 duration 取 span `start_time`→`end_time` 差（GetTraceDetail 返回 `DurationMicroseconds`），错误取 span `Status=ERROR`；`gen_ai_runtime_operation_latency(_count)` 是集群聚合 Metrics，不归属单次调用。**

### 4.6 Trace 高级能力
- 一键跳转 playground
- 一键导出任务
- 多种基线问题自动回流模板
- 告警触发 trace 自动诊断（规划中）

## 5. 输入输出规范

### 输入
- 观测服务的输入是 Runtime 运行产生的遥测数据（指标、Trace、日志）
- 无侵入接入通过 OTLP 协议采集，无需业务代码改动

### 输出
- **观测大盘**：各对象指标图表（QPS/错误率/时延/带宽等）
- **Trace 详情**：下钻单次请求全链路，含 AI 层各节点
- **TLS 日志**：结构化日志查询
- **诊断报告**：veops agent 对 trace 的自动诊断洞察

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit 运行时管理权限（开启观测）+ APMPlus/TLS 只读查看权限
- **入站认证**：与 Runtime 一致
- **出站凭据**：观测本身不涉及出站凭据
- **数据安全**：trace 含完整对话内容，需注意 PII；数据驻留火山引擎境内；存储 30 天不另收费
- **安全围栏兼容**：统一排障路径最后一步结合安全围栏攻击日志判断是否被攻击

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| 观测大盘无数据 | 未开启观测服务 | 编辑 Runtime 勾选观测服务并重新发布 |
| Trace 链路不完整 | 埋点字段缺失 / 非 AI 层服务未接入 | 确认 AI 层与微服务同一条 trace；检查 OTLP 接入 |
| 日志查不到 | TLS 未开通 / 日志字段配置错 | 确认观测服务已自动开通 TLS；查看日志字段说明文档 |
| 三方 Coding Agent 无法接入 | 插件未安装 / 无侵入注入未配置 | 按官方文档安装对应插件（Codex/Claude Code/Cursor/OpenClaw） |
| veops agent 诊断无结果 | trace 数据不足 / 诊断 skill 未覆盖该场景 | 等待更多 trace 数据；参考诊断 skill 说明 |
| trace attribute 不丰富 | 未 Follow gen.ai 标准 / 内容采集开关关闭 | 确认使用最新版 veadk；如需输入/输出内容字段，检查 `OBSERVABILITY_OPENTELEMETRY_TRACE_CONTENT` 未设为 false |

**统一排障路径**：
```
观测大盘定位异常对象（Runtime/工具/MCP/模型）
    ↓
下钻 Trace（看 AI 层各节点耗时/错误）
    ↓
查看 TLS 日志（看详细报错）
    ↓
结合安全围栏攻击日志（判断是否被攻击）
```

## 8. 可执行验证办法

1. 确认 Runtime 开启观测服务后调用若干请求
2. 在观测大盘确认 Runtime 有 QPS、时延、错误率指标
3. 下钻一条 Trace，确认 AI 层各节点（模型调用、工具调用）在同一条 trace 中
4. 在 TLS 日志中确认有对应请求的结构化日志
5. 如需接入三方 Coding Agent，确认无侵入插件生效后 trace 可见

```bash
# 【需云凭据联调】<runtime-domain> 为 GetRuntime.Endpoint，未在本环境实测
# 验证调用产生 trace
curl -X POST https://<runtime-domain>/invoke \
  -H "Content-Type: application/json" \
  -H "user_id: test-user" \
  -H "session_id: obs-test" \
  -d '{"prompt": "帮我总结一下文档"}'
# 预期：200 返回；观测大盘可见 QPS 增量；Trace 列表可见对应链路
```

## 9. 与其他组件的关系

- **上游依赖**：AgentKit Runtime（必须开启观测服务）
- **下游联动**：
  - **评测（Evaluation）**：trace 数据回流到评测集，是评测的数据源
  - **安全围栏（Guardrails）**：排障路径最后一步结合攻击日志
  - **veops agent**：对 trace 做自动诊断
- **常见组合**：
  - Runtime + 观测 + 评测 = 完整 Eval-driven 闭环
  - 观测 + 安全围栏 = 安全事件可追溯
  - 三方 Coding Agent + 无侵入接入 = 统一观测多云多语言 Agent

## 10. 已知限制与注意事项

- **在线评测必须先开启观测服务**，否则 trace 无法回流
- **定价（服务端按写入数据量后付费，独立计费，实际以控制台为准）**：Trace 0.4 元/GB（境外 0.56），Metrics 0.18 元/百万数据点（境外 0.36）；**免费额度 Trace 25GB/月、Metrics 1 亿数据点/月**；TLS 日志赠送 30 天免费存储。（来源：<internal-lark-doc>）
- 支持无侵入接入的 Coding Agent：**Codex、Claude Code、Cursor、OpenClaw**
- 数据回流支持：回流到 agentkit、暴露原始 topic 给 TLS 加工、导出 Kafka/las/tos
- **后续规划**（以官方为准）：
  - Session 洞察分析：session 聚类 + 一键调用 devops agent 诊断
  - 告警触发 trace 自动诊断——异常自动归因
  - 推出预付费计价模式
- 观测可独立于 Agent 托管单独售卖，适合监控三方/自建 Agent
- 自建 Langfuse 迁移场景可迁移到火山托管观测，规避底层 CK 扩容瓶颈

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 观测概览（APMPlus+TLS） | https://docs.volcengine.com/docs/AgentKit/Observabilityoverview-2?lang=zh | 概览 |
| 数据观测与可观测对象指标表 | https://docs.volcengine.com/docs/AgentKit/Observability?lang=zh | 数据观测 |
| 统一排障路径 | https://docs.volcengine.com/docs/AgentKit/BasicTroubleshootingUnifiedTroubleshootingSchemeBasedonObservationSystem?lang=zh | 基础排障 |
| 运行时监控数据（AgentKit） | https://docs.volcengine.com/docs/86681/2164880?lang=zh | 监控数据 |
| 数据回流（全栈可观测平台） | https://docs.volcengine.com/docs/86845/2232301?lang=zh | 数据回流 |
| 三方接入/veops/定价/对比/路线图 | <internal-lark-doc> | doc07 第一节 |
| VeADK tracer 环境变量 | https://volcengine.github.io/agentkit-sdk-python/ | doc03 SDK 核验报告 3.2 节 |
| AgentKit 埋点字段与 Metrics（浏览器 DOM 读取） | https://docs.volcengine.com/docs/ObservabilityPlatform/AgentKittrackingfieldsandmetricsdescription?lang=zh | APMPlus 全栈可观测平台 |
| VeADK 埋点字段（通用/LLM/Tool 类，浏览器 DOM 读取） | https://volcengine.github.io/veadk-python/cn/docs/framework/span-attributes/ | VeADK 独立文档站 span-attributes |
| APMPlus GetTraceDetail OpenAPI（按 TraceId 查 span 树） | https://api.volcengine.com/api-docs/view?action=GetTraceDetail&serviceCode=apmplus_server&version=2026-01-01 | 火山引擎 API Explorer，2026-09-18 核验 |
| APMPlus ListSpan OpenAPI（按时间范围查 span 列表） | https://api.volcengine.com/api-docs/view?action=ListSpan&serviceCode=apmplus_server&version=2026-01-01 | 火山引擎 API Explorer，2026-09-18 核验 |
| APMPlus ListSession OpenAPI（按时间范围查会话列表） | https://api.volcengine.com/api-docs/view?action=ListSession&serviceCode=apmplus_server&version=2026-01-01 | 火山引擎 API Explorer，2026-09-18 核验 |
| APMPlus 服务地址（OpenAPI 域名/地域） | https://www.volcengine.com/docs/6431/1582353?lang=zh | 应用性能监控全链路版 |
| APMPlus OpenAPI 鉴权方式（AK/SK HMAC-SHA256 签名 V4） | https://www.volcengine.com/docs/6431/1176476?lang=zh | 应用性能监控全链路版 OpenAPI 使用示例 |
| 数据回流到评测集的控制台步骤/字段映射/10万条上限/PII 默认脱敏 | <internal-lark-doc> | 评测能力更新 + 可观测数据回流 OnePage（企业内部） |
| 回流「只回流新数据/历史走离线导出」等限制 | <internal-lark-doc> | Agent 观测/评测能力下钻对比（企业内部） |
| 观测/记忆库/知识库监控对象与观测诊断、点赞点踩 | <internal-lark-doc> | Agentkit 可观测产品能力（企业内部） |
| 观测计费（Trace/Metrics 单价与免费额度） | <internal-lark-doc> | AgentKit 产品与计费一览（企业内部） |
