# AgentKit Skills 导航与阅读顺序

> 本文件是 14 个组件 Skill 的总入口。新手不必全读——按下方依赖图先读底座，再按你要搭的能力挑挂载组件，最后读安全横切与闭环。
> 最后更新：2026-09-28（基准验收后补充）

## 1. 依赖分层图

```
┌─────────────────────────────────────────────────────────────┐
│  闭环层        observability  →  evaluation                  │
│  （先开观测才能评测）                                         │
├─────────────────────────────────────────────────────────────┤
│  安全横切      identity-permission   guardrails              │
│  （生产上线前必须；可与任意挂载组件组合）                     │
├─────────────────────────────────────────────────────────────┤
│  挂载组件      session-memory  knowledge-base  sandbox       │
│                skills  gateway-mcp  a2a-registry             │
│  （挂到 Agent 上的能力，按需挑选）                           │
├─────────────────────────────────────────────────────────────┤
│  编排层        adk-workflow（多 Agent 编排，google.adk 原语）│
├─────────────────────────────────────────────────────────────┤
│  底座层        veadk  →  agentkit-sdk  →  agentkit-runtime   │
│  （veadk.Agent 是主体；sdk 包装入口；runtime 是部署载体）    │
└─────────────────────────────────────────────────────────────┘
```

## 2. 推荐阅读顺序

| 阶段 | 必读 Skill | 目的 |
|---|---|---|
| 1. 底座 | `veadk` → `agentkit-sdk` → `agentkit-runtime` | 搞清楚 Agent 主体、入口装饰器、部署载体 |
| 2. 编排（可选） | `adk-workflow` | 多 Agent 路由/并行/Dynamic 编排 |
| 3. 挂载（按需） | `session-memory` / `knowledge-base` / `sandbox` / `skills` / `gateway-mcp` / `a2a-registry` | 挑你需要的能力 |
| 4. 安全（生产必做） | `identity-permission` + `guardrails` | 入站鉴权、出站凭据、内容安全 |
| 5. 闭环 | `observability` → `evaluation` | 先接观测，再做评测 |

## 3. 离线可跑 vs 必须云凭据

这是新手最该先看的一张表——决定了你能不能在本地直接验证。

| Skill | 本地可离线验证的部分 | 必须云凭据的部分 |
|---|---|---|
| `veadk` | `veadk.Agent`/`Runner` 构造、import、签名核验 | 真实模型调用、`create_agentkit_app` 云端部署 |
| `agentkit-sdk` | `AgentkitSimpleApp` + `@entrypoint`/`@ping` 本地起服务、缺 user/session_id→400 | `agentkit launch` 部署、云端 invoke |
| `agentkit-runtime` | OpenAPI 清单、描述桩 | Create/Release/Invoke 真调用 |
| `adk-workflow` | ✅ **google-adk 2.2.0 Graph/Join/Dynamic 无模型真跑**（自带 `scripts/validate_orchestration.py`） | 带 LLM 节点的真实编排 |
| `agentkit-skills` | SkillSpace/Skill 注册契约、`skills=[ID]` 加载门 | 真实 upload/ListSkillsBySpaceId（CLI 0.52.13） |
| `session-memory` | import / 后端工厂枚举 / `save_session` 签名；**`backend="local"` 并非无条件离线真构造**（见表下注） | local 真实读写、mem0/Viking 后端、embedding 向量化——均需 AK/SK |
| `knowledge-base` | import / schema 契约 | local 后端构造与真实检索同样需 AK/SK（embedding 初始化）；VikingDB/ContextSearch 真实检索 |
| `sandbox` | ✅ 子进程真执行代码 + session FS 复用/隔离 | 真云沙箱（`AGENTKIT_TOOL_ID`） |
| `gateway-mcp` | 本地 JSON-RPC MCP（initialize→tools/list→tools/call）+ Bearer 401 | 远端 MCP_ENDPOINT 连接 |
| `a2a-registry` | AgentCard schema 校验、`veadk.a2a.ve_a2a_server.init_app()` 本地起 server | 注册到 A2A 空间、Consumer 真实发现调用 |
| `guardrails` | 4 回调契约、规则桩拦截、缺 `TOOL_LLM_SHIELD_APP_ID` 抛 ValueError | 真 LLM Shield 拦截 |
| `identity-permission` | 入站 Bearer/JWT 验签桩、Cedar Allow/Deny、4 行验收矩阵 | 真 UserPool/SSO/JWKS、权限网关发布 |
| `observability` | 内存 span recorder、gen_ai.* 属性、单次 trace vs 聚合分离 | APMPlus/TLS 真查询 |
| `evaluation` | Dataset/ExactMatch/LLM-judge-stub/Experiment 本地跑分 | 在线评测平台 |

> **冷启动实测更正（2026-09-28，钉版 venv 无 AK/SK 环境）**：`LongTermMemory(backend="local")` 与 `KnowledgeBase(backend="local")` 的**构造本身**仍会初始化 embedding/Ark token 并查找 Volcengine AK/SK（或 VeFaaS IAM 文件 `/var/run/secrets/iam/credential`）；无凭据时直接抛 `FileNotFoundError: Get Volcengine access key or secret key ... not exists`。因此 local 后端 ≠ 无凭据离线真读写，只能离线做 import/签名/契约探针，真读写仍需云凭据。裸 `Agent()` 同理触发凭据查找，离线探针可传占位 `model_api_key`（见 veadk Skill §8）。

## 4. 统一环境基线（避免各 Skill 版本漂移）

- **Python**：推荐 3.12（系统 3.14 装 `google-adk==2.2.0` 会因 watchdog 无 wheel 编译失败）
- **核心钉版**：`veadk-python==1.1.13`、`agentkit-sdk-python==0.8.7`、`google-adk==2.2.0`、`mcp==1.26.0`
- **离线 local 后端必装**：`uv add 'veadk-python[extensions]==1.1.13'`（裸包装 `backend="local"` 会 ImportError）
- **mem0 后端另需**：`mem0ai==0.1.118`
- **CLI**：公开 `agentkit-cli 0.52.13`（Skill 子命令只读+upload/delete）；a2a/harness 子命令来自内部文档，未在公开 CLI 实测

## 5. 跨组件关键约束（散落在各 §9，这里集中）

- **评测前必须先开观测**：evaluation 依赖 observability 的 trace 数据
- **guardrails 开关≠生效**：控制台勾选不代表高代码流量过防火墙，必须挂 4 回调并验证拦截串
- **sdk 缺 user/session_id 必须 400**：不回落 default，不生成随机 id（否则多用户串会话）
- **a2a Provider 必须用 `veadk.a2a.ve_a2a_server.init_app()`**：不要自创 HTTP handler；容器侧加 `_GatewayPathRewrite` 中间件
- **skills 必须在 Agent 构造时传 `skills=[SKILL_SPACE_ID]`**：否则 `skills=[]` 不触发 `load_skills()`
- **sandbox 同 session_id 复用同一 FS**：跨 session 隔离
