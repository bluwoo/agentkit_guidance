# 14 观测 (Observability)

> 概览：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Observabilityoverview-2?lang=zh
> 数据观测：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Observability?lang=zh
> 排障：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/BasicTroubleshootingUnifiedTroubleshootingSchemeBasedonObservationSystem?lang=zh

## 概念

观测 = **APMPlus（指标/链路）** + **TLS 日志**。开启观测服务后自动开通 APMPlus 与 TLS，绘制观测大盘。

## 可观测对象与指标

| 对象 | 关键维度 |
|---|---|
| 智能体运行时 | QPS、错误率、时延、CPU/内存、入/出带宽 |
| 工具（沙箱） | 调用次数、时延、成功率 |
| 记忆库 | 调用量、检索时延 |
| MCP 服务 | 请求次数（图/柱/线）、错误码分布、平均时延、出/入向带宽、公网出向响应带宽 |
| MCP 工具集 | 带宽流量、请求调用、检索类型、性能时延、工具索引 |
| 网关实例 | QPS、请求次数、入口/出口总带宽、访问日志 |
| 模型服务 | 推理 Token 消耗、缓存效率、推理时延 |

## 数据观测与回流
- **数据观测**：在控制台查看各对象监控大盘。
- **数据回流**：把 Agent 运行数据回流用于评测/分析。
- **埋点字段与指标说明**：独立文档定义 Trace/Session 字段。

## 日志
- 开启日志 → 查看日志 → 日志字段说明；底层 TLS。

## 基础排障
来源：BasicTroubleshooting...
统一排障路径：从观测大盘定位异常对象（Runtime/工具/MCP/模型）→ 下钻 Trace → 查看 TLS 日志 → 结合攻击日志（安全围栏）判断是否被攻击。
