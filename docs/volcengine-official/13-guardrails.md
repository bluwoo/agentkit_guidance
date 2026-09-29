# 13 安全围栏 (Guardrails)

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Guardrailsoverview?lang=zh
> 集成：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/IntegratingGuardrailsinagents?lang=zh

## 概念

安全围栏基于**大模型应用防火墙**，嵌入 Agent 业务流程，实时监控模型输入/输出，防护 OWASP LLM Top10：
- **提示词攻击防护**（Prompt Injection）
- **模型滥用防护**
- **敏感数据防护**（PII 识别/脱敏）
- **算力消耗防护**（DDoS/资源滥用）

## 操作
- 在 Runtime 创建/编辑时勾选"安全围栏服务"开启。
- 开启后在 Agent 中自动集成（无需改业务代码）。
- 查看安全概览、攻击日志；可关闭安全围栏。
- 独立计费（大模型应用防火墙计费）。
