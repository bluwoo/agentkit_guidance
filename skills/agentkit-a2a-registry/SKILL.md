---
name: agentkit-a2a-registry
description: AgentKit A2A 中心（Registry）——基于 Google A2A 协议的智能体注册与发现中心。当需要创建智能体空间、注册 Runtime Agent 或外部 Agent、通过语义检索发现其他 Agent、配置 Provider/Consumer 跨 Agent 协作时使用本 Skill。
---

# AgentKit A2A 中心 (Registry) Skill

## 1. 概述

A2A（Agent-to-Agent）是 Google 提出的开放协议，实现不同框架/供应商 Agent 间互通协作。**A2A 中心（Registry）** 统一管理平台内外 A2A Agent 通信，基于底层网关提供标准 A2A 协议的同步/异步通信能力。核心价值：Agent 资产统一注册与治理，一次注册处处可发现，支持语义检索自动识别调用意图，跨团队/平台/网络协作。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已注册火山引擎账号并开通 AgentKit 服务
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] 已有至少一个可调用的 Runtime Agent（Provider 侧）
- [ ] AgentKit CLI 已安装（TypeScript 版）
- 依赖包：`agentkit-cli`，`veadk-python==1.1.13`
- 环境变量：`VOLCENGINE_REGION=cn-beijing`

## 3. 快速上手

### 3.1 控制台操作路径

1. **A2A 中心 → 创建智能体空间（A2aSpace）** → 开启/关闭语义检索 → 添加标签（最多 20 个）
2. **注册智能体（A2aAgent）** → 选择"智能体运行时来源"一键注册 Runtime Agent，或导入 JSON 文件/填写 AgentCard 地址注册外部 Agent
3. **版本管理** → 管理智能体版本，查看/更新 Agent JSON 与 AgentCard 地址
4. **发现与调用** → 在同空间内通过语义检索或标签筛选发现目标 Agent，A2A Client 基于 AgentCard 动态发现并通信

### 3.2 Provider 端：创建 A2A Agent（CLI）

> **⚠️ CLI 版本前提（2026-09-28 基准验收补充）**：本节 `agentkit init --template a2a / config / launch / invoke --a2a` 与 §3.3 的 `agentkit init --template harness / add harness / deploy / invoke harness` 均来自内部操作文档，**未在公开 `agentkit-cli` 上实测**。当前公开 CLI 0.52.13 的 Skill 子命令仅支持只读（list/get）+ upload/delete（见 `agentkit-skills` Skill §3.2），不保证暴露上述 a2a/harness 子命令。照抄前先执行 `agentkit --version` 与 `agentkit --help` 确认子命令存在；若版本不支持，改走 §3.4「Runtime 控制台勾选注册到 A2A 空间」这条已验证路径，或用 §3.5 的 VeADK A2A SDK 代码方式。

```bash
# 【需云凭据联调】以下 CLI 来自内部操作文档，未在本环境实测（本阶段未执行云联调，火山引擎凭据可用性尚未核验）
# ⚠️ 端点注意：AgentKit 控制面 OpenAPI 为 agentkit.<region>.volcengineapi.com；
#    下方示例的 --registry-endpoint 来自内部文档，未在官方 API 分片中核验，以控制台/实测为准。
# 创建 Provider Agent 模板（A2A 模板）
agentkit init weather_agent \
  --template a2a \
  --model-name "${MODEL_AGENT_MODEL:-demo-model}" \
  --tools web_search

# 配置部署
agentkit config weather_agent \
  --launch_type cloud \
  --cloud_provider volcengine \
  --region cn-beijing \
  --runtime_name weather-agent \
  --runtime_auth_type key_auth

# 环境变量
export VOLCENGINE_ACCESS_KEY="${VOLCENGINE_ACCESS_KEY:?set-ak}"
export VOLCENGINE_SECRET_KEY="${VOLCENGINE_SECRET_KEY:?set-sk}"
export VOLCENGINE_REGION=cn-beijing
export MODEL_AGENT_NAME="${MODEL_AGENT_MODEL:-demo-model}"
export MODEL_API_KEY="${MODEL_API_KEY:?set-key}"
export MODEL_ENDPOINT="https://ark.${VOLCENGINE_REGION:?set-region}.volces.com/api/v3"

# 部署并验证
agentkit launch
agentkit status --verbose
agentkit invoke --runtime-id "${RUNTIME_ID:?set-runtime-id}" --a2a "北京天气怎么样？"
```

### 3.3 Consumer 端：Harness 注册到 A2A Registry（CLI）
```bash
# 【需云凭据联调】以下 harness/registry CLI 来自内部操作文档，未在本环境实测
# 创建 Harness Consumer Agent
agentkit init travel_harness --template harness

# 添加 harness 并指定 A2A Registry 端点
agentkit add harness --name travel_harness \
  --runtime adk \
  --short-term-memory-type local \
  --model-name "${MODEL_AGENT_MODEL:-demo-model}" \
  --system-prompt "你是旅行规划助手，需要天气信息时自动调用空间内的天气 Agent。" \
  --registry-region cn-beijing \
  --registry-endpoint "https://${REGISTRY_ENDPOINT:?set-registry}/"

# 部署 Consumer
agentkit deploy --harness travel_harness --region cn-beijing

# 调用 Consumer，它会自动搜索并调用 Provider Agent
agentkit invoke harness travel_harness "帮我规划一个去北京的三天旅行行程"
```

### 3.4 Runtime 一键注册到 A2A 空间

在创建/编辑 Runtime 时，勾选"注册到 A2A 空间"并选择目标空间。注册地址随网络访问方式自动选公网/私网。注册完成后自动生成 AgentCard（含版本、技能如 `chat`），对外经 `/.well-known/agent-card.json` 暴露；`protocolVersion` 按现行公开示例 0.3.0 生成。

### 3.5 Provider 端：正式 VeADK A2A SDK 代码（不要自创 HTTP server）

Provider Agent 的容器内应使用 **`veadk.a2a.ve_a2a_server.init_app()`** 创建标准 FastAPI 应用，而非手写 `do_GET` / `message/status` 等 HTTP handler。init_app 自动注册：
- `GET /.well-known/agent-card.json` → 标准 AgentCard JSON
- `POST /` → A2A JSON-RPC 2.0（`message/send` / `tasks/get` / `initialize`）

```python
# server.py —— Provider 容器内 A2A server（正式 SDK 用法）
import os
from veadk import Agent, Runner
from veadk.a2a.ve_a2a_server import init_app
from veadk.memory.short_term_memory import ShortTermMemory, InMemorySessionService

agent = Agent(
    name="my_a2a_provider",
    instruction="你是一个A2A测试Provider。",
    model_name=os.getenv("MODEL_AGENT_MODEL", "<model-name>"),
)

# 生产环境用 DatabaseSessionService，测试用 InMemorySessionService
stm = ShortTermMemory(session_service=InMemorySessionService())

# 正式 SDK：一行创建标准 A2A FastAPI app
app = init_app(
    server_url=os.getenv("A2A_SERVER_URL", "http://localhost:8000"),
    app_name="my_a2a_app",
    agent=agent,
    short_term_memory=stm,
)


class _GatewayPathRewrite:
    """AgentKit 网关对 Runtime-source A2A 注册会重复 /runtime/<id> 路径前缀。
    A2A JSON-RPC 处理器只挂在 POST / 上，因此对所有 POST 请求在路由前把 path
    重写为 /；GET（agent-card）保持原样。容器侧必须加此中间件。"""
    def __init__(self, inner):
        self.inner = inner
    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("method") == "POST":
            scope = dict(scope)
            scope["path"] = "/"
            scope["raw_path"] = b"/"
        await self.inner(scope, receive, send)

app = _GatewayPathRewrite(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

本地验证：`GET /.well-known/agent-card.json` 返回含 `name`/`version`/`protocolVersion`/`skills` 的 AgentCard；`POST /` 发 JSON-RPC `message/send` 返回标准 `{jsonrpc:"2.0", id, result|error}`。参考实现见 `reference-agents/a2a-test-server/server.py`。

## 4. 核心概念与 API

| 概念 | 说明 | 关键参数 |
|---|---|---|
| A2aSpace（智能体空间） | Agent 注册与发现的逻辑容器 | 可开启语义检索、最多 20 个标签 |
| A2aAgent（注册智能体） | 注册到空间的 Agent 实例 | 来源：Runtime 一键注册 / JSON 文件导入 / AgentCard 地址 |
| AgentCard | A2A 协议标准的 Agent 描述文件（JSON） | 字段见下方《AgentCard 字段规范》；注册后经 `/.well-known/agent-card.json` 暴露 |
| A2aAgentVersion | 智能体版本管理 | 多版本并存，可查看/更新/删除 |
| SearchAgentCards | 语义检索 API | 按意图自动语义索引，匹配候选 Agent |

### Provider / Consumer 模式

| 角色 | 模板 | 关键 CLI 参数 |
|---|---|---|
| Provider（提供能力的 Agent） | `--template a2a` | `--model-name`、`--tools`、部署为 Runtime |
| Consumer（调用其他 Agent 的 Agent） | `--template harness` | `--registry-region`、`--registry-endpoint`、`--registry-space-id/name`、`--registry-top-k` |

### AgentCard 字段规范（以公开示例为准）

注册来源（Source）：**Runtime**（填 Runtime 地址）或 **Standard**（`ImportType=json` 导入 JSON / `ImportType=url` 填 AgentCard 地址，`SetDefaultVersion=true`）。AgentCard 遵循 Google A2A 协议，现行公开文档示例 `protocolVersion` 为 **0.3.0**；`protocolBinding` 取 `JSONRPC`（`GRPC`/`HTTP+JSON` 已废弃）；运行期消息方法为 `message/send`（JSON-RPC）。

> 必填字段（version/name/description/protocolVersion/supportedInterfaces[].url/protocolBinding/defaultInputModes/defaultOutputModes/skills[]）与可选字段（capabilities.*/securitySchemes/securityRequirements/iconUrl 等）的完整清单与示例，见 [references/agentcard-schema.md](references/agentcard-schema.md)（以公开示例为准，含来源 URL）。最小可导入 JSON 示例见 §11 来源追溯。

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `VOLCENGINE_ACCESS_KEY` | 火山引擎访问密钥 ID | 是 |
| `VOLCENGINE_SECRET_KEY` | 火山引擎 secret 访问密钥 | 是 |
| `VOLCENGINE_REGION` | 地域（cn-beijing） | 是 |
| `MODEL_AGENT_NAME` | 模型名称 | 是 |
| `MODEL_API_KEY` | 模型 API Key | 是 |
| `MODEL_ENDPOINT` | 模型接入点（方舟） | 是 |

### A2A API 清单（Version 2025-10-30）

| 分类 | API |
|---|---|
| 空间管理 | CreateA2aSpace / UpdateA2aSpace / ListA2aSpaces / GetA2aSpace / DeleteA2aSpace |
| 智能体注册 | CreateA2aAgent / UpdateA2aAgent / ListA2aAgents / GetA2aAgent / DeleteA2aAgent |
| 版本管理 | ListA2aAgentVersions / GetA2aAgentVersion / DeleteA2aAgentVersion |
| 语义检索 | SearchAgentCards |

## 5. 输入输出规范

### 输入（Consumer 调用 Provider）
- Consumer 请求：`prompt`（用户自然语言任务描述）
- Registry 检索：Agent 意图 → 语义匹配 AgentCard → 返回候选 Agent 列表
- A2A 协议通信：Consumer 基于 AgentCard 地址直接调用 Provider

### 输出
- Provider Agent 响应：A2A 协议标准格式
- Consumer 聚合回答：`string` — 整合多个 Provider 结果后的自然语言回答
- SearchAgentCards 输出：匹配的 AgentCard 列表（含评分）

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit A2A 管理权限（空间创建/智能体注册/版本管理）
- **入站认证**：Runtime 网关认证（API Key / SSO），A2A 通信走网关
- **出站凭据**：通过网关注入，Agent 间通信由网关统一认证
- **AgentCard 安全**：AgentCard 包含服务地址与认证信息，注册时需控制空间可见范围
- **网络安全**：公私网服务地址可变更，注册地址随 Runtime 网络方式自动选择

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| Consumer 找不到 Provider | 双方未注册到同一 A2aSpace / 空间名错误 | 确认 Provider 和 Consumer 都注册到同一空间；检查 `--registry-space-id/name` |
| 语义检索无结果 | 空间未开启语义检索 / Provider 描述不清晰 | 在空间设置中开启"智能体语义检索"；完善 Provider 的 AgentCard 描述与技能标签 |
| A2A 调用超时 | Provider Runtime 未就绪 / 网络不通 | 检查 Provider Runtime 状态（`agentkit status --verbose`）；确认公私网地址匹配 |
| 注册失败 | Runtime 未发布 / 未配置网络访问 | 确认 Runtime 已 Release 成功；配置公网或私网访问 |
| AgentCard 地址错误 | 公私网切换后地址未更新 | 更新 A2aAgent 的 AgentCard 地址，支持公私网服务地址变更 |

排障路径：Consumer 日志确认检索结果 → A2A 空间控制台查看注册列表 → Provider Runtime 状态检查 → 网络连通性验证

## 8. 可执行验证办法

1. 创建 A2aSpace 并开启语义检索
2. 部署 Provider Runtime 并注册到空间，确认控制台可见且 AgentCard 自动生成
3. 部署 Consumer Harness 并指向同一 Registry 端点
4. 调用 Consumer，确认自动发现并调用 Provider：
```bash
agentkit invoke harness travel_harness "帮我查一下北京今天的天气"
```
5. 在 Provider 日志中确认收到来自 Consumer 的调用（调用方标识可见）
6. 调用 `SearchAgentCards` API 验证语义检索返回正确候选

## 9. 与其他组件的关系

- **上游依赖**：Runtime（Provider Agent 部署）、Gateway（A2A 协议通信通道）
- **下游联动**：Agent 协作（多 Agent 任务拆解与聚合）、观测（跨 Agent 调用 trace）
- **常见组合**：
  - Provider Runtime + A2A 空间 + Consumer Harness = 多 Agent 协作
  - Runtime 创建时勾选"注册到 A2A 空间" = 一键发布 Agent 能力
  - A2A Registry + Gateway = Agent Mesh（POC 阶段）

## 10. 已知限制与注意事项

- **一个火山账号当前只能创建一个模型网关**（模型网关层面限制，非 A2A 空间限制）
- **Agent Mesh / Agent Team 复杂任务协作（任务拆解/交接/状态跟踪/结果聚合）仍为 POC 阶段，非现网能力**
- **Runtime-source Agent 的 AgentCard URL 重复路径问题**：通过"注册到 A2A 空间"一键注册 Runtime Agent 时，网关注册的 AgentCard URL 可能带重复 `/runtime/<id>` 前缀，导致 Consumer 调用时 POST 路径与容器内 A2A JSON-RPC handler（仅挂在 `/`）不匹配。容器侧必须加 `_GatewayPathRewrite` ASGI 中间件，对所有 POST 请求在路由前把 path 重写为 `/`（见 §3.5 代码示例）。GET agent-card 不受影响。
- **Provider 端必须用正式 SDK `veadk.a2a.ve_a2a_server.init_app()`**，不要自创 `do_GET` / `message/status` HTTP handler——非标准实现无法通过 A2A Registry 的 AgentCard 发现与 JSON-RPC 协议校验。
- A2A 智能体 JSON 文件 schema 见 §《AgentCard 字段规范》（以公开示例为准；`protocolVersion` 以现行公开示例 0.3.0 为准，`protocolBinding` 用 `JSONRPC`）
- 空间最多支持 20 个标签
- 语义检索效果依赖 AgentCard 描述与技能标签质量
- ArkClaw 企业版应用中心注册后，用户可通过自然语言/@ 命令调用已注册的 Agent

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| A2A 中心概念与两大能力 | https://docs.volcengine.com/docs/AgentKit/A2ACenteroverview?lang=zh | A2A 中心概述 |
| 操作流程（创建空间→注册→版本管理→注销） | https://docs.volcengine.com/docs/AgentKit/quick-access-a2a-center?lang=zh | 快速接入 A2A 中心 |
| Runtime 一键注册到 A2A 空间 | https://docs.volcengine.com/docs/AgentKit/quick-access-a2a-center?lang=zh | 快速接入 A2A 中心 |
| A2A API 清单 | https://docs.volcengine.com/docs/AgentKit/A2ACenteroverview?lang=zh | API 参考 |


---

## 措辞与契约修正记录（2026-09-18）

- §3.2 注释「（无云凭据）」改为「（本阶段未执行云联调，火山引擎凭据可用性尚未核验）」。
