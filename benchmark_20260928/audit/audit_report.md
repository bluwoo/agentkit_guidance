# AgentKit Skills 只读审计报告

- 审计对象：`skills/` 下 14 个组件 SKILL.md + `SKILL-TEMPLATE.md`；被审计产物 `harness/` + `tests/`
- 审计方式：只读。未改动 `skills/` 与 `harness/` 任何文件；仅复跑 pytest 与在 `.venv` 内做构造探针
- 审计时间：2026-09-28（CST）
- 审计人视角：独立第三方，不复用执行代理的结论

---

## 1. 复核结论

### 1.1 测试复跑（独立复跑，非引用 journal）

命令：`benchmark_20260928/.venv/bin/python -m pytest tests/ -v`

结果：**34 passed, 4 warnings in 4.19s，退出码 0**。逐用例与 `journal/pytest_output.txt` 完全一致（34 项逐一对应）。
唯一 warning：`DeprecationWarning: BaseAgentConfig is deprecated`（来自 google-adk 2.2.0，无害）。
**journal 声称的"34 passed"属实。**

实测运行环境：Python 3.12.14（uv 安装），pytest 9.1.1。与 journal §2 决策 2 一致（系统 Python 3.14 装不上 google-adk 2.2.0 的 watchdog wheel）。

### 1.2 覆盖真实性核查（抽查每个模块是否真实现了 Skill 核心接口，还是空壳）

| 组件 | 真实度判定 | 证据 |
|---|---|---|
| c01 veadk | **半真实** | 真实 `veadk.Agent` 可构造（探针实测 MRO=`[Agent, LlmAgent, BaseAgent]`，与 veadk SKILL §1 一致）；但 `runner.run` 是 `ScriptedRunner` 本地桩，真实模型调用=CloudBoundary。覆盖矩阵"完整（真实构造）"属实但已说明 runner 为桩。 |
| c02 sdk | **契约桩** | `@entrypoint/@ping` + 缺 user/session_id→400 不回落。与 agentkit-sdk SKILL §3.2/§10 硬规则一致；测试 `test_missing_user_id_session_id_rejected_400` 真验证了 400。 |
| c03 runtime | **描述桩** | RuntimeDescriptor + OpenAPI 清单；清单 15 个 API 与 runtime SKILL §4 line 117 逐项对得上（`InvokeTool` 不在 Runtime 清单里，测试还专门断言 `"InvokeTool" not in RUNTIME_APIS`）。 |
| c04 workflow | **真跑** | 真实 `google-adk==2.2.0` Graph/Join/Dynamic，无模型跑通。探针/测试均通过。与 adk-workflow SKILL §3.2 范式一致。 |
| c05 skills | **代码在、但零测试** | `SkillRegistry/execute_skill/skills_field_from_env` 实现了"必须传 skills=[SKILL_SPACE_ID]"加载门（与 skills SKILL §10.5 一致），但 **grep 全部 tests 目录，`SkillRegistry/execute_skill/skills_field_from_env` 被引用 0 次**。覆盖矩阵标"对应 test_components_import.py"=仅 import。**这是覆盖矩阵唯一明显高估的一格。** |
| c06 memory | **真实构造+本地实现** | 探针实测 `LongTermMemory(backend="local")` 真构造出 `InMemoryLTMBackend`（日志 `Initialized long term memory ... InMemoryLTMBackend`）。三层记忆落库是本地 dict 实现。 |
| c07 mcp | **契约桩** | 本地 JSON-RPC server 复现 initialize→tools/list→tools/call 四层 + Bearer 401。与 gateway-mcp SKILL §5/§8 四层验收一致。 |
| c08 a2a | **契约桩** | AgentCard schema（protocolVersion 0.3.0 校验、JSONRPC）+ `_GatewayPathRewrite` 重写 POST→/。与 a2a SKILL §3.5/§4 一致。 |
| c09 sandbox | **真跑（子进程）** | `subprocess.run` 真执行 Python；同 session FS 复用 / 跨 session 隔离有测试。注意：`read-only` 分支是空 `pass`（不真正拦截写），但矩阵未声称本地强制 read-only。 |
| c10 guardrails | **边界桩+规则桩** | 探针实测：不设 `TOOL_LLM_SHIELD_APP_ID` 时 `from veadk.tools.builtin_tools.llm_shield import content_safety` 真抛 `ValueError: The environment variable TOOL_LLM_SHIELD_APP_ID not exists...`，与 guardrails SKILL §3.2 line 54 及 harness c10 line 35 文案一致。拦截文案常量与 SKILL §3.3 实测串一致。 |
| c11 identity | **契约桩** | Bearer/JWT 验签 + Cedar Allow/Deny + 4 行验收矩阵（401/401/200/403），与 identity SKILL §6 安全验收表逐行对应。 |
| c12 knowledge | **真实构造、但检索走自写词法器** | 探针实测 `KnowledgeBase(backend="local")` 真构造出 `InMemoryKnowledgeBackend`；**但真实对象只有 `search` 方法、没有 `retrieve`**，而 harness `LocalKnowledgeBase.retrieve()` 是自写词法打分器，从未调用 `real_kb`。覆盖矩阵写"完整（真实 local 后端）"略带高估——构造真、检索路径不是 SDK 路径（矩阵已诚实标注"本地词法检索 RAG"）。 |
| c13 observability | **契约桩** | 内存 span recorder，严格区分"单次 trace duration=span start→end 差"与"P50/P95 聚合"，与 observability SKILL §4.0 铁律一致。 |
| c14 evaluation | **契约桩** | Dataset/ExactMatch/LLM-judge-stub/Experiment 本地跑分；与 evaluation SKILL §4 三件套概念一致。 |

**覆盖真实性总评**：14 个模块中 12 个名副其实（真实构造/真跑/契约桩边界清晰）；c05 缺行为测试、c12 检索非 SDK 路径，两处存在"构造真但关键行为未被测试触达"的轻度高估。没有发现纯空壳（每个模块都有与对应 SKILL 接口对得上的实现）。

### 1.3 日志可信度（抽查 journal 的"Skill 说了 X"是否属实）

| journal 声明 | 复核结果 |
|---|---|
| §1 各组件关键类/env 摘要（14 行表格） | **全部属实**。逐条对照 SKILL.md：如 sdk 的"缺 user/session_id 400 不回落"=sdk §3.2 line 82；workflow"不要写 veadk.workflow"=adk-workflow §1 line 15；guardrails"开关≠生效"=guardrails §1 line 16；a2a"必须 init_app + _GatewayPathRewrite"=a2a §3.5 line 92/121；skills"必须传 skills=[ID] 否则不 load_skills"=skills §7 line 186 与 §10.5 line 252。 |
| §6 猜1：裸装 `veadk-python==1.1.13` 构造 local 后端报 `requires '[extensions]'` | **属实且重要**。全仓 `grep -rn "extensions" --include=SKILL.md` 只命中 a2a 的 `capabilities.extendedAgentCard`（无关）；**14 个 Skill 无一提及 `veadk-python[extensions]`**。本 venv 里 redisvl/opensearch-py/vikingdb-sdk/openviking-sdk 均已装（=装了 extras），local 后端才构造成功。journal 的踩坑记录是真的。 |
| §6 猜3：content_safety 无 APP_ID 抛 ValueError | **属实**。探针复现，报错文案与 harness c10 完全一致。 |
| §9 称 a2a Skill"自己也用'实测校正'小节标注了" | **不属实（journal 小错）**。`grep "实测校正\|实测修正"` 仅命中 skills §10.5（line 241）与 sandbox line 269。a2a SKILL 并无实测校正小节，只有 §3.2 的"未实测"行内注释。journal 把 skills/sandbox 的校正小节误安到了 a2a 头上。 |
| §9 称 a2a §3.2/§3.3 CLI 与 skills §3.2 CLI 0.52.13 口径不一 | **属实**。a2a line 37–83 列了 `agentkit init --template a2a / add harness / deploy / invoke harness`；skills line 38 明确"CLI 0.52.13 Skill 命令只读+upload/delete"。两者确实未做 reconciliate。 |
| §10 安全红线（未读凭据、未云写、未改 skills/） | 与产物一致：无任何明文 AK/SK；`cloud_boundary_report()` 把 11 个云写动作全部停在边界。 |

**日志可信度总评**：journal 主体高度可信，技术判断基本准确；仅 §9 一处对 a2a 文档结构的描述有误（把别的 Skill 的校正小节安到了 a2a），不影响结论。

---

## 2. 十维评分表（每维 1–5，5 最好）

维度缩写：发现=可发现性 / 边界=适用边界 / 前置=前置条件 / 版本=版本准确性 / 复制=代码可复制性 / 衔接=组件间衔接 / 恢复=错误恢复 / 门禁=验证门禁 / 安全=安全性 / 效率=信息密度效率。

| Skill | 发现 | 边界 | 前置 | 版本 | 复制 | 衔接 | 恢复 | 门禁 | 安全 | 效率 | 总分/50 | 一句话总评 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| adk-workflow | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 4 | 4 | **46** | 双基线钉版+可运行校验脚本+8 层验证门禁，本批最强。 |
| agentkit-sdk | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 4 | 5 | 4 | **44** | 请求契约/400 规则讲得死，两包分别装讲清。 |
| agentkit-gateway-mcp | 4 | 5 | 4 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | **44** | 四层验收+入出站凭据隔离+协议版本矩阵，生产向扎实。 |
| agentkit-guardrails | 4 | 5 | 4 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | **44** | "开关≠生效"反直觉坑讲透，三条件验收门禁可操作。 |
| agentkit-sandbox | 4 | 5 | 4 | 5 | 4 | 4 | 5 | 4 | 4 | 4 | **43** | 09-24 云实测把项目归属/快照级联/配额坑全列了。 |
| agentkit-skills | 4 | 5 | 4 | 5 | 3 | 4 | 5 | 4 | 4 | 4 | **42** | CLI 0.52.13 实测边界+§10.5 云端校正很诚实。 |
| veadk | 4 | 4 | 4 | 4 | 4 | 5 | 4 | 4 | 4 | 4 | **41** | MRO/工厂 9 参源码核验扎实，但部分内置工具标"待核验"。 |
| agentkit-identity-permission | 4 | 5 | 4 | 3 | 3 | 5 | 5 | 4 | 5 | 3 | **41** | 4 行验收矩阵+JWT 清单强，但两套钉版环境+私有 import 易混。 |
| agentkit-runtime | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 3 | 4 | 4 | **38** | 概念/API 清单清楚，但代码薄、验证全在云端。 |
| agentkit-observability | 4 | 4 | 4 | 4 | 3 | 5 | 4 | 3 | 4 | 3 | **38** | gen_ai 属性表+单 trace/聚合铁律好，但 430 行偏冗长。 |
| agentkit-knowledge-base | 4 | 4 | 2 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | **37** | backend 表齐，但漏 `[extensions]` 前置，本地后端跑不起来。 |
| agentkit-session-memory | 4 | 4 | 2 | 4 | 3 | 4 | 4 | 3 | 4 | 4 | **36** | 三层模型/后端工厂表好，同样漏 extras，示例只走 mem0 云。 |
| agentkit-a2a-registry | 4 | 4 | 3 | 2 | 4 | 4 | 3 | 3 | 4 | 3 | **34** | AgentCard 字段规范准，但 §3.2/§3.3 CLI 与 0.52.13 漂移未 reconciliate。 |
| agentkit-evaluation | 4 | 4 | 4 | 3 | 2 | 4 | 3 | 3 | 3 | 3 | **33** | 三件套/闭环概念清楚，但"代码集成"是通用模板、无 eval SDK 可跑。 |

**整体套件评分（14 个加权均值）≈ 39.3/50**。作为"干净室新手仅靠文档 18 分钟搭出 34 测试通过的 harness"的能力基线，属于**良好偏上**：边界标注（"需云凭据联调/未实测"）普遍诚实、排障表可操作；主要失分集中在"离线本地路径的前置依赖缺失"和"跨 Skill 版本漂移未收口"。

---

## 3. 不足清单（证据驱动，按严重度分级）

### 阻塞（Blocker）

**B1. session-memory / knowledge-base / veadk：离线 local 后端漏写 `veadk-python[extensions]` 前置**
- 涉及：`agentkit-session-memory` §2、`agentkit-knowledge-base` §2、`veadk` §2
- 问题：三个 Skill 的依赖行只写 `uv add veadk-python==1.1.13` / `mem0ai==0.1.118`，但 `LongTermMemory(backend="local")`、`KnowledgeBase(backend="local")` 在裸装上会因缺 extensions 子依赖（redisvl/opensearch/vikingdb）而构造失败。
- 证据：
  - journal §6 猜1（line 83）："裸装 veadk-python==1.1.13 时这两个构造会报 requires 'veadk-python[extensions]'，必须装 extras。Skill 正文只在 mem0 处提了 mem0ai==0.1.118，没提 local 后端也需要 extensions extras。"
  - 我在本 venv 实测：redisvl 5.x、opensearch-py 3.x、vikingdb-python-sdk、openviking-sdk 均已安装时，local 后端才构造出 `InMemoryLTMBackend`/`InMemoryKnowledgeBackend`。
  - `grep -rn "extensions" skills/*/SKILL.md`：无任何 Skill 提到 `veadk-python[extensions]`。
- 影响：忠实按 Skill 依赖行裸装的新手，在本地/离线调通记忆与知识库这两个"本地可调试"路径上直接 ImportError，只能靠猜（本实验就是猜中才过）。
- 修正：在 session-memory §2 与 knowledge-base §2（及 veadk §2）依赖段加一行："**本地/离线调试用 `backend="local"` 时必须装 extras：`uv add 'veadk-python[extensions]==1.1.13'`；裸 `veadk-python` 会在构造 local 后端时 ImportError。mem0 后端另需 `mem0ai==0.1.118`。"

### 高（High）

**H1. a2a-registry §3.2/§3.3 CLI 与 0.52.13 现实漂移未收口**
- 涉及：`agentkit-a2a-registry` §3.2（line 37–62）、§3.3（line 64–84）
- 问题：a2a 给出 `agentkit init --template a2a`、`agentkit add harness`、`agentkit deploy`、`agentkit invoke harness`，但 `agentkit-skills` §3.2 line 38 实测"公开 CLI 0.52.13 Skill 命令只读+upload/delete"。a2a 自己只在每行加了"未实测"注释，没有说明这些命令需要哪个 CLI 版本、是否在 0.52.13 存在。
- 证据：a2a line 37/68/71/80/83；skills line 38。journal §9 line 105 也独立指出该漂移。
- 影响：新手在 0.52.13 上照抄 a2a CLI 会撞 unknown option/无此子命令，且无排障指引。
- 修正：a2a §3.2/§3.3 顶部加"CLI 版本前提"框：这些 `init --template / add harness / deploy` 来自内部操作文档，公开 `agentkit-cli 0.52.13` 未暴露；先用 `agentkit --version` 确认，或改走 §3.4"Runtime 控制台勾选注册到 A2A 空间"这条已验证路径。

**H2. 无跨 Skill 导航/阅读顺序图（可发现性）**
- 涉及：整体（skills 根目录无 README/index）
- 问题：14 个 Skill 之间无"先读哪个、依赖顺序"的总览。新手必须全读 14 个（journal §1 确实读了全部 14 个）。
- 证据：skills 根目录只有 14 个组件目录 + SKILL-TEMPLATE.md，无 index/README。journal §1 阅读顺序是新手自己"先底座后周边"临时决策的。
- 影响：上手成本高，容易漏掉交叉依赖（如"评测前必须先开观测"这种跨件约束散落在各 §9）。
- 修正：新增 `skills/README.md` 一张依赖图：veadk→sdk→runtime 为底座；memory/kb/sandbox/skills/mcp/a2a 为挂载组件；identity/guardrails 为安全横切；observability→evaluation 为闭环。标注"离线可跑 vs 必须云凭据"。

**H3. identity-permission 两套钉版环境易让新手装错**
- 涉及：`agentkit-identity-permission` §2（line 20–23）、§3.3（line 66–72）
- 问题：离线导入基线写"Python 3.13.7 + agentkit-sdk 0.8.7 + mcp 1.26"，0714 E2E 钉版又写"Python 3.10.19 + agentkit-sdk 0.6.2 + mcp 1.28.1"；且 §3.3 用了下划线私有模块 `agentkit.auth._openapi`。本实验实际跑在 Python 3.12.14，与两个"基线"都不完全一致，但仍通过——说明 Skill 的版本约束写得过死却又不闭环。
- 证据：identity line 20–23；line 69 自述"下划线私有模块，非公开稳定 API"。
- 影响：新手不知道该照哪套装；私有 import 在版本间可能漂移。
- 修正：在 §2 明确"**本仓库统一以 0.8.7 为导入基线；0.6.2 仅 0714 教学 E2E 用，不要混装**"，并把 §3.3 的私有 import 标注为"诊断用、非生产依赖"。

### 中（Medium）

**M1. harness c05_skills 零行为测试（覆盖矩阵高估）**
- 涉及：`harness/c05_skills.py` + `journal/components_coverage.md` 第 5 行
- 问题：`SkillRegistry/execute_skill/skills_field_from_env` 实现了 skills SKILL 最关键的"加载门"，但全部 tests 目录对这些符号引用为 0；覆盖矩阵却把它映射到 `test_components_import.py`（仅 import）。
- 证据：`grep -rl SkillRegistry tests/` = 0；矩阵 line 14。
- 影响：skills 的核心坑（不传 skills=[] → 不 load_skills）在 harness 里没被任何测试锁死，未来回归可能悄悄失效。
- 修正：coverage 矩阵把 c05 标为"import-only"；补一个测试：设 `SKILL_SPACE_ID` 后 `skills_field_from_env()` 返回 `[sid]`，未设返回 `[]`。

**M2. harness c12_knowledge 真实 InMemoryKnowledgeBackend 从未被查询**
- 涉及：`harness/c12_knowledge.py`
- 问题：真实 `KnowledgeBase(backend="local")` 对象只有 `search`、没有 `retrieve`（探针实测 `hasattr(kb,'retrieve')=False`）；harness 检索走自写词法器，`real_kb` 构造后即闲置。
- 证据：探针输出 `has retrieve: False ['search', ...]`；c12 line 42–52 自打分。
- 影响："真实 local RAG 后端"的说法在测试层面只验了构造，没验 SDK 检索路径。
- 修正：coverage 矩阵措辞改为"真实构造 + 本地词法桩检索"；或补一个对 `real_kb.search(...)` 的冒烟。

**M3. agentkit-sdk §3.2 示例写死 `/data/sessions.db`**
- 涉及：`agentkit-sdk` §3.2 line 55–57
- 问题：示例 `os.makedirs("/data")` + `sqlite+aiosqlite:////data/sessions.db`，在普通 macOS/无 root Linux 上 `/data` 不可写，复制即报错。
- 证据：sdk line 55–56。
- 影响：新手复制最小示例首跑失败。
- 修正：把默认路径改为 `./.sessions.db`（相对路径），再用注释说明生产用绝对路径 4 斜杠写法。

**M4. observability 信息密度低、SSE 样板重复**
- 涉及：`agentkit-observability`（430 行）；以及 sdk/runtime/veadk/skills/memory/mcp/a2a/sandbox/guardrails/identity/kb/eval 等 ~10 个 Skill 重复贴同一段注释掉的 SSE 代码块。
- 问题：每个 Skill 都复制同一段 `run_async`/`StreamingMode.SSE` 注释代码，占大量篇幅但零新增信息；observability 还把全部 gen_ai 字段表铺开。
- 证据：sdk line 95–115、runtime line 60–77、skills line 101–113、memory line 82–98、kb line 95–107 等几乎逐字相同。
- 影响：新手被冗余淹没；版本一改要同步改十几处。
- 修正：SSE 样板只在 veadk 或 sdk 保留一份，其余 Skill 改为"流式写法见 veadk SKILL §5"。

### 低（Low）

**L1. journal §9 对 a2a 文档结构描述有误**：称 a2a"自己也用实测校正小节标注了"，实际 a2a 无该小节（grep 证明仅 skills §10.5 与 sandbox 有）。属日志小瑕疵，不影响结论。

**L2. harness c09 read-only 模式是空 `pass`**：`LocalSandbox` 的 read-only 分支不真正拦截写（c09 line 38–40），也无测试。当前矩阵未声称本地强制 read-only，可接受，但应在代码注释里写明"本地桩不强制，真强制在云沙箱"。

**L3. `python3 -c "inspect.signature(Runner.run)"` 验证命令重复出现在 ~8 个 Skill**：无害但冗余，可收敛到 veadk 统一说明。

**L4. 覆盖矩阵"需云端凭据用例数量：0"属实，但 CloudBoundary 是约定而非强制**：harness 靠人工标注边界，没有机制防止某模块真的发云请求。对本实验可接受。

---

## 4. 亮点清单（应保留）

1. **adk-workflow 的双基线+可运行校验脚本**（§1/§3.2/§10）：明确"AgentKit 钉版 2.2.0 vs 官网 2.10.0"，给出 `scripts/validate_orchestration.py` 可直接跑，并把"2.2.0 无 `max_parallel_workers`"这类版本差异写进失败表。harness c04 几乎照抄其范式即跑通。
2. **guardrails 的"开关≠生效"反直觉坑**（§1 line 16、§10 line 300）：把"控制台勾选≠高代码流量过防火墙"用警示框前置，并给出三条件验收门禁（拦截串<1s + 正常请求放行 + 日志见 `LLM Shield triggered`）。harness 据此把真 LLM Shield 标成 CloudBoundary 而非假装生效。
3. **skills §10.5 云端实测校正**（line 241–268）：承认 `UpdateRuntime.SkillSpaceId` 字段被静默忽略、真实消费走 `SKILLS=space:<id>` / `SKILL_SPACE_ID` env，而不是照抄控制台 UI。这种"文档 vs 实测冲突以实测为准"的范式值得推广。
4. **sandbox §云联调实测修正**（line 269–279）：项目归属（CLI 无 `-p`）、CodeEnv 最低规格、快照级联删除、配额已满等只有真踩过才知道的坑。
5. **gateway-mcp 的四层验收 + 入出站凭据隔离**（§5/§6/§8）：initialize→tools/list→tools/call(isError=false)→后端 四层分别断言；入站 Authorization 与出站注入 Header 不得共用；明文 Key 禁入日志。harness c07/c11 直接复现了这个矩阵。
6. **observability 的"单次 trace vs 聚合"铁律**（§4.0 line 120）：反复强调单次 duration=span start→end 差，P50/P95/QPS 是聚合窗指标、不得归属单次调用。harness c13 据此把 `trace_summary` 与 `aggregate_window` 拆成两个方法。
7. **全套件一致的"【需云凭据联调】未实测"诚实标注**：几乎每个云命令段都标了"未在本环境实测/以控制台为准"，让新手能清楚区分"本地能跑"与"必须上云"。这是本套件对新手最友好的整体设计。
8. **sdk 的 400 硬规则**（§3.2 line 82、§10 line 274）：缺 user/session_id 必须 400、不回落 default、不生成随机 id，并解释了为什么（多用户聚合到同一会话=数据泄漏）。

---

## 5. 优先修正建议（Top 5，按投入产出比排序）

| 优先级 | 修正项 | 对应不足 | 为什么先做 | 改哪里 |
|---|---|---|---|---|
| 1 | 给 session-memory / knowledge-base / veadk 的 §2 补 `[extensions]` extras 前置 | B1 | 一句话依赖行改动，直接消除离线搭建第一个 ImportError 卡点；本实验就因它返工/猜测 | 三个 SKILL.md 的"依赖包"段加一行 |
| 2 | a2a §3.2/§3.3 加"CLI 版本前提/与 0.52.13 关系"说明 | H1 | 防止新手照抄必失败的命令；与已有"未实测"注释互补 | a2a SKILL.md §3.2 顶部加框 |
| 3 | 新增 `skills/README.md` 依赖/导航图 + 离线vs云标注 | H2 | 一次性把"读哪 4 个先、哪些必须上云"讲清，砍掉全读 14 个的成本 | skills/ 根目录新文件 |
| 4 | 给 c05_skills 加载门补行为测试、c12 改"构造真/检索桩"措辞 | M1/M2 | 小改动即可把覆盖矩阵从"高估"拉到"诚实"，保护最重要的 skills 加载门不回归 | tests/ + coverage 矩阵 |
| 5 | 把重复的 SSE 注释代码块收敛到 veadk/sdk 一处 | M4 | 版本一改只改一处，显著降冗余 | 其余 ~10 个 SKILL.md 的 SSE 段改为链接 |

---

### 附：审计动作清单（只读）
- 复跑 pytest：34 passed（4.19s），退出码 0。
- venv 构造探针：LTM(local)/KB(local)/Agent MRO/content_safety 无 APP_ID 抛 ValueError 全部复现。
- 包清单核对：veadk-python 1.1.13 / agentkit-sdk-python 0.8.7 / google-adk 2.2.0 / mcp 1.26.0；已装 extensions（redisvl/opensearch/vikingdb），未装 mem0ai。
- 未修改 `skills/` 与 `harness/` 下任何文件；本文件是唯一新增产物。

---

## 6. 修正后独立复验（2026-09-28）

原审计以上各节记录的是**修正前基线**，用于保留发现问题时的证据。随后已完成以下正式修正：

1. `veadk`、`agentkit-session-memory`、`agentkit-knowledge-base` 补充 `veadk-python[extensions]` 前置。
2. `agentkit-a2a-registry` 补充 CLI 版本前提与不支持时的 SDK/控制台替代路径。
3. 新增套件总入口 `skills/README.md`，集中说明依赖顺序、离线/云边界和统一版本。
4. `agentkit-identity-permission` 明确 0.8.7 为新项目默认，0.6.2 仅用于历史教学复现。
5. `agentkit-sdk` 将本地 SQLite 示例从写死 `/data/sessions.db` 改为项目相对路径。
6. Benchmark 为 `agentkit-skills` 增加 6 个行为测试，并将 Knowledge Base 的覆盖描述改为“真实构造 + 本地词法桩检索”。

主代理在修正完成后独立执行：

```bash
benchmark_20260928/.venv/bin/python -m pytest benchmark_20260928/tests -q
```

结果：**40 passed，0 failed，4 个 `BaseAgentConfig` 弃用警告，5.06s，退出码 0**。警告来自固定版 `google-adk==2.2.0`，未被静默忽略。

正式 `skills/` 扫描树仅保留 14 个组件 `SKILL.md`；修正前备份已移至项目 `_backup/skills-pre-benchmark-fix-20260928/`，避免重复 Skill 被发现。
