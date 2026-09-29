---
name: agentkit-identity-permission
description: AgentKit 身份与权限平台——覆盖 User→Agent→Tool 全链路身份认证、权限控制与凭据管理。当需要为 Agent 配置入站登录（快速登录/企业SSO OIDC-SAML）、出站授权（IAM角色级联委托/OAuth令牌托管/AK-SK托管）、Cedar策略权限网关、或托管下游凭据时使用本 Skill。生产环境 Agent 上线前必须配置。
---

# AgentKit 身份与权限 (Identity & Permission) Skill

## 1. 概述

身份与权限平台是 AgentKit 的一站式身份及权限管理中心，解决 **User → Agent → Tool** 全链路的身份认证、权限控制与凭据管理问题。它由四大职责组成：**入站认证（Inbound AuthN）** 验证"谁可以访问 Agent"、**权限网关 + Cedar 策略（Permission Gateway + Cedar AuthZ）** 授权"谁能通过哪个 Agent 操作什么资源"、**身份凭据托管（Credential Provider / PassVault）** 安全存储下游密钥、**网关出站注入（Outbound Injection）** 在调用后端时受控注入凭据。这四职责互不替代，生产环境必须分离设计。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已开通 AgentKit 身份权限平台（控制台 → 身份与权限 → 开通）
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`（建议用短期 STS，不要把长期控制面 AK/SK 交给 Agent Runtime）
- [ ] 已创建 AgentKit Runtime 并发布
- [ ] 如需企业 SSO：已准备企业 IdP 的 OIDC/SAML 元数据
- 依赖包版本（**两层钉版，勿混用；新项目默认用第一行**）：
  - **【默认/推荐】离线导入基线（本仓库统一）**：`agentkit-sdk-python==0.8.7` + `veadk-python==1.1.13` + `google-adk==2.2.0` + Python 3.12–3.13 + `mcp==1.26.0`；下方 §3.3 两个 import 在此版本 import PASS
  - **【仅历史教学复现，不要用于新项目】** 0714 教学 E2E 钉版（已云端实测验收 2026-07-16）：`agentkit-sdk-python==0.6.2`（内部 commit `<git-sha-prefix>`）+ Python 3.10.19 + `mcp==1.28.1`
  - 公开 `agentkit-sdk-python 0.5.10` 不含完整认证模块，不能回退使用
- CLI 版本：`agentkit-cli==0.52.5`（钉版；无内部仓库权限时应停止，不能退回公开包）
- 环境变量：`VOLCENGINE_REGION=cn-beijing`（已公测地域为华北2/北京、华东2/上海）

## 3. 快速上手

### 3.1 控制台操作路径

AgentKit 控制台 → 身份与权限 → 以下子模块：
- **用户池（UserPool）**：创建用户池 → 记录 UserPoolUid → 配置登录方式（本地用户名密码 / 企业 SSO / 外部 OIDC Connection）
- **客户端（Client）**：创建 OAuth Client → 配置回调地址（浏览器用授权码、CLI 用 Device Flow Native Client、已有上游 Token 用 Token Exchange）
- **外部身份提供商（IdP）**：添加 OIDC/SAML 配置
- **权限策略（Policy）**：创建权限空间 → 定义资源类型与 Action → 编写 Cedar 策略 → ENABLE 并校验
- **权限网关（Permission Gateway）**：创建 Service → 绑定后端连接与 PermissionSpaceId → 配置 Route（Method/Path/Priority）→ APISpec 配置 IdentifierType/ActionType → 发布
- **凭据（Credential）**：创建 Credential Provider（API Key / OAuth Client / IAM Role）→ 配置注入位置元数据

### 3.2 CLI 登录与身份验证

```bash
# 【需云凭据联调】钉版 CLI 命令来自内部操作手册，未在本环境实测
# 安装钉版 CLI
curl -fsSL "https://agentkit-cli.tos.${VOLCENGINE_REGION:?set-region}.volces.com/install.sh" -o /tmp/agentkit-install.sh
AGENTKIT_VERSION=0.52.5 sh /tmp/agentkit-install.sh
agentkit --version  # 必须输出 0.52.5

# 仅登录身份（不启动 Agent）
agentkit login "https://agentkit.${VOLCENGINE_REGION:?set-region}.volces.com/${AGENTKIT_PROJECT:?set-project}" --identity-only

# 与共享 Agent 对话
agentkit chat "${AGENTKIT_PROJECT:?set-project}-agent"

# 查看登录后的 token 文件
cat ~/.agentkit/auth/sessions/agentkit.${VOLCENGINE_REGION:?set-region}.volces.com-${AGENTKIT_PROJECT:?set-project}.json

# 多用户身份隔离演示
# alice
cat ~/.agentkit-demo/user-a/auth/sessions/agentkit.${VOLCENGINE_REGION:?set-region}.volces.com-${AGENTKIT_PROJECT:?set-project}.json
# bob
cat ~/.agentkit-demo/user-b/auth/sessions/agentkit.${VOLCENGINE_REGION:?set-region}.volces.com-${AGENTKIT_PROJECT:?set-project}.json
```

### 3.3 代码集成（SDK 端身份凭据）

```python
# 【离线核验通过 2026-09-22（钉版 venv 复测仍 PASS）】以下 import 在 agentkit-sdk-python 0.8.7 中可导入：
#   from agentkit.auth._openapi import OpenApiClient  → PASS
#   from agentkit.sdk.mcp.client import AgentkitMCPClient → PASS
# 注意：agentkit.auth._openapi / agentkit.sdk.mcp.client 为下划线私有模块，非公开稳定 API，
# 仅用于诊断/联调时回读配置；生产代码应优先走控制台配置 + 网关出站注入，不要依赖私有 import。
# 复测环境：Python 3.13.7, agentkit-sdk-python 0.8.7, mcp 1.26.0
from agentkit.auth._openapi import OpenApiClient
from agentkit.sdk.mcp.client import AgentkitMCPClient

# 入站调用：从 GetMCPService 回读的有效 Key（创建时只提交名称，不提交值）
# 回读值仅在内存使用，禁止输出到日志/Trace
inbound_key = "从 GetMCPService 回读的有效值"
client = AgentkitMCPClient(
    endpoint="https://<mcp-service-domain>",
    headers={"Authorization": f"Bearer {inbound_key}"}
)

# 列工具 / 调工具（await 须在 async 函数内）
async def call_mcp_tool():
    await client.initialize()
    tools = await client.list_tools()
    result = await client.call_tool("check_agentkit_outbound_identity", {})
    return result
```

### 3.4 配置文件（agentkit.yaml 身份相关）

```yaml
launch_types:
  cloud:
    runtime_envs:
      # 入站认证：由控制台配置，代码侧不硬编码
      # 出站凭据：由 Identity Credential Provider 托管，代码侧不硬编码下游密钥
      AGENTKIT_TOOL_ID: "<平台工具标识>"
```

## 4. 核心概念与 API

### 4.1 组件清单

| 组件 | 说明 | 关键参数 |
|---|---|---|
| **UserPool（用户池）** | 管理真实用户登录、JWT 签发、SSO 对接的边界 | UserPoolUid, issuer |
| **Client（客户端）** | OAuth 客户端，为 Web/App/Agent 前端发令牌 | ClientID, redirect_uri, 授权类型（Authorization Code / Device Flow / Token Exchange） |
| **User（用户）** | 用户池内的具体用户实体 | 用户名/密码/SSO 映射 |
| **IdP（外部身份提供商）** | 对接企业 OIDC/SAML IdP | OIDC discovery URL / SAML metadata |
| **Policy（权限策略）** | Cedar 策略，细粒度控制 Agent/MCP服务/Skill/知识库文档级访问 | Subject, Action, Resource, Context, References, OriginalCallers |
| **Permission Gateway（权限网关）** | 策略执行点（PEP），拦截请求交 Cedar 判定 | PermissionSpaceId, Route(Method/Path/Priority), APISpec |
| **Credential（凭据）** | 托管 AK/SK/OAuth 凭据的 Provider | ProviderType(ApiKey/OAuthClient/IAMRole), Location(Header/Query), ParameterName, Prefix |
| **WorkloadPool** | Agent/工作负载身份的管理边界 | 信任关系、令牌签发范围 |
| **WorkloadIdentity** | 具体 Agent/App/Service 的可鉴权 principal | 绑定 WorkloadPool |

### 4.2 入站认证方式

| 方式 | 场景 | 请求头 |
|---|---|---|
| API Key | 教学、内部系统、Agent 调工具 | `Authorization: Bearer <mcp_api_key>` |
| OAuth JWT（User Access Token） | 用户登录后访问、生产用户身份 | `Authorization: Bearer <user_access_token>` |

### 4.3 出站认证方式

| 方式 | 场景 |
|---|---|
| API Key Credential Provider | 后端用固定 API Key |
| OAuth Client / M2M | 后端用 OAuth Client Credentials |
| User Federation / OBO | Agent 代表当前用户访问第三方 |
| IAM Role（级联委托链） | Agent 访问火山内部资源，2026-06-19 新增级联委托链身份传递 |

### 4.4 关键 API

| API | 用途 |
|---|---|
| `CreateWorkloadPool` | 创建工作负载身份管理边界 |
| `CreateWorkloadIdentity` | 为具体 Agent/App 创建可鉴权 principal |
| `AddWorkloadMetaData` | 限制可信属性 |
| `GetWorkloadAccessToken` / `GetWorkloadAccessTokenForJWT` / `GetWorkloadAccessTokenForUserId` | 换取 Workload Access Token |
| `CreateMCPService` | 创建 MCP 服务（配 Inbound/Outbound Authorizer） |
| `GetMCPService` | 回读服务实际配置（含入站 Key 有效值） |
| `PublishService` / `PublishRoute` | 发布权限网关 Service 和 Route |

> ⚠️ 上表中 `CreateWorkloadPool` / `CreateWorkloadIdentity` / `AddWorkloadMetaData` / `GetWorkloadAccessToken*` 等 Workload 身份 API **未出现在 shard1/2/4 的官方 OpenAPI 字段分片中**（shard4 身份章节均为控制台操作页，非 OpenAPI），其字段以内部操作手册与线上回读为准，**勿当已公开的 OpenAPI 契约**。`CreateMCPService`/`GetMCPService` 已在 shard2 核验。

### 4.5 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `VOLCENGINE_ACCESS_KEY` | 火山账号 AK（建议短期 STS） | 是 |
| `VOLCENGINE_SECRET_KEY` | 火山账号 SK | 是 |
| `VOLCENGINE_SESSION_TOKEN` | STS Session Token（使用 STS 时必填） | 否 |
| `VOLCENGINE_REGION` | 部署地域 | 是（cn-beijing） |
| `AGENTKIT_TOOL_ID` | 平台工具标识，决定 sandbox 模式 | 否 |

## 5. 输入输出规范

### 入站请求（用户/Agent → Gateway）
- Header: `Authorization: Bearer <token>` — 入站凭证（API Key 或 User Access Token）
- MCP 握手阶段：`initialize` → `tools/list` → `tools/call` 四层必须分别断言

### 出站注入（Gateway → 后端 API）
- Gateway 从 Identity 取明文凭据，按 Provider metadata 注入：
  - `Location=Header`, `ParameterName=X-Backend-Api-Key`, `Prefix=""`
  - **不得与入站 `Authorization` 共用同一 Header**
- 后端只认 Gateway 注入的出站凭据；无凭据应返回 401

### Cedar 策略判定输入
- Subject: User + Workload Identity（Agent principal）
- Action: 工具操作（如 `read_finance_report`）
- Resource: 资源标识（如具体文档/API）
- Context: 请求上下文（风险、目的、审批状态）
- 输出：Allow / Deny（Deny → 403）

## 6. 权限与安全

- **所需 IAM 权限**：Identity 平台开通权限 + AgentKit 资源管理权限；建议用短期 STS，确保具备三类临时资源 Create/Get/List/Delete 权限
- **入站认证**：API Key（教学/服务间）或 OAuth JWT（生产用户）；生产必须用 UserPool + 企业 SSO
- **出站凭据**：AK/SK 托管（API Key Provider）、OAuth 令牌托管（OAuth Client / OBO）、IAM 角色级联委托
- **数据安全**：下游密钥不写 Agent 代码；长期敏感值不明文落库；运行时明文凭据只向受信任 Gateway/执行器返回；**严禁在终端/日志/Trace/错误体/MCP Result 打印 Authorization/API Key/Access Token/Refresh Token**
- **安全围栏兼容**：身份权限层与安全围栏（Guardrails）独立工作，可同时开启

### 安全验收矩阵（必须通过）

| # | 操作 | 期望结果 |
|---|---|---|
| 1 | CLI 裸调（无任何凭证） | 401 |
| 2 | 用过期 token 调用 | 401 |
| 3 | 有权限用户登录后调工具 | 200，返回预期业务结果 |
| 4 | 无权限用户调同样工具 | 能聊天，但调工具 403 |

### JWT 验收清单
验签、kid、iss、aud、exp、client 与目标 UserPool/Client 一致。以下情况都必须失败：无 Token、坏签名、未知 kid、过期、错 issuer、错 audience、错 client、其他 UserPool、ID Token 冒充 Bearer。

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| `agentkit auth admin doctor` 不通过 | AK/SK 未设或权限不足；Identity 未开通；APIG/VeFaaS/VPC 不可用 | 检查环境变量、确认账号权限、控制台开通授权 |
| MCP Service 一直 `Creating` | 后端函数未发布完；APIG 域名/路由慢；后端配置字段错 | 等 2-5 分钟、看详情、看 `FailedLogFileUrl`、确认后端 Ready/Running |
| MCP Service 进入 `Error` | HTTP→MCP Swagger 未 Base64 编码；Swagger 不合规；HTTPS 后端未配 TLS | 用 VeFaaS Function 后端规避 TLS 问题；检查 Swagger 规范 |
| CustomJWT 早期握手可达但无保护 | 误把"transport/initialize 可达"判为鉴权通过 | 四层分别断言：initialize HTTP 状态 → tools/list 可见性 → tools/call isError=false → 后端真实执行 |
| 握手成功但工具报错或 `authenticated: false` | 出站凭据/注入位置/后端校验不一致 | 按序查：入站 Key 来自 GetMCPService 回读 → Provider metadata Location/ParameterName/Prefix → OutboundAuthorizerConfiguration 回读 AuthorizerType=Identity → 后端只用出站 Header 校验 |
| 权限网关创建了但策略未生效 | 权限网关不是"创建即生效" | 必须：① 后端地址改指向网关域名 ② 配置资源映射并发布 ③ 封闭原后端直连 |
| 403 Denied | Cedar 策略拒绝 | 检查策略 Subject/Action/Resource/Context 映射是否正确 |

排障路径：观测大盘定位异常 → 下钻 Trace → TLS 日志 → 安全围栏攻击日志；身份问题额外检查 GetMCPService 回读配置。

## 8. 可执行验证办法

1. **裸调验证**：不带任何凭证调用 MCP Service，确认返回 401
2. **过期 token 验证**：使用过期的 User Access Token，确认返回 401
3. **有权限用户验证**：登录有权限用户，调用工具返回 200 且有预期业务结果
4. **无权限用户验证**：换一个无权限用户，确认能聊天但调工具返回 403

> 完整端到端验收脚本（交互式读入主账号/AK/SK/STS token，调 `agentkit_gateway_identity_e2e.py`）与严格预期输出（最后一行必须同时出现三个 true），见 [references/e2e-acceptance.md](references/e2e-acceptance.md)。
> 该脚本钉版环境：Python 3.10.19, agentkit-sdk-python 0.6.2, mcp 1.28.1（已云端验收 2026-07-16，见 doc06）；与本仓库离线导入基线（0.8.7 / Python 3.13.7）不同，二者不要混装。【需云凭据联调】本环境未实测。

## 9. 与其他组件的关系

- **上游依赖**：AgentKit Runtime（需先部署 Agent）、APIG（网关底座）、IAM
- **下游联动**：
  - **权限网关** → 拦截所有 Agent→Tool 调用，交 Cedar 判定
  - **Credential Provider** → 为 Gateway 出站注入提供密钥
  - **安全围栏（Guardrails）** → 与身份权限独立，可同时开启
- **常见组合**：
  - Runtime + 身份权限 + 网关 = 生产级安全 Agent
  - UserPool/SSO + Permission Gateway/Cedar + Credential Provider = 完整生产授权链
  - 入站 JWT + 出站 OBO = 用户代表型 Agent（Agent 代用户访问第三方资源）

## 10. 已知限制与注意事项

### 关键坑（必须注意）
- **API Key 入站 ≠ Workload Identity**：API Key 只证明共享凭证持有者，不会自动产生可鉴权的 Agent principal。生产需显式创建 Workload Identity。
- **Allowed Clients 空列表 = 允许所有**：不是默认拒绝。必须填实际 UserPool Client ID 并回读确认非空。
- **ID Token 不能当 Bearer**：ID Token 仅用于客户端确认登录，不得作为 MCP/Gateway 的 Authorization Bearer。使用 Access Token。
- **权限网关不是创建即生效**：必须同时完成 ① 后端改指向网关域名 ② 资源映射发布 ③ 封闭原后端直连。缺一即可能绕过授权。
- **入站 Key 创建时不要提交值**：创建 MCP Service 只提交 Key 名称，Ready 后从 `GetMCPService` 回读才是有效值。回读值仅内存使用。
- **出站注入 Header 不得与入站 Authorization 共用**：实测入站 Authorization 仍会到后端，不能当作凭据隔离。
- **Workload Access Token 接入 Gateway 的完整 issuer/JWKS/audience 配置当前手册未闭环**，需以线上接口和回读验证为准。

### 版本兼容性
- 公开 `agentkit-sdk-python 0.5.10` 不含完整认证模块，不能用于本组件
- **0714 教学 E2E 钉版**：内部 `agentkit-sdk-python==0.6.2`（commit `<git-sha>`，Python 3.10.19 / mcp 1.28.1），已云端端到端验收
- **当前离线导入基线**：`agentkit-sdk-python==0.8.7`（Python 3.13.7 / mcp 1.26.0），§3.3 两个 import 在此版本仍 PASS
- CLI 钉版：`agentkit-cli 0.52.5`
- 无内部仓库权限时应停止，不能退回公开包

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 身份与权限概述 | https://docs.volcengine.com/docs/AgentKit/Identityandpermission?lang=zh | 概述 |
| 出站授权（Agent代表用户访问火山资源） | https://docs.volcengine.com/docs/AgentKit/outbound-authorization-agent-represents-the-user-to-access-volcano-engine-resources?lang=zh | 出站授权 |
| 入站快速登录 | https://docs.volcengine.com/docs/AgentKit/2549763 | 入站快速登录 |
| 企业 SSO | https://docs.volcengine.com/docs/AgentKit/2549764 | 企业 SSO 联合登录 |
| 出站第三方资源 | https://docs.volcengine.com/docs/AgentKit/2549765 | 出站第三方资源 |
| 出站火山资源 | https://docs.volcengine.com/docs/AgentKit/2549766 | 出站火山资源 |
| 创建权限网关 | https://docs.volcengine.com/docs/AgentKit/2549776 | 创建权限网关 |
| 开通身份权限平台 | https://docs.volcengine.com/docs/AgentKit/2549762 | 开通身份权限平台 |
| 完整链路/坑/验收矩阵/钉版环境 | <internal-lark-doc> | doc06 全文 |
| CLI 安装/登录/验收矩阵 | <internal-lark-doc> | doc05 全文 |
| RBAC/ABAC/连接器权限模型 | <internal-lark-doc> | doc08 第4节 |
