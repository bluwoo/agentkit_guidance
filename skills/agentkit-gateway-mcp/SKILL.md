---
name: agentkit-gateway-mcp
description: AgentKit 网关 / MCP——Agent 访问后端工具的统一入口，承担认证、路由、协议转换、访问治理。支持 MCP 服务四种接入方式（部署 veFaaS / REST转MCP / 接入已有 MCP Server / 私网域名）、MCP 工具集语义检索、模型服务代理、凭据安全托管。当需要将 HTTP API 或 MCP Server 接入 AgentKit、创建 MCP 工具集、配置网关凭据、或调试 Agent 工具调用时使用本 Skill。
---

# AgentKit 网关 / MCP Skill

## 1. 概述

网关是 Agent 访问后端工具的统一入口，承担**认证、路由、协议转换、访问治理**。它把外部 HTTP API、MCP 服务、MCP 工具集包装成 Agent 可调用的 MCP 工具，在入口处统一做入站认证、出站凭据注入、审计与权限控制。支持共享网关（POC/低流量）和专属网关（生产环境）两种形态。核心组件包括 MCP 服务（MCPService）、MCP 工具集（MCPToolset）和模型服务代理。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已注册火山引擎账号并开通 AgentKit 服务
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] 后端服务可通过公网或私网访问（HTTP API 或已有 MCP Server）
- [ ] 已选择模型并获取方舟 API Key
- 依赖包：`agentkit-sdk-python`，`mcp`，`google-adk`
- 环境变量：`MCP_ENDPOINT`、`MCP_AUTH_KEY`、方舟 `API_KEY`

## 3. 快速上手

### 3.1 控制台操作路径

**接入已有 MCP Server：**
1. AgentKit 控制台 → 网关 → MCP 服务 → 创建 → 选择"接入已有 MCP Server"
2. 填写后端 MCP Server Endpoint（支持 Streamable HTTP）、认证方式
3. 网关生成 MCP 服务 Endpoint + ApiKey（Bearer Token）
4. 在 Runtime"关联组件"中选择该 MCP 服务/工具集

**REST API / OpenAPI 转 MCP：**
1. 准备后端 HTTP API 的 OpenAPI 3.x 规范文件（Swagger JSON）
2. 创建 MCP 服务 → 选择"HTTP 转 MCP" → 上传 OpenAPI 规范 → 指向上游 HTTP 服务
3. 网关自动生成 MCP 工具 schema，映射鉴权参数
4. 获取 MCP 访问方式与调用示例

**创建 MCP 工具集（语义检索）：**
1. 创建 MCP 工具集 → 添加多个 MCP 服务的工具
2. 开启"语义检索"（按用户意图动态选工具）
3. 在 Runtime 关联该工具集

### 3.2 SDK 代码集成

> Runner 入口通用骨架与签名（`runner.run` 非流式 / SSE `run_async`+`types.Content`+预建 session / inspect 验证脚本）统一见 [`../references/runner-entrypoint.md`](../references/runner-entrypoint.md)；本节只保留 MCP 工具集装配。

```python
# 【import 路径来源】MCPToolset / StreamableHTTPConnectionParams 来自 google-adk==2.2.0 官方导出
#   （路径见官方文档 IntegratingMCPinagents）；未在本仓库 test_imports.py 覆盖范围内，未做钉版 venv import 复测
# Runner.run(messages=) 签名见 ../references/runner-entrypoint.md §3（2026-09-18 results.json 84/84 通过）。
import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()

# 通过网关 Endpoint + 入站 Key 连接 MCP 工具集
mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=os.getenv("MCP_ENDPOINT"),
        headers={"Authorization": f"Bearer {os.getenv('MCP_AUTH_KEY')}"}
    )
)

agent = Agent(
    name="ecs_helper",
    model_name="<model-name>",
    instruction="你是云资源管理助手，需要操作云资源时调用 MCP 工具。",
    tools=[mcp_toolset]
)

runner = Runner(agent=agent)

# 非流式（推荐）：runner.run(messages=) 直接返回字符串；如需 SSE 流式见共享 reference §4。
@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result

app.run(host="0.0.0.0", port=8000)
```

### 3.3 验证 MCP 工具调用
```bash
# 【需云凭据联调】$MCP_ENDPOINT 需为已创建并 Ready 的 MCP 服务/工具集地址，未实测
# 验证 MCP 服务握手与工具列表
curl -X POST $MCP_ENDPOINT \
  -H "Authorization: Bearer $MCP_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 4. 核心概念与 API

| 概念 | 说明 | 关键参数 |
|---|---|---|
| MCPService | 把后端工具能力包装为 MCP 服务 | 四种接入方式：部署 veFaaS / REST转MCP / 接入已有 MCP Server / 私网域名 |
| MCPToolset | 聚合多个 MCP 服务的工具为一个工具集 | 支持语义检索（按意图动态选工具） |
| 入站认证 | 谁可访问 MCP 服务/工具集 | API Key（Bearer Token）或 OAuth JWT |
| 出站凭据 | Agent 调下游用什么凭据 | API Key Provider / OAuth Client(M2M) / User Federation(OBO) / IAM Role |
| 模型服务代理 | 网关层代理方舟模型 | Proxy API Key 维度 + 模型维度 Token 用量管控（2026-09-10） |

### MCP 服务四种接入方式

| 方式 | 说明 | 适用场景 |
|---|---|---|
| 部署 MCP 服务（veFaaS） | 函数服务模式部署，计 CPU/内存 | 新开发的 MCP 工具，无已有后端 |
| REST API / OpenAPI 转 MCP | 上传 OpenAPI 3.x 规范，网关自动转换 | 存量 HTTP API 快速接入，接入周期周级→3-5小时 |
| 接入已有 MCP Server | 填写后端 MCP Server 地址与认证，网关代理 | 已有 MCP Server 需统一治理 |
| 私网域名方式 | 私网域名接入调试（2026-09-10起） | 后端服务仅私网可达 |

### 语义检索优化效果

| 指标 | 全量拉取 | 渐进式（语义检索） | 改善 |
|---|---|---|---|
| Token 消耗 | 31,883 | 10,763 | 降 60%+ |
| 耗时 | 6000ms+ | 26ms | 大幅提升 |

> 语义检索工具索引计费：0.014 元/万个/小时。工具集应按业务域组合并开启语义检索。

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `MCP_ENDPOINT` | MCP 服务/工具集网关地址 | 是 |
| `MCP_AUTH_KEY` | 入站 ApiKey（Bearer Token） | 是 |
| `API_KEY` / `ARK_API_KEY` | 火山方舟模型 API Key | 是 |
| `VOLCENGINE_ACCESS_KEY` | 火山引擎访问密钥 | 是（控制台管理操作） |
| `VOLCENGINE_SECRET_KEY` | 火山引擎 secret 访问密钥 | 是（控制台管理操作） |

### MCP API 清单（Version 2025-10-30）

| 分类 | API |
|---|---|
| MCP 服务 | CreateMCPService / ListMCPServices / GetMCPService / UpdateMCPService / UpdateMCPTools / DeleteMCPService |
| MCP 工具集 | CreateMCPToolset / ListMCPToolsets / GetMCPToolset / UpdateMCPToolset / DeleteMCPToolset / ListMCPToolsetTools |
| 标签 | TagResources / UntagResources / ListTagsForResources |

## 5. 输入输出规范

### 输入
- `MCP_ENDPOINT`: `string` — 网关生成的 MCP 服务/工具集地址
- `Authorization: Bearer <MCP_AUTH_KEY>` — 入站认证 Header
- MCP 协议请求：JSON-RPC 2.0 格式（`tools/list`、`tools/call`）

### 输出
- `tools/list`：可用工具列表（含名称、描述、参数 schema）
- `tools/call`：工具执行结果
- 错误：MCP 标准错误码 + HTTP 状态码
- 四层验收：① initialize HTTP 状态 → ② tools/list 可见性 → ③ tools/call isError → ④ 后端真实执行

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit 网关管理权限（创建 MCP 服务/工具集）
- **入站认证（单服务二选一，互斥）**：
  - 每个 MCP 服务同时只能配置一种入站 AuthorizerType（`InboundAuthorizerConfiguration.AuthorizerType`）：
    - `ApiKey`：`Authorization: Bearer <mcp_api_key>` — 教学/服务间
    - `CustomJWT`（OAuth JWT）：`Authorization: Bearer <user_access_token>` — 生产用户身份
  - 二者在同一服务上**互斥**，不能同时启用；可通过「更新 MCP 入站身份认证」修改类型，但修改后旧入站凭证模型失效，需重新联调握手（企业内部「更新MCP入站身份认证」能力已商用）（来源：<internal-lark-doc>
- **出站凭据安全边界**：
  - 真实 API Key / OAuth Token / AK-SK 全部由 Gateway 出站凭据托管注入
  - 调用方只持 Proxy Key / 入站 API Key，不接触明文凭据
  - 出站注入 Header 不得与入站 `Authorization` 共用同一 Header
  - **严禁**在日志/Trace/错误体/MCP Result 中打印 Authorization/API Key/Token
- **网关架构**：基于 Envoy + Istio 构建，数据面 + 控制面
- **插件三层**：
  | 插件类型 | 原理 | 适用 |
  |---|---|---|
  | 内置 C++ filter | Envoy 原生 | 长期稳定基础能力（MCP 协议代理、日志跟踪） |
  | WASM 插件 | Envoy 内建 WebAssembly | 功能扩展主力（认证鉴权、路由、限流） |
  | 外置 Ext-process | 独立服务 | 独立能力、性能不敏感（意图识别、协议转换） |

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| MCP Service 一直 `Creating` | 后端函数未发布完 / APIG 域名路由慢 | 等待 2-5 分钟，查看详情和 `FailedLogFileUrl` |
| MCP Service 进入 `Error` | Swagger 未 Base64 编码 / Swagger 不规范 / 后端 TLS 未配 | 检查 OpenAPI 文件格式与编码；确认后端 TLS 配置 |
| 握手成功但工具报错 / `authenticated: false` | 入站已过，出站凭据注入位置不对 | 按序查：① Key 来自 `GetMCPService` 回读；② Provider metadata `Location=Header`、`ParameterName=<独立Header>`；③ `OutboundAuthorizerConfiguration` 回读 `AuthorizerType=Identity` |
| 无/错入站凭证 401 | 正常安全行为 | 确认 Bearer Token 来源正确（服务 Ready 后 `GetMCPService` 回读） |
| Agent 不调用工具 | instruction 不够明确 / MCP 工具名不对 | 先手动 `tools/list` 确认工具可见，再在 instruction 中明确调用要求 |
| 调用超时 | 后端服务慢 / 工具集过大 | 开启语义检索减少 Token；提升后端性能 |

排障路径：四层 MCP 验收（initialize → tools/list → tools/call → 后端执行）→ 网关日志 → 入站/出站配置回读 → 后端服务状态

## 8. 可执行验证办法

1. 创建 MCP 服务后，确认状态 Ready
2. 从 `GetMCPService` 回读获取有效入站 Key（仅内存使用）
3. 四层验收：
```bash
# ① initialize 握手（旧协议有状态握手路径；protocolVersion 取网关接受的旧版本之一即可）
# 网关旧协议当前接受：2025-11-25 / 2025-06-18 / 2025-03-26 / 2024-11-05；下面用最旧的 2024-11-05 作示例
# 【版本依赖】MCP 2026-07-28 新无状态协议不使用 initialize，见 §10 协议版本矩阵；老服务/HTTP转MCP 仍走本握手
curl -X POST $MCP_ENDPOINT \
  -H "Authorization: Bearer $MCP_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}'

# ② tools/list 确认工具可见
curl -X POST $MCP_ENDPOINT \
  -H "Authorization: Bearer $MCP_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# ③ tools/call 调用工具，确认 isError=false
curl -X POST $MCP_ENDPOINT \
  -H "Authorization: Bearer $MCP_AUTH_KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"<tool-name>","arguments":{}}}'
```
4. 负向测试：不带 Key / 错误 Key 均应返回 401
5. 在 Agent 中集成后调用，确认 Agent 自动选择并调用 MCP 工具

## 9. 与其他组件的关系

- **上游依赖**：火山 APIG（网关底座）、后端服务（HTTP API / MCP Server / veFaaS）、Identity（凭据托管）
- **下游联动**：Runtime（关联 MCP 工具集）、观测（工具调用 trace）、权限网关（Cedar 策略授权）
- **常见组合**：
  - Runtime + MCP 工具集 = Agent 可调用企业工具
  - MCP 工具集 + 语义检索 = 低成本大规模工具接入
  - 模型网关 + MCP 网关 = 完整 Agent 基础设施
  - Gateway + Identity + 权限网关 = 生产级安全 Agent 工具访问
- **计费独立**：Runtime 网关与 MCP 网关是两套独立实例，分别下单计费

## 10. 已知限制与注意事项

- **一个火山账号当前只能创建一个模型网关**（模型网关层面）
- **Agent Mesh / Agent Team 复杂任务协作仍为 POC**，非现网能力
- 入站 API Key 创建时只提交名称不提交值，服务 Ready 后通过 `GetMCPService` 回读才是有效值
- Allowed Clients 空列表 = 允许所有（不是默认拒绝），必须显式填写
- ID Token 不能当 MCP/Gateway Bearer，必须用 Access Token
- 公共 `agentkit-sdk-python 0.5.10` 不含完整认证模块，完整功能需 `0.6.2`+
- 运行时明文凭据会出现在内存中，严禁日志/Trace/错误体回显
- MCP 协议支持 Streamable HTTP 传输；**协议版本矩阵（企业文档核证 2026-09-22）**：
  - 旧有状态握手路径接受 `protocolVersion` ∈ {2025-11-25, 2025-06-18, 2025-03-26, 2024-11-05}，版本不匹配会报 "unsupported protocolVersion ... supported versions:..."（来源：<internal-lark-doc>
  - **MCP 2026-07-28 新无状态协议**（去掉 initialize 握手、改用 streamable HTTP 无状态调用）：
    - MCP 工具集：**已全面兼容新旧协议所有场景（含存量实例）**
    - MCP 服务部署/导入：**存量实例不支持，新实例可支持**
    - HTTP 转 MCP：**尚不支持 2026-07-28，仅支持旧协议**
    - ReleaseNote v26.09.17（2026-09-18）起新增 2026-07-28 兼容支持；截至 2026-09-21 该 P0 能力仍在开发推进中，对外展示与灰度名单以控制台为准（来源：<internal-lark-doc>
  - 仍待确认：存量 MCP 服务实例的老协议→2026-07-28 迁移工具/迁移 SOP 企业文档未闭环，勿断言存量实例可一键升级
- 存量应用 API → MCP 接入周期从周级降至 3-5 小时级

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 网关概念与两种形态 | https://docs.volcengine.com/docs/AgentKit/Gatewayoverview?lang=zh | 网关概述 |
| MCP 服务四种接入方式 | https://docs.volcengine.com/docs/AgentKit/Gatewayoverview?lang=zh | 网关概述（MCPService） |
| 接入已有 MCP Server 步骤 | https://docs.volcengine.com/docs/AgentKit/connect-existing-mcp-server-to-agentkit-gateway?lang=zh | 接入已有 MCP Server |
| REST/OpenAPI 转 MCP | https://docs.volcengine.com/docs/AgentKit/connect-existing-rest-api-or-openapi-to-mcp-tool?lang=zh | REST API 转 MCP 工具 |
| SDK MCPToolset 集成代码 | https://docs.volcengine.com/docs/AgentKit/IntegratingMCPinagents?lang=zh | 在 Agent 中集成 MCP |
| MCP 协议版本兼容性 | https://docs.volcengine.com/docs/AgentKit/MCPprotocolversioncompatibilityinstructions?lang=zh | MCP 协议版本兼容说明 |
| 计费计数规则 | https://docs.volcengine.com/docs/AgentKit/gateway_mode_and_mcp_request_counting_rules?lang=zh | 网关与 MCP 请求计数规则 |
| 凭据安全边界与四层验收 | <internal-lark-doc> | AgentKit Gateway + Identity 新手入门操作（0714） |
| 语义检索 token 优化（31883→10763） | <internal-lark-doc> | AgentKit Gateway：从内部基建到企业场景（MCP Tool Search） |
| Envoy+Istio 架构与插件三层 | <internal-lark-doc> | AgentKit Gateway：从内部基建到企业场景（架构概览） |
| 一个账号一个模型网关限制 | <internal-lark-doc> | AgentKit Gateway：从内部基建到企业场景（局限说明） |
| MCP API 清单 | https://docs.volcengine.com/docs/AgentKit/Gatewayoverview?lang=zh | API 参考 |
| MCP 2026-07-28 新协议 + 新旧兼容矩阵 + 入站认证可更新（核证 2026-09-22） | <internal-lark-doc> | AgentKit 网关 ReleaseNote & 功能列表 |
| MCP 0728 无状态协议含义与旧握手版本集（核证 2026-09-22） | <internal-lark-doc> | MCP 网关（0714） |
| MCP 0728 P0 开发进度（截至 2026-09-21） | <internal-lark-doc> | AgentKit 0921 文档建设项目 |
