# 01 产品简介与动态

> 来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]?lang=zh 入口页及各子页
> 最近更新：2026-09-18 阅读

## 1. 什么是 [PRODUCT]

**[PRODUCT]（智能体开发平台）** 是火山引擎推出的一站式 AI Agent 开发、部署、运行与治理平台。它把"写代码 → 部署 → 调用 → 观测 → 评测 → 治理"整条链路产品化，开发者无需自建基础设施即可企业级落地 Agent。

核心定位（来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Whatis[PRODUCT]?lang=zh）：
- **低门槛开发**：提供 [PRODUCT] Studio（可视化/自然语言搭建）、[PRODUCT] CLI、[PRODUCT] Python SDK（深度封装 [BASE-ADK]）三种方式。
- **一站式部署运行**：代码推送到镜像仓库后一键发布到"智能体运行时（Runtime）"，自动扩缩容、负载均衡、健康检查。
- **企业级治理**：内置网关、身份与权限、安全围栏、观测、评测、会话与记忆、知识库、Skills、A2A Registry、沙箱等组件。

## 2. 产品功能全景

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Productfeatures-18?lang=zh

| 能力域 | 组件 | 说明 |
|---|---|---|
| 开发 | [PRODUCT] Studio / CLI / Python SDK / [BASE-ADK] | 可视化搭建、命令行工程化、装饰器式 SDK、多语言 ADK |
| 部署运行 | 智能体运行时 Runtime | 托管 Agent 服务实例，支持镜像/模型/环境变量/A2A 空间/关联组件/IAM 角色更新 |
| 工具执行 | 沙箱模板 Sandbox | 代码/浏览器/预置 Skill 执行的隔离环境；5 种预置模板 |
| 工具生态 | Skills / Skills 中心 | Skill 构建、调试、评估、注册；Skills 空间版本管理 |
| 多智能体 | A2A 中心 (Registry) | A2A 智能体注册、发现、语义检索、版本管理 |
| 上下文 | 会话管理 / 记忆库 | 短期会话（PostgreSQL/Serverless PG）+ 长期记忆（mem0/Viking 记忆库）|
| 知识 | 知识库 (VikingDB RAG) | 文档切片、语义检索、知识问答 |
| 接入 | 网关 / MCP | REST/OpenAPI 转 MCP、已有 MCP Server 接入、MCP 工具集、模型服务 |
| 安全 | 身份与权限 / 安全围栏 | User→Agent→Tool 全链路 IAM/OAuth/JWT；提示词攻击/敏感数据/算力消耗防护 |
| 运维 | 观测 / 日志 | APMPlus 指标链路 + TLS 日志 |
| 质量 | 评测 | 评测集、评估器、评测实验、会话分析、评估打标 |
| 合规 | IAM 访问控制 / 标签 / 项目 | 资源级权限与成本分摊 |

## 3. 应用场景

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Applicablescenarios-8?lang=zh
- 智能客服/知识问答（RAG 知识库 + 会话记忆）
- 企业办公自动化（日程、文档、审批，ArkClaw/[BASE-AGENT] 沙箱）
- AI 编码助手（Code Sandbox + Codex CLI，代码生成/调试/测试）
- 多智能体协作（A2A Registry + CreateAgentToolset 动态子 Agent 委派）
- 业务工具集成（MCP 网关把 REST API / 已有 MCP Server 统一暴露给 Agent）

## 4. 使用限制（关键配额）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Limits-7?lang=zh
- 开服地域：仅 **华北2（北京）cn-beijing**、**华东2（上海）cn-shanghai**（来源：Availableregions）
- 单账号单地域运行时数量上限 **20**；单运行时实例数上限 **20**（2026-03-06 起，见新功能记录）
- 运行时实例最低规格 **0.5 vCPU**（2026-08-21 起）
- 资源创建后**不支持更换地域**；地域间内网完全隔离
- Python 版本要求 **≥3.10**（SDK 文档要求，推荐 3.12）

## 5. 相关云产品（依赖生态）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Relatedcloudproduct-2?lang=zh
- **火山方舟 Ark**：模型推理（豆包系列），API Key 鉴权
- **函数服务 veFaaS**：Runtime / MCP 服务的 Serverless 承载
- **镜像仓库 CR**：Agent 容器镜像托管
- **Viking 记忆库 / mem0 记忆库**：长期记忆后端
- **Viking 知识库**：基于 VikingDB 向量库的 RAG
- **APMPlus**：指标/链路观测；**TLS 日志服务**：日志
- **智能体身份和权限管理平台**：User→Agent→Tool 身份与凭据
- **大模型应用防火墙**：安全围栏底层
- **API 网关 APIG / VPC / PrivateLink / TOS / 持续交付 CP / PostgreSQL / MySQL**
- **[BASE-ADK]**：火山引擎智能体开发套件（SDK 底层）

## 6. [PRODUCT] 支持的接口/SDK 分层

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/[PRODUCT]-supportedinterfaces?lang=zh
- **[PRODUCT] CLI**：命令行 DevOps，与控制台互补，可脚本化。
- **[PRODUCT] Python SDK**：装饰器式（`@app.entrypoint`），封装 [BASE-ADK]，兼容 Google ADK、LangGraph。
- **[PRODUCT] MCP**：工具统一接入 + 网关生命周期管理。
- **[BASE-ADK] 多语言 SDK**：覆盖 Python SDK 不支持的操作。
- **控制面 API**：创建/更新 Runtime、网关等；**数据面 API**：调用 Agent、写入记忆等。
- 注意：Python SDK/CLI 不覆盖 [BASE-ADK] 全部能力，缺失时用 [BASE-ADK] 多语言 SDK。

## 7. 新功能动态（节选，2026 年）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Newfeaturereleasenotes-30?lang=zh （全文 71KB，仅读前 8KB）
- **2026-09-11**：MCP 专属网关新增插件（凭据转换、自定义服务扩展）。
- **2026-09-10**：沙箱实例快照手动创建；MCP 私网域名调试；模型网关按 Proxy API Key/模型维度控 Token。
- **2026-09-04**：[PRODUCT] Studio「快速模式」内置 CreateAgentToolset 动态子 Agent 委派。
- **2026-09-01**：Runtime 支持专属网关（生产）/共享模式（POC）；沙箱模板新增 MCP 服务对外能力 + OAuth JWT 入站认证。
- **2026-08-31**：网关计费形态全面升级（按资源实际用量 + 网关实例形态计费）。
- **2026-08-21**：Studio 新增「智能模式」「从存量项目迁移」（LangChain/LangGraph/Dify）；Harness Sidecar 提升稳定性。
- **2026-08-07**：新增 ArkClaw Sandbox、[BASE-AGENT] Sandbox 预置模板。
- **2026-07-31**：会话资源支持 Serverless PostgreSQL。
- **2026-07-17**：Runtime Webshell 浏览器终端。
- **2026-07-10**：新增 Code Sandbox 类型。
- **2026-06-19**：[PRODUCT] Harness CLI 工具链发布；身份与权限支持组织架构导入/云凭据托管/级联委托。
- **2026-06-10**：Codex（沙箱内 AI 编码 Agent）。
- **2026-05-27**：[PRODUCT] **正式商用**。
- **2026-04-10**：A2A 中心发布；MCP 服务可被 ArkClaw 应用中心调用。
- **2026-03-06**：运行时配额升至 20；A2A 空间注册；MCP 工具集监控。
