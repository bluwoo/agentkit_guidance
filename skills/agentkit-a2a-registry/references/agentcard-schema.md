# a2a-registry 深度参考：AgentCard 字段规范（PRD 核证 2026-09-22）

> 本文件是 `agentkit-a2a-registry` SKILL.md §4 的展开：AgentCard 的注册来源与必填/可选字段全表。
> 字段与 `protocolVersion` 均为 PRD 核证（2026-09-22），未删改。

## 注册来源（Source）

A2aAgent 的注册来源（Source）：**Runtime**（填 Runtime 地址）或 **Standard**（`ImportType=json` 导入 JSON 文件 / `ImportType=url` 填 AgentCard 地址，`SetDefaultVersion=true`）。

AgentCard 遵循 Google A2A 协议，平台当前支持 `protocolVersion` 为 **0.2.6 与 0.3.0**（来源：<internal-lark-doc>

## 必填字段

| 字段 | 说明 |
|---|---|
| `version` | 语义化版本（如 `1.0.0`） |
| `name` | Agent 名称（≤64 字符，ASCII 可视字符） |
| `description` | 描述 |
| `protocolVersion` | `0.2.6` / `0.3.0` |
| `supportedInterfaces[].url` | HTTPS 服务地址 |
| `supportedInterfaces[].protocolBinding` | 取 `JSONRPC`（`GRPC`/`HTTP+JSON` 为旧版已废弃） |
| `defaultInputModes` | 如 `["text/plain","application/json","image/png"]` |
| `defaultOutputModes` | 同上 |
| `skills[]` | 每项含 `id` / `name` / `description` / `tags`（可选 `examples`/`inputModes`/`outputModes`） |

## 可选字段

`capabilities.streaming`、`capabilities.pushNotifications`、`capabilities.stateTransitionHistory`、`capabilities.extendedAgentCard`；`securitySchemes`（API Key / OAuth2；API Key 可配 `in: query|header`）与 `securityRequirements`；`iconUrl`、`documentationUrl`、`provider.organization`/`url`、`tenant`、`capabilities.extensions`。

A2A 运行期消息方法为 `message/send`（JSON-RPC）（来源：<internal-lark-doc>

最小可导入 JSON 示例见 SKILL.md §11 来源追溯对应行（ArkClaw 企业版 Agent 手册）。
