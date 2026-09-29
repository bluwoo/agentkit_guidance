# AgentKit 新手 Harness 执行日志

- **任务开始**：2026-09-28 17:05:49 CST
- **日志记录完成**：2026-09-28 17:23 CST（仍持续到交付）
- **执行代理视角**：从零开始，无任何 AgentKit 先验知识；唯一信息来源为正式 Skills 目录 + 项目根目录结构。

---

## 0. 总览

- 通读 SKILL-TEMPLATE.md + 全部 14 个组件 SKILL.md。
- 在 `benchmark_20260928/` 下建 venv，按 Skill 钉版安装依赖。
- 产出 `harness/`（14 个组件模块 + 总装 app）与 `tests/`（7 个测试文件，34 用例）。
- 测试结果：**34 passed**（证据见 `journal/pytest_output.txt`）。

---

## 1. Skills 读取记录（顺序、关键信息）

阅读顺序按"先底座、后周边"决策。每条记录：组件 / 关键类·函数 / 前置·环境变量 / 与其他组件关系。

| # | 时间(约) | Skill | 读到的关键信息 |
|---|---|---|---|
| 1 | 17:06 | `agentkit-sdk` | `AgentkitSimpleApp()` + `@app.entrypoint(payload,headers)` + `@app.ping` + `app.run()`。请求契约 Header `user_id/session_id`、Body `prompt/files`。`runner.run(messages=,user_id=,session_id=)->str`。缺 user/session_id 必须 400，不回落 default。包 `veadk-python==1.1.13`、`agentkit-sdk-python==0.8.7`。 |
| 2 | 17:06 | `agentkit-runtime` | Runtime=托管在线服务；region `cn-beijing`；控制面域名 `agentkit.cn-beijing.volcengineapi.com`、工具执行域名 `agentkit.cn-beijing.volces.com`。OpenAPI 清单 CreateRuntime…GetRuntimeWebshellEndpoint。 |
| 3 | 17:07 | `veadk` | `veadk.Agent` 继承 Google ADK `LlmAgent`；`Runner`；内置工具 `run_code`；`create_agentkit_app` 工厂；长期记忆/知识库/skills/tracers。env `VOLCENGINE_AK/SK`、`MODEL_AGENT_NAME`、`AGENTKIT_TOOL_ID`。 |
| 4 | 17:08 | `adk-workflow` | 原语从 `google.adk`/`google.adk.workflow` 导入，**不是** `veadk.workflow`。Graph(edges=)、`Event(route=)`+`DEFAULT_ROUTE`、`JoinNode`、Dynamic `@node(rerun_on_resume=True)`+`ctx.run_node()`。钉版 `google-adk==2.2.0`。自带 `scripts/validate_orchestration.py`（无模型 FunctionNode 跑通）。 |
| 5 | 17:08 | `agentkit-skills` | Skill=能力单元，SkillSpace=版本容器；挂载走 Runtime 关联组件；veadk Agent 必须构造时传 `skills=[SKILL_SPACE_ID]` 否则 `skills=[]` 不触发 `load_skills()`。`execute_skill`。CLI 0.52.13 只读+upload/delete。 |
| 6 | 17:09 | `agentkit-session-memory` | 三层记忆：会话层(PG)/短期(Runner)/长期(mem0·viking·local)。`LongTermMemory(backend=)` 默认 `opensearch` 必须显式指定；`viking_mem` 废弃转发 `viking`。`await runner.save_session_to_long_term_memory(session_id,user_id)`。 |
| 7 | 17:10 | `agentkit-gateway-mcp` | `MCPToolset(connection_params=StreamableHTTPConnectionParams(url=MCP_ENDPOINT, headers={"Authorization":"Bearer "+MCP_AUTH_KEY}))`。四层验收 initialize→tools/list→tools/call(isError=false)→后端。入站 ApiKey/CustomJWT 互斥。 |
| 8 | 17:10 | `agentkit-a2a-registry` | AgentCard 暴露于 `/.well-known/agent-card.json`；JSON-RPC `message/send`；`protocolVersion` 限 0.2.6/0.3.0、`protocolBinding=JSONRPC`。Provider 容器必须用 `veadk.a2a.ve_a2a_server.init_app()`，并加 `_GatewayPathRewrite` 把 POST 路径重写为 `/`。 |
| 9 | 17:11 | `agentkit-sandbox` | `run_code` 工具；同 `session_id` 复用同一沙箱 FS；三层权限(read-only/workspace-write/danger-full-access × untrusted/on-request/never)。env `AGENTKIT_TOOL_ID`。 |
| 10 | 17:12 | `agentkit-guardrails` | 高代码 Agent 必须挂 `content_safety` 4 回调(before/after_model_callback、before/after_tool_callback)，来自 `veadk.tools.builtin_tools.llm_shield`；导入需 `TOOL_LLM_SHIELD_APP_ID`。拦截文案 `"Your request has been blocked due to: Prompt Injection..."`。"开关≠生效"。 |
| 11 | 17:12 | `agentkit-identity-permission` | 入站 API Key/OAuth JWT；Cedar 策略→Permission Gateway PEP；凭据托管。安全验收矩阵：无凭据401/过期401/授权200/越权403。`user_id` header 不是可信身份。 |
| 12 | 17:13 | `agentkit-knowledge-base` | `KnowledgeBase(backend="viking"/"local"/..., index=, top_k=)` 挂 `Agent(knowledgebase=...)` 自动挂 `LoadKnowledgebaseTool`。`local`=InMemoryKnowledgeBackend；viking 需 `DATABASE_VIKING_COLLECTION`。 |
| 13 | 17:13 | `agentkit-observability` | APMPlus+TLS；env `ENABLE_APMPLUS/ENABLE_TLS/ENABLE_COZELOOP`。gen_ai.* span 属性。铁律：单次 trace duration=span start→end 差；P50/P95/QPS 是聚合指标，不归因单次调用。APMPlus OpenAPI GetTraceDetail/ListSpan/ListSession。 |
| 14 | 17:14 | `agentkit-evaluation` | 三件套 Dataset(input/reference/actual)/Evaluator(内置+LLM-as-Judge 0.0~1.0)/Experiment(A/B)。在线评测须先开观测；评测对象当前仅 A2A 注册 Agent。平台侧能力。 |

---

## 2. 关键选型与决策

1. **真实 SDK vs 本地桩**：先按 Skill 钉版尝试安装真实包（决策依据：Skills 明确给出 `uv pip install veadk-python==1.1.13 / agentkit-sdk-python==0.8.7 / google-adk==2.2.0`）。能真实导入/构造的就用真实对象（veadk Agent、LongTermMemory(backend="local")、KnowledgeBase(backend="local")、google.adk Workflow）；需要云端凭据的边界（模型调用、Runtime 部署、MCP 远端、A2A 注册、LLM Shield 真拦截、APMPlus 查询、评测平台）用本地契约桩并打 `CloudBoundary` 标记。
2. **Python 版本**：系统自带 Python 3.14.7，google-adk 2.2.0 的 watchdog 6.0.0 无 cp314 wheel 需源码编译失败 → 改用 Skill 推荐的 3.12（`uv python install 3.12`，得到 3.12.14）。
3. **workflow 无模型运行**：直接复用 `adk-workflow/scripts/validate_orchestration.py` 的范式（`InMemorySessionService` + `google.adk.runners.Runner` + `types.Content`），抽成 `run_workflow()`，路由/并行 Join/Dynamic 三类全部真跑。
4. **测试异步**：不用 pytest-asyncio（避免插件/asyncio_mode 配置坑），改用 sync 测试内 `asyncio.run(...)`。

---

## 3. 命令与产物（关键命令 + 输出摘要）

| 时间 | 命令 | 结果摘要 |
|---|---|---|
| 17:07 | `python3 --version` / `uv --version` / curl pypi | Python 3.14.7、uv 可用、PyPI 200 |
| 17:08 | `uv pip install google-adk==2.2.0` (py3.14) | **失败**：watchdog 6.0.0 在 py3.14 无 wheel，clang 编译 fsevents 报错 |
| 17:11 | `uv python install 3.12` → 重建 venv | 下载 cpython-3.12.14（约 2m43s），venv 就绪 |
| 17:12 | `uv pip install google-adk==2.2.0` (py3.12) | 成功；`from google.adk import Workflow, Event` 验证 OK |
| 17:13 | `uv pip install mcp==1.26.0 veadk-python==1.1.13 agentkit-sdk-python==0.8.7` | 成功（含 vikingdb/volcengine/tiktoken 等重依赖） |
| 17:14 | 探测导入 | veadk.Agent/Runner、AgentkitSimpleApp、run_code、LongTermMemory、KnowledgeBase 全部 OK；a2a `init_app` OK；**content_safety 无 APP_ID 时抛 ValueError（与 Skill §3.2 完全一致）** |
| 17:14 | `uv pip install "veadk-python[extensions]==1.1.13"` | 装 redis/redisvl 等；LTM(backend="local")→InMemoryLTMBackend、KB(backend="local")→InMemoryKnowledgeBackend 构造 OK |
| 17:20 | 冒烟：`import harness.*` + 跑三类 workflow | routing=`[BUG HANDLER] processing: I found a bug`、fanout=`MERGED[length=B:5, upper=A:HELLO]`、dynamic=`[FORMATTED] Hello World [/FORMATTED]` |
| 17:21 | `pytest tests/ -v` | 首跑 **32 passed / 2 failed**（MCP `LocalMCPTool` 误把 `run` 当构造参数） |
| 17:22 | 修复后重跑 | **34 passed**（证据 `journal/pytest_output.txt`） |

产物：`harness/` 16 个 .py、`tests/` 7 个文件（34 用例）、`journal/`、`audit/`(空)。

---

## 4. 首次失败

- **首次失败**：在系统 Python 3.14 上装 `google-adk==2.2.0`，watchdog 6.0.0 拉起来用 clang 编译 `watchdog_fsevents.c` 失败（`error: ... returned non-zero exit status 1`，hint 提示缺 Python.h）。
  - 原因：钉版 google-adk 2.2.0 约束 `watchdog<=6.0.0`，而 6.0.0 没有 cp314 预编译 wheel。
  - 解决：不强行用系统 3.14；改用 uv 安装独立 Python 3.12.14（Skill 本身推荐 3.12），之后全部 wheel 就位。

## 5. 返工与绕路

- **返工 1（MCP 测试）**：`LocalMCPTool` 初版把 `run` 写成类方法，测试却用 `LocalMCPTool(..., run=lambda...)` 构造 → `TypeError: unexpected keyword argument 'run'`。返工为 `handler` 字段 + `run()` 调 `self.handler`，测试同步改 `handler=`。浪费约 2 步。
- **绕路 1**：最初想用 pytest-asyncio，担心 `asyncio_mode` 配置在 pytest 9.x 的差异，改为 `asyncio.run` 包装，零插件依赖。

## 6. 未经 Skill 支撑的猜测（及结果）

- **猜 1**：`LongTermMemory(backend="local")` / `KnowledgeBase(backend="local")` 能否在离线环境构造。
  - 结果：猜中可行，但**踩了一个 Skill 没明说的坑**——裸装 `veadk-python==1.1.13` 时这两个构造会报 `requires 'veadk-python[extensions]'`，必须装 extras。Skill 正文只在 mem0 处提了 `mem0ai==0.1.118`，没提 local 后端也需要 extensions extras。
- **猜 2**：workflow 在 2.2.0 上能否无 LLM 跑通。结果：可行，照抄 Skill 自带验证脚本范式即可。
- **猜 3**：content_safety 在没 APP_ID 时的行为。结果：与 Skill 描述一致地抛 ValueError（算半次验证而非纯猜）。

## 7. 因 Skill 指引避免的坑

- **不在 py3.14 硬刚**：Skill 多处写"Python ≥3.10（推荐 3.12，quickstart 用 3.12.0）"——直接切 3.12，避免了和原生扩展死磕。
- **workflow 原语从 google.adk 导入**：Skill 明确写"不要写 `veadk.workflow`"——我没有去造 veadk.workflow。
- **缺 user/session_id 返回 400 不回落**：agentkit-sdk Skill §3.2/§10 反复强调，我在 `c02_sdk_app` 直接实现并加了测试。
- **guardrails 开关≠生效**：我没有假装"控制台勾选=已防护"，而是把真 LLM Shield 标成 CloudBoundary，本地只做规则桩。
- **MCP 入站/出站凭据不混用、不明文打印**：identity/gateway 两个 Skill 都强调，桩里只持 Bearer 入站 key，不模拟明文凭据回显。

## 8. 耗时与步骤数

- **起止**：17:05:49 → 17:23（交付点），约 **18 分钟**。
- **工具调用轮次估算**：约 **30 轮**（读 Skill 14 次批量合并为 5 批、环境探测约 8 轮、写文件约 18 次、跑测试约 6 轮）。
- **每组件耗时**：阅读约 4 分钟；环境搭建约 8 分钟（含下载 Python 3.12 的 2m43s）；写 14 模块约 4 分钟；测试与修复约 2 分钟。

## 9. Skill 质量即时印象（随手记）

- **清楚好用**：`adk-workflow`（自带可运行验证脚本、双版本基线、明确"不要写 veadk.workflow"）、`agentkit-sdk`（请求契约 + 400 规则讲得很死）、`agentkit-guardrails`（反直觉坑"开关≠生效"讲透了）、`agentkit-sandbox`（2026-09-24 实测修正把配额/项目归属/快照级联坑都列了）。
- **含糊/踩坑**：`agentkit-session-memory`/`knowledge-base` 说"backend=local 本地调试"，但没提 local 后端在裸装 `veadk-python` 时要 `[extensions]` extras；新手会卡在 ImportError。
- **有矛盾/过时**：`agentkit-a2a-registry` §3.2/§3.3 的 `agentkit init/add/deploy` CLI 参数与 `agentkit-skills` §3.2 的 CLI 0.52.13 实测（只读+upload/delete）口径不一——Skill 自己也用"实测校正"小节标注了，说明版本漂移严重。
- **对新手友好度总体**：高。每个 Skill 都有"前置条件 checklist + 最小可运行代码 + 失败处理表 + 可执行验证办法"，且大量"已离线核验/已云端实测"标注，能让新手快速判断哪些能本地跑、哪些必须上云。

---

## 10. 安全红线遵守记录

- 未读取/泄露 `~/.bash_profile`、`~/.zshrc`、Cookie、JWT、AK/SK；未在任何产物里写明文凭据。
- 未执行任何需要真实云凭据的写操作；Runtime 部署/发布、MCP 远端连接、A2A 注册、LLM Shield 真拦截、沙箱真创建、APMPlus 查询均停在 `CloudBoundary`。
- 未修改 `skills/` 下任何 SKILL.md，未修改 `agentkit_wizard/` 下任何文件；全部产物写在 `benchmark_20260928/`。
