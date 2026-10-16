# a2a-registry 深度参考：AgentCard 字段规范（以公开示例为准）

> 本文件是 `agentkit-a2a-registry` SKILL.md §4 的展开：AgentCard 的注册来源与必填/可选字段全表。
> 字段以现行公开示例为准；`protocolVersion` 为公开示例 `0.3.0`。

## 注册来源（Source）

A2aAgent 的注册来源（Source）：**Runtime**（填 Runtime 地址）或 **Standard**（`ImportType=json` 导入 JSON 文件 / `ImportType=url` 填 AgentCard 地址，`SetDefaultVersion=true`）。


## 必填字段

| 字段 | 说明 |
|---|---|
| `version` | 语义化版本（如 `1.0.0`） |
| `name` | Agent 名称（≤64 字符，ASCII 可视字符） |
| `description` | 描述 |
| `protocolVersion` | 现行公开示例 `0.3.0` |
| `supportedInterfaces[].url` | HTTPS 服务地址 |
| `supportedInterfaces[].protocolBinding` | 取 `JSONRPC`（`GRPC`/`HTTP+JSON` 为旧版已废弃） |
| `defaultInputModes` | 如 `["text/plain","application/json","image/png"]` |
| `defaultOutputModes` | 同上 |
| `skills[]` | 每项含 `id` / `name` / `description` / `tags`（可选 `examples`/`inputModes`/`outputModes`） |

## 可选字段

`capabilities.streaming`、`capabilities.pushNotifications`、`capabilities.stateTransitionHistory`、`capabilities.extendedAgentCard`；`securitySchemes`（API Key / OAuth2；API Key 可配 `in: query|header`）与 `securityRequirements`；`iconUrl`、`documentationUrl`、`provider.organization`/`url`、`tenant`、`capabilities.extensions`。


最小可导入 JSON 示例见 SKILL.md §11 来源追溯对应行（ArkClaw 企业版 Agent 手册）。
