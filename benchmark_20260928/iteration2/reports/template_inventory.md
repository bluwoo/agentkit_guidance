# 迭代2 · 切片C：重复 Runner/SSE/签名验证样板盘点（template_inventory）

- 盘点时间：2026-09-28
- 盘点范围：`skills/` 下 14 个正式 Skill 的 `SKILL.md`
- 切片 C 负责修改：**除 `agentkit-evaluation/**` 与 `agentkit-knowledge-base/**` 之外的 12 个 Skill**（这两个由其他切片负责，本报告仅统计不修改）。
- 方法：逐文件阅读 + `grep` 标记（`inspect.signature` / `runner.run(` / `run_async` / `StreamingMode.SSE` / `AgentkitSimpleApp` / `create_session`/`SessionNotFoundError`）。
- 签名 ground-truth（本机 `benchmark_20260928/.venv`，钉版 veadk-python 1.1.13 / agentkit-sdk-python 0.8.7 / google-adk 2.2.0，实测 2026-09-28）见 §3。

---

## 1. 重复样板的构成

被反复复制的「代码集成」样板由 5 个固定片段组成，每次出现约 25–45 行：

| 片段 | 内容 | 重复次数 | 冗余度 |
|---|---|---|---|
| **T1 导入头** | `from veadk import Agent, Runner` / `from agentkit.apps import AgentkitSimpleApp` / `from google.genai import types` / `from google.adk.agents import RunConfig` / `from google.adk.agents.run_config import StreamingMode` | 10 | 高 |
| **T2 非流式入口** | `@app.entrypoint async def run(payload, headers): result = await runner.run(messages=payload["prompt"], user_id=..., session_id=...); return result` | 10 | 中（骨架可保留，仅注释冗余） |
| **T3 注释掉的 SSE 块** | `# async def run_stream(...)` 整段 `run_async` + `types.Content(...)` + `StreamingMode.SSE` + `yield event.model_dump_json(...)` | 9 | **极高（零新增信息）** |
| **T4 session 预建注释** | “run_async 继承 ADK 父类，auto_create_session 默认 False，session 不存在会 raise SessionNotFoundError，必须先 `short_term_memory.create_session(...)`” | 9 | 高 |
| **T5 inspect 签名验证一行** | `python3 -c "from veadk.runner import Runner; import inspect; print(inspect.signature(Runner.run))"` | 11 | 高（无害但冗余） |

> 审计报告 `audit/audit_report.md` M4 / L3 已点名：SSE 注释块在 ~10 个 Skill 重复、`inspect.signature` 一行在 ~8 个 Skill 重复，建议只在 veadk/sdk 保留一份、其余改为跳转。

---

## 2. 14 个 Skill 逐个定位（样板所在行号 = 修改前行号）

> 列含义：`样板片段` = 该 Skill 实际包含哪些片段；`独有约束` = **必须保留**、不得随样板一起删的组件特有内容。

| Skill | 行数(前) | 样板位置（SKILL.md 行号） | 含片段 | 组件独有约束（保留） |
|---|---|---|---|---|
| **agentkit-runtime** | 201 | §3.2 行 28–80；inspect 行 45 | T1,T2,T3,T4,T5 | 双域名区分（控制面 volcengineapi.com vs InvokeTool volces.com，行 20）；`/invoke` Header user_id/session_id + Body prompt/files；Runtime API 清单(Version 2025-10-30)；0.5vCPU/跨账号公网镜像/计费 2026-09-01 变更等版本事实 |
| **agentkit-observability** | 430 | §3.2 行 48–95；inspect 行 69 | T1,T2,T3,T4,T5 | 三层文档结构铁律（单次 trace=span 起止差 vs P50/P95 聚合，行 120/134/180）；七大观测对象表；§4.3 全部 gen_ai 字段表（通用15/LLM23/Tool9）；§4.4 APMPlus GetTraceDetail/ListSpan/ListSession OpenAPI；§4.5 10 个日志字段；数据回流 10 万条上限/PII；定价（Trace 0.4 元/GB 等）；ENABLE_APMPLUS/TLS 环境变量 |
| **agentkit-gateway-mcp** | 287 | §3.2 行 44–105；inspect 行 77 | T1,T2,T3,T4,T5 | MCPToolset/StreamableHTTPConnectionParams 集成（行 50–65）；四层 MCP 验收；入站 AuthorizerType 互斥；MCP 协议版本矩阵（2024-11-05…2026-07-28 无状态协议兼容）；语义检索 token 31883→10763；Envoy+Istio 三层插件 |
| **agentkit-guardrails** | 314 | §3.2 基线 Agent 行 126–172；inspect 行 146 | T1,T2,T3,T4,T5 | content_safety 4 回调 + `TOOL_LLM_SHIELD_APP_ID`（行 60–80）；“开关≠生效”反直觉坑；`runtime update --envs-json --auto-release`（env: 不进容器）；2026-09-23 <PROJECT_NAME> 云端实测拦截响应原文；AK/SK 从 VeFaaS IAM 文件自动取 |
| **agentkit-sandbox** | 279 | §3.2 行 30–87；inspect 行 54 | T1,T2,T3,T4,T5 | `run_code` 工具 + `@app.ping`（行 34,80–82）；同 session_id 复用沙箱 FS；5 模板表；快照生命周期/分钟级竞态；三层权限；2026-09-24 <PROJECT_NAME> 云实测（ProjectName 归属/CodeEnv 规格/快照级联/DeleteTool 异步） |
| **agentkit-sdk** | 298 | §3.2 行 33–126；inspect 行 76 | T1,T2,T3,T4,T5 | **鉴权 400**：缺 user_id/session_id 返 400 JSONResponse、不回落 default（行 79–87）；**记忆落库/持久化**：显式 `ShortTermMemory(db_url=...)` + `DatabaseSessionService` assert（行 47–60,274）；SQLite 4 斜杠 URL；两包分别装；两种集成路径对比 |
| **agentkit-session-memory** | 298 | §3.2 行 37–104；inspect 行 69 | T1,T2,T3,T4,T5 | `LongTermMemory(backend=...)` + **记忆落库** `save_session_to_long_term_memory`（行 77–82,98–101）；后端工厂 8 值表；`viking_mem` 废弃→viking；`[extensions]` extras 前置；mem0ai==0.1.118；1 分钟抽取延迟 |
| **agentkit-skills** | 283 | §3.3 行 67–116；inspect 行 90 | T1,T2,T3,T4,T5 | CLI 0.52.13 只读+upload/delete 实测边界；SkillSpace region 隔离；§10.5 <PROJECT_NAME> 云校正（SKILLS/SKILL_SPACE_ID env、`skills=[...]` 才触发 load_skills、UpdateRuntime.SkillSpaceId 被静默忽略）；Quota |
| **veadk** | 220 | §3.2 行 35–60（无完整 AgentkitSimpleApp 块）；§5 run/run_async 描述行 143–145；§8 inspect 行 183 | T5（+ 概念描述） | `Agent(LlmAgent)` MRO；`create_agentkit_app` 9 参数；内置工具表；8 种记忆后端；tracer 开关；固定版 1.1.13（84/84） |
| **agentkit-a2a-registry** | 286 | **无 Runner 样板**（用 `veadk.a2a.ve_a2a_server.init_app()`，行 99–142） | —（不参与样板收敛） | `_GatewayPathRewrite` ASGI 中间件（重复 /runtime/<id> 前缀）；AgentCard 字段规范/protocolVersion 0.2.6|0.3.0；CLI 未实测警告（0.52.13 子命令漂移）；一账号一个模型网关/Agent Mesh POC |
| **agentkit-identity-permission** | 288 | **无 Runner 样板**（用 `OpenApiClient`/`AgentkitMCPClient`，行 65–89） | —（不参与样板收敛） | **鉴权 400/401/403 验收矩阵**；JWT 验签清单；**session 预建**=MCP 握手四层断言；两层钉版（0.8.7 vs 0.6.2）；私有 import 警告；出/入站 Header 不得共用；Allowed Clients 空=允许所有 |
| **adk-workflow** | 279 | **无 AgentkitSimpleApp 入口样板**（`run_async` 命中是 `_run_async_impl`，行 168，误报）；有 `scripts/validate_orchestration.py` | —（已有渐进披露脚本） | **Workflow 版本差异**：google-adk 2.2.0 vs 官网 2.10.0（`max_parallel_workers`/`max_concurrency`）；Graph/Dynamic/Collaborative/Template 规则；HITL/checkpoint；Live Graph 规则 |
| agentkit-evaluation ★ | 225 | §代码集成（inspect 行 63） | T1,T2,T3,T5 | **本切片不改**（其他切片负责） |
| agentkit-knowledge-base ★ | 243 | §代码集成（inspect 行 85） | T1,T2,T3,T4,T5 | **本切片不改**（其他切片负责） |

★ = 排除在切片 C 修改范围外，仅统计。

---

## 3. 权威签名事实（供共享 reference 使用，本机实测 2026-09-28）

钉版：`veadk-python==1.1.13`、`agentkit-sdk-python==0.8.7`、`google-adk==2.2.0`（与离线验证 results.json 84/84 一致）。

```
Runner.run(self,
    messages: str | list[str] | MediaMessage | list[MediaMessage | str],   # 必填
    user_id: str = '',
    session_id: str = 'tmp-session-<时间戳>',      # 缺省自动生成；内部 create_session
    run_config: RunConfig | None = None,
    save_tracing_data: bool = False,
    upload_inline_data_to_tos: bool = False,
    run_processor: BaseRunProcessor | None = None,
) -> str
# 语义：自动 short_term_memory.create_session()，自动转 Content，返回最终文本 str。

Runner.run_async(self, *,
    user_id: str, session_id: str,                 # 关键字必传
    invocation_id: str | None = None,
    new_message: types.Content | None = None,       # 必须手动构造 types.Content，不能传裸 str
    state_delta: dict | None = None,
    run_config: RunConfig | None = None,           # 流式用 RunConfig(streaming_mode=StreamingMode.SSE)
    yield_user_message: bool = False,
) -> AsyncGenerator[Event, None]
# 语义：继承 ADK 父类，auto_create_session 未被 veadk 覆盖（默认 False）；
#       session 不存在会 raise SessionNotFoundError → 必须先显式 create_session。

AgentkitSimpleApp：提供 @app.entrypoint / @app.ping / app.run(host, port)。
```

---

## 4. 收敛方案（落到本切片动作）

1. **新建权威共享 reference**：`skills/references/runner-entrypoint.md` + 可执行 `skills/references/verify_runner_signature.py`。
   - 集中存放 T1–T5 的权威写法、§3 签名事实、以及「鉴权400 / 记忆落库 / session预建 / 持久化STM」四条跨组件契约的**权威定义 + 各归哪个 Skill**。
2. **12 个 Skill 瘦身**：
   - T3（注释掉的 SSE 块）整段删除，替换为一行跳转 `流式 SSE / inspect 验证 → skills/references/runner-entrypoint.md`。
   - T5 inspect 一行删除（改为调用共享脚本 `verify_runner_signature.py`）。
   - T1 导入只保留该 Skill 自身代码真正用到的（删 `types/RunConfig/StreamingMode` 等仅服务于已删 SSE 块的导入）。
   - T2 非流式骨架保留（可复制性需要），但把重复的“源码核验”长注释压成一行跳转。
   - **保留**各 Skill §2 表中标注的“独有约束”，一字不删。
3. **重点四件渐进披露**：
   - observability：§4.3–4.5 大字段表/OpenAPI 表/日志字段表 → `agentkit-observability/references/span-attributes-and-query-api.md`，SKILL.md 留铁律 + 概览 + 跳转。
   - runtime：§3.2 代码块瘦身并跳转共享 reference；保留双域名/版本事实。
   - a2a-registry：保持 init_app 独有模式；把 AgentCard 字段详表收敛跳转 `agentkit-a2a-registry/references/agentcard-schema.md`；保留版本漂移警告。
   - identity-permission：保留 400/401/403 验收矩阵与两层钉版；把 E2E 验收脚本全文下沉 `agentkit-identity-permission/references/e2e-acceptance.md`，SKILL.md 留矩阵 + 跳转。
4. **不动**：`benchmark_20260928/harness|tests|security|evaluation`；不新建备份（复用 `iteration2/backup_skills/`）；`agentkit-evaluation` / `agentkit-knowledge-base` 不改。
