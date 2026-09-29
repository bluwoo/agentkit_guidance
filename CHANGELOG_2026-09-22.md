# [PRODUCT] Skills 精修变更说明

**精修日期**：2026-09-22（第一轮全量精修 + 第二轮定点修复）
**范围**：`skills/` 下全部 14 个组件 SKILL.md
**原则**：保留现有正确内容，就地精修；区分已核实 / 版本依赖 / 仍待确认；不声称云端验证通过。

---

## 〇-B、第四轮：ADK `llms-full.txt` 全文审计与双版本回归（2026-09-28）

本轮跟随 GitHub `llms-full.txt` 的迁移提示，完整读取 `https://adk.dev/llms-full.txt`（约 3.39 MB、74,854 行），并将官网主干与 [PRODUCT] 固定版分开核验：

- [PRODUCT] 执行基线：`google-adk==2.2.0`；官网/PyPI 对照基线：`google-adk==2.10.0`，使用独立临时 venv，不修改项目固定环境。
- 增加双版本规则，禁止把官网主干新增参数直接用于 [PRODUCT] 钉版。
- 补充 `Workflow(max_concurrency=N)`；明确 2.2.0 的 `node()` 无 `max_parallel_workers`，2.10.0 才有。
- 精确化 Graph 中 `LlmAgent.mode`：固定版未显式设置时按 `single_turn` 语义运行；有非 START 前驱的 `chat` 节点会被 Graph 校验拒绝；`task` 因官网正文存在冲突表述，继续要求真实集成验证。
- 补充 Schema、Event 单一最终 output、state 作用域和大对象存储边界。
- 补充 1.x→2.x 迁移门禁：自定义 Session Schema 兼容 `node_info`、`output` 等字段；禁止直接 append Session Event；异常上抛给 `RetryConfig`，不得吞掉 `NodeInterruptedError`。
- 补充 Live Graph：单事件循环/单 `LiveRequestQueue`、发声节点显式 mode、live 路径不并发、`ParallelAgent` / `LoopAgent` 不可用于 live。
- 2.2.0 和 2.10.0 的三种 Template 均发弃用警告；2.10.0 同时提示 Workflow 尚不能机械替换所有 `LlmAgent` sub-agent 场景。
- 2.2.0 Dynamic 用例的 `leftover tasks` 经源码核查为旧版清理日志；同一用例在 2.10.0 已消失，未发现未完成协程或结果缺失。

第四轮验证结果：
- 2.2.0 与 2.10.0：同一组 Graph 顺序、三路由、Join、back-edge、Dynamic、Template Sequential/Parallel/Loop 全部通过。
- `quick_validate.py`：通过。
- `test_code_blocks.py`：14 Skills / 20 Python 代码块 / 20 通过 / 0 失败。
- 正式 Skill 敏感信息扫描：未发现 Cookie/JWT/真实 AK/SK。

---

## 〇-A、第三轮：ADK 编排正式 Skill 升级

已将后续对 `https://adk.dev/workflows/`、`https://adk.dev/graphs/` 及 9 个相关页面的学习与离线核验结果合并到权威文件 `skills/adk-workflow/SKILL.md`：

- 新项目选型改为 **Graph/Dynamic 优先**；SequentialAgent / ParallelAgent / LoopAgent 明确为仍可运行但已弃用的存量模板。
- 替换 Graph/Dynamic 占位符示例，新增 `scripts/validate_orchestration.py`。脚本不用模型或云资源，覆盖 Graph 顺序、条件与 DEFAULT_ROUTE、Join、back-edge、Dynamic、Sequential、Parallel、Loop。
- 修正 `LoopAgent.max_iterations`：固定版默认是 `None`，不是 5；必须显式硬上限并通过 escalate 退出。
- 修正 Parallel 状态口径：分支不同，但固定版 Python 使用浅拷贝 InvocationContext，不能假定 `session.state` 为完全隔离副本。正式示例改为显式输入、独占输出键、事件 `state_delta`，并对两个分支做精确输出断言。
- 补充 Graph 由 session events 重建恢复状态、Dynamic 的 `rerun_on_resume` / run_id / HITL 规则，明确恢复与故障注入尚未实测。
- 确认 `CreateAgentToolset` 的真实导入路径和构造签名，移除“API 待核验”；仍保留资源权限、动态创建和 Runtime 行为未联调边界。
- 明确 Python 2.2.0 的 `node()` 支持 `parallel_worker=True`，但没有 `max_parallel_workers` 参数；不得照搬 TypeScript 配置。
- 明确本轮未完成真实模型、Supervisor 运行时委派、Runtime/A2A 云端链路验证。

第三轮验证结果：
- `quick_validate.py`：`adk-workflow` Skill 结构与元数据通过。
- `test_code_blocks.py`：14 个组件、17 个 Python 代码块，17 通过 / 0 失败；其中 `adk-workflow` 4 个代码块通过。
- `skills/adk-workflow/scripts/validate_orchestration.py`：8 类编排全部运行通过，并额外覆盖 BUG、SUPPORT、DEFAULT_ROUTE 三条路由；运行时出现 3 条 Template 弃用警告，以及 Dynamic 示例的 leftover task 取消提示，均已在 Skill 中保留边界说明。
- 真实 LLM、checkpoint/HITL 故障恢复、Supervisor 动态委派、[PRODUCT] Runtime/A2A 云端联调未执行。

---

## 〇、第二轮定点修复（交付前抽检发现的内容矛盾）

交付前抽检发现以下矛盾，已逐一修复并回归验证。每条均标注涉及文件与修复方式：

| # | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | guardrails §2 | 依赖/环境变量写"无需额外安装/无"，与 §1/§3.2 高代码路径需 content_safety 回调 + TOOL_LLM_SHIELD_APP_ID 矛盾 | §2 按控制台路径 / SDK 高代码路径拆分依赖与环境变量 |
| 2 | guardrails §3.2 | 代码块含猜测 API"疑似 structured_guardrail_callbacks()之类"；基线代码未显著标注未接围栏 | 删除猜测 API，明确列为接入阻塞（钉版 [BASE-ADK] 1.1.13 未导出该符号）；基线代码加 🚨 生产安全警示，不得当生产安全示例 |
| 3 | guardrails §3.3 | 绝对说"只走控制台配置" | 改为两条路径生效条件说明，高代码路径还需代码级回调 + 环境变量 |
| 4 | guardrails §7 | "攻击日志为空"遗漏"高代码未挂回调"核心原因 | 排障表补充原因③：高代码 Agent 未挂 content_safety 回调（控制台显示已启用但实际无流量经检测） |
| 5 | guardrails §5 | 把业务自定义 user_id/session_id 当标准可信身份 | 澄清 user_id/session_id 是业务路由与会话隔离标识，不作为授权依据；入站认证由网关层完成，见 identity-permission Skill |
| 6 | guardrails §8 | curl 无入站鉴权示例；测试命中日志暗示全路径安全 | curl 补 Authorization Bearer 鉴权（按实际启用方式二选一）；验证范围说明仅覆盖受控规则命中+正常流量+链路关联，不构成全路径安全保证 |
| 7 | guardrails/gateway-mcp/[PRODUCT]-skills | 验证日期误标：声称"离线核验通过 2026-09-22（钉版 venv）"，但 import/签名验证实际为 2026-09-18 历史 results.json（84/84），本轮仅做文案复核 + py_compile | 三处均改为"2026-09-18 历史离线验证 results.json 已核验；2026-09-22 文案复核"；MCPToolset 注明未在 test_imports 覆盖范围 |
| 8 | knowledge-base §1 | 称"每次对话自动检索"，与 §4 确认挂载 LoadKnowledgebaseTool（工具可调用）矛盾 | 改为"Agent 可在对话中调用检索工具；是否每轮触发由 Agent 根据 instruction 与工具描述决定，不保证每轮必检索" |
| 9 | knowledge-base §3.2 | `index=os.getenv(...)` 缺失时传 None 导致后续失败 | 增加显式必填检测：环境变量缺失时 raise RuntimeError，不允许传 None |
| 10 | knowledge-base §2 | 新增 ContextSearch 路径后，前置条件仍要求所有人必须 VikingDB | 按 Viking 后端路径 / ContextSearch 后端路径拆分前置条件；VikingDB Collection 仅 Viking 路径必填 |
| 11 | knowledge-base §10 | 索引 2~3s/20s/23TB/350MB 等指标无条件适用所有后端 | 限定为 Viking 后端增量文档更新的产品资料口径（非全量初次建库、非所有文档类型、非 SLA）；ContextSearch 等其他后端以各自服务为准 |

第二轮修复后回归：test_code_blocks.py 重跑 14 skills / 15 块 / 15 通过 / 0 失败（第二轮删除了 guardrails §3.2 中猜测 API 的代码块，故总数从第一轮的 16 降至 15）；frontmatter / 代码围栏 / py_compile 全部通过。

---

## 一、全局变更（第一轮全量精修）

| 变更项 | 说明 |
|---|---|
| 版本号统一 | 全部组件依赖包由 `>=1.0.8` / `==1.0.10` 等混合表述统一为离线验证固定版 `[BASE-ADK]-python==1.1.13` / `[PRODUCT]-sdk-python==0.8.7` / `google-adk==2.2.0` |
| last_verified | 全部 14 个文件更新为 `2026-09-22` |
| 引用格式 | 企业搜索来源由被剥离的 `["url"]` 裸数组统一转为内联 `（来源：url）` 格式，共修复 12 处 |
| 结构验证 | 全部 14 文件 frontmatter 完整、代码围栏闭合、Python 代码块 py_compile 通过 |
| 代码块测试 | `test_code_blocks.py`：14 skills 扫描、16 块、16 通过 / 0 失败 |

## 二、各组件变更摘要

### Batch A：核心框架与部署（5 组件）

**[BASE-ADK]**
- 版本号对齐 1.1.13（§2 依赖、§8 验证脚本、§10 版本说明）
- 消除 `run_code` import "待实测"标记 → 改为离线核验通过（results.json 84/84）
- 内置工具表新增「核验状态」列：`run_code` 已 PASS，`web_search/image_*` 保持 ⚠️ 待核验
- §11 来源表补离线验证报告引用

**[PRODUCT]-runtime**
- §2 依赖补固定版本号；代码块 import 本就被 results.json 证实

**[PRODUCT]-sdk**
- §2 依赖、§3.3 快速上手补固定版本号
- §10 版本演进说明消除与 frontmatter 的前后矛盾

**adk-workflow**
- §2 两处版本号对齐；编排类 import 全部被 results.json 证实

**[PRODUCT]-sandbox**
- 企业搜索核证 CLI 子命令语义：`exec`=交互式 WebSocket 终端（attach codex），`shell`=HTTP 单命令返回 JSON；§3.3 补区分说明，§8 注明用途
- §3.2 `Runner(agent=agent)` 补 `app_name`（注明可省略）
- 版本号对齐；§11 来源表补 CLI 语义内部 wiki

### Batch B：安全与集成（5 组件）

**[PRODUCT]-gateway-mcp**
- MCP 协议版本核证：2026-07-28 新无状态协议 + 网关支持矩阵（旧有状态握手接受 2024-11-05 等版本）
- 入站认证互斥规则核证：API Key / OAuth JWT 互斥，可通过更新能力修改类型但旧凭证失效
- 出站凭据托管机制细化

**[PRODUCT]-identity-permission**
- SDK 版本自相矛盾消除（0.6.2 vs 0.8.7 → 统一 0.8.7）
- 入站/出站授权流程细化

**[PRODUCT]-guardrails**（修正幅度最大）
- 关键纠正：高代码 Agent 必须显式挂载 `content_safety` 4 个回调（before/after_model + before/after_tool）+ 配置 `TOOL_LLM_SHIELD_APP_ID`，仅控制台勾选不生效
- 反直觉坑标注：控制台显示"已启用"但代码未挂回调时，流量可能一次都没经过防火墙检测；以攻击日志拦截记录为准
- 四类防护策略细化（提示词攻击/模型滥用/敏感数据/算力消耗）
- 独立计费说明

**[PRODUCT]-a2a-registry**
- AgentCard 字段规范核证：必填/可选字段清单，`protocolVersion` 限 0.2.6/0.3.0，`protocolBinding` 用 `JSONRPC`
- 注册来源（Runtime/Standard）与导入方式（JSON/URL）
- 版本号对齐

**[PRODUCT]-skills**
- 地域前提核证：公测地域 cn-beijing / cn-shanghai，企业私有 SkillSpace 是 region 级隔离
- Quota 核证：Skill 400、SkillSpace 40、单空间绑定 Skill 50
- 三种挂载方式细化
- 版本号对齐

### Batch C：数据与观测（4 组件）

**[PRODUCT]-knowledge-base**
- 离线核验 `KnowledgeBase` import 与 `Agent(knowledgebase=)` 入参（[BASE-ADK]/agent.py:264）
- 补全 ContextSearch 统一检索网关：后端选项表（viking/context_search/opensearch/redis/milvus/tos_vector/openviking/local）
- 补全构造参数 `top_k(默认10)/enable_profile/query_with_user_profile/backend_config`
- 补全环境变量（VIKING_PROJECT/RESOURCE_ID/VERSION/REGION/KNOWLEDGEBASE_INDEX + context_search_*）
- 索引耗时（约 2~3s，≤20s）、规模上限（单库 23TB/单文档 350MB）
- 细粒度访问控制风险注记（SSO 同角色共用账号为已知卡点）

**[PRODUCT]-session-memory**
- 离线核验 `LongTermMemory` import、`save_session_to_long_term_memory` 协程签名
- 关键纠正：SDK 默认 backend 是 `opensearch`，生产必须显式传 `mem0`/`viking`
- `viking_mem` 废弃确认（→viking，生产推荐 viking/mem0）
- 会话后端补全（local/sqlite/mysql/postgresql），隔离键 `app_name+user_id+session_id`
- 「AddSession 100 条上限」标注为待确认（内部资料/源码均未找到依据）

**[PRODUCT]-observability**
- 数据回流从一句话 → 可执行配置步骤（可观测→数据回流→创建导出任务，字段映射 GenAIInput→input）
- 回流上限：总量与单次均 10 万条、只回流新数据、PII 默认脱敏
- 定价修正：Trace 0.4 元/GB、Metrics 0.18 元/百万数据点、免费额度（Trace 25GB/月 + Metrics 1 亿点/月 + TLS 赠 30 天）

**[PRODUCT]-evaluation**
- 评估器类型细化：≥50 预置 + LLM（0.0~1.0）+ Code（Python/JS）
- 评测对象关键限制：当前仅支持 A2A 中心注册 Agent
- 评测集规格（input/reference_output/actual_output，约 5000~10000 条/200MB）
- 路线图校准：已上线=评测集+评估器+实验（8月）；轨迹/过程评测 P1（Q3/Q4）
- trace 回流与 observability 交叉引用

## 三、企业知识核证记录（含来源 URL）

| 批次 | Query（自然语言） | 结果 | 关键来源 URL |
|---|---|---|---|
| A | [PRODUCT] 沙箱 CLI 执行命令子命令是 exec 还是 shell？正确写法和参数是什么？ | ✅ 证实为两个不同子命令（exec=WS交互终端，shell=HTTP单命令返回JSON） | 见 [PRODUCT]-sandbox/SKILL.md §11 |
| B | MCP 协议当前兼容版本与网关支持矩阵是什么？2026-07-28 新协议支持情况？ | ✅ 2026-07-28 新无状态协议 + 旧版本兼容矩阵（2024-11-05 等）；工具集全面兼容，HTTP转MCP尚不支持 | <INTERNAL_REFERENCE_REMOVED>；<INTERNAL_REFERENCE_REMOVED> |
| B | 入站认证 API Key/OAuth JWT 是否互斥、能否修改类型？ | ✅ 互斥，可通过更新能力修改类型但旧凭证失效，需重新联调 | <INTERNAL_REFERENCE_REMOVED> |
| B | Guardrails 支持哪些策略类型与挂载方式？高代码是否必须挂回调？ | ✅ 四类防护（提示词攻击/模型滥用/敏感数据/算力消耗）；高代码须显式挂载 content_safety 4 回调 + TOOL_LLM_SHIELD_APP_ID；仅控制台勾选不生效 | <INTERNAL_REFERENCE_REMOVED>；<INTERNAL_REFERENCE_REMOVED>；<INTERNAL_REFERENCE_REMOVED> |
| B | A2A AgentCard 字段规范是什么？protocolVersion 支持哪些？ | ✅ 必填/可选字段清单；protocolVersion 限 0.2.6/0.3.0；protocolBinding 用 JSONRPC | <INTERNAL_REFERENCE_REMOVED> |
| B | Skills 中心地域限制与 Quota 是什么？ | ✅ 公测地域 cn-beijing/cn-shanghai；企业私有 SkillSpace 是 region 级隔离；Quota: Skill 400/Space 40/单空间绑定 50 | <INTERNAL_REFERENCE_REMOVED>；<INTERNAL_REFERENCE_REMOVED> |
| C | 观测 trace 回流配置方式与评估器类型？ | ✅ 回流步骤（可观测→数据回流→创建导出任务）+ 10万条上限 + ≥50 预置评估器 + LLM/Code 评估器 | 见 [PRODUCT]-observability/SKILL.md §11、[PRODUCT]-evaluation/SKILL.md §11 |
| C | 记忆 viking_mem 废弃状态与 AddSession 限制？ | 部分：viking_mem→viking 确认（生产推荐 viking/mem0）；100条上限内部资料/源码均未找到，标注待确认 | 见 [PRODUCT]-session-memory/SKILL.md §11 |
| C | 知识库 ContextSearch 配置与索引耗时？双引擎是什么？ | ✅ Viking + ContextSearch 双引擎统一检索网关；后端选项 8 种；文档级 ACL；索引增量更新约 2~3s（≤20s） | <INTERNAL_REFERENCE_REMOVED>；<INTERNAL_REFERENCE_REMOVED> |

> 各组件完整来源 URL 清单见对应 SKILL.md §11「来源追溯」表。

## 四、验证覆盖（精确区分验证层级与日期）

> **重要**：`docs/verification/results.json` 中的 84/84 通过为 **2026-09-18 历史离线验证**（test_imports.py + test_signatures.py + test_session_semantics.py + test_code_blocks.py，venv=Python 3.13.7 / [BASE-ADK] 1.1.13 / [PRODUCT]-sdk 0.8.7 / google-adk 2.2.0）。本轮（2026-09-22）未重跑 test_imports/test_signatures/test_session_semantics，仅引用其历史结论；本轮重跑的是 test_code_blocks.py（py_compile 语法级）。

| 验证类型 | 执行日期 | 覆盖情况 |
|---|---|---|
| YAML frontmatter 解析 | 2026-09-22（两轮均查） | ✅ 14/14 通过 |
| Markdown 代码围栏闭合 | 2026-09-22（两轮均查） | ✅ 14/14 通过 |
| Python 代码块 py_compile（test_code_blocks.py） | 2026-09-22 第二轮重跑 | ✅ 14 skills 扫描、15 块、15 通过 / 0 失败；交付前独立 compile 复核同为 15 块、0 语法错误 |
| 离线 import 路径（test_imports.py，25 项） | 2026-09-18 历史 | ✅ 25/25 通过（results.json）；本轮未重跑，引用历史结论 |
| 离线函数签名（test_signatures.py，36 项） | 2026-09-18 历史 | ✅ 36/36 通过（results.json）；本轮未重跑，引用历史结论 |
| 会话语义（test_session_semantics.py，8 项） | 2026-09-18 历史 | ✅ 8/8 通过（results.json）；本轮未重跑 |
| Batch C 额外离线探测 | 2026-09-22 | ✅ KnowledgeBase/LongTermMemory import + inspect 字段签名 + Agent(knowledgebase=) + _get_backend_cls 工厂（venv 实测） |
| Batch B 额外离线探测 | 2026-09-22 | ✅ identity-permission §3.3 两个 import 实测 PASS；guardrails `content_safety` 符号与 4 个回调字段确认存在且 Agent 构造成功；Runner.run 签名基线确认 |
| 真实云端集成验证 | 2026-09-22（审计修正） | ⚠️ 14 个组件均为 PARTIAL：共享 Runtime/A2A 明确落在 default 而非目标 <PROJECT_NAME>；模型输出受 RPM 429；多项仅完成创建、兼容性或复用资源验证。详见 `docs/cloud-validation/report.md` |

**验证脚本路径**（项目内相对路径，均已确认存在）：
- `docs/verification/test_imports.py`
- `docs/verification/test_signatures.py`
- `docs/verification/test_code_blocks.py`
- `docs/verification/test_session_semantics.py`
- `docs/verification/run_all.sh`
- `docs/verification/results.json`（2026-09-18 历史结果）

## 五、仍待确认项

1. **[BASE-ADK] 内置工具**：`web_search`/`image_generate`/`image_edit`/`video_generate` 的精确 import 子模块与函数签名未在离线测试覆盖
2. **adk-workflow**：Graph/Dynamic/Template 的无模型编排与 CreateAgentToolset 导入/签名已补证；仍未验证真实 LLM、暂停恢复/故障注入、Supervisor 运行时委派、CreateAgentToolset 资源权限与 Runtime/A2A 云端链路。
3. **[PRODUCT]-sandbox**：CLI 具体 flag（`--enable-snapshot` 等）、OpenAPI `CreateTool.ToolType` 枚举取值未在本机跑 `--help` 实测
4. **[PRODUCT]-knowledge-base**：按 user_id 文档级 ACL 在 SSO 同角色共用账号场景的实际隔离效果需联调；初始全量建库耗时未单独核证
5. **[PRODUCT]-session-memory**：「AddSession 单次 100 条上限」内部资料/源码均未找到依据；ShortTermMemory 各后端并发/容量上限未核证
6. **[PRODUCT]-evaluation**：评测集上限内部口径 5000 vs 1 万行不一致（已标"以控制台为准"）；轨迹/过程白盒化评测为路线图/灰度能力
7. **[PRODUCT]-observability/evaluation**：APMPlus OpenAPI 字段为浏览器 DOM + API Explorer 读取，未用 AK/SK 真实调用验证
8. **全部组件**：云端联调（真实 Runtime 调用、MCP 握手、记忆落库、知识库检索、观测数据上报）均未实测

## 六、未触碰范围

- 未修改 `server/`、`web/`、`vendor/`、`design/`、`deploy/`、`deployment-state/`、`frontend/`、`tests/`、`[DELIVERY]_data/` 等无关目录
- 未读取或传播 `.env` / 真实凭证
- 未全局安装 Skills 或发布到其他账号/云盘
- 本轮已使用真实火山凭据执行部分云端动作，但 14 项均未满足完整 PASS 门禁；详细未验证边界以 `docs/cloud-validation/report.md` 为准。

## 七、交付包与使用边界

- 权威文件位于 `/home/user/Documents/[PRODUCT]_dev_skills/skills/`，按组件打开各目录的 `SKILL.md`。
- `[PRODUCT]-skills-delivery-2026-09-22.zip` 是项目内增量快照。第三轮同步后实际文件数以压缩包清单为准，其中包含 14 个组件 SKILL.md、1 个模板、6 个公共验证脚本/历史结果文件、1 个变更说明，以及 adk-workflow 新增的 1 个离线验证脚本；目录条目不计入文件数。
- 压缩包不是自包含安装包：Skill 中引用的其他项目文档、SDK 依赖与运行环境没有全部打包。优先在原项目中使用；迁移前需逐项补齐相对引用与依赖，不要直接运行未经审阅的验证脚本。
- 第三轮交付前检查结果见最终回复与压缩包清单；它覆盖结构、Python 代码块语法、ADK 无模型示例、ZIP CRC 和项目文件哈希。这些检查不代表真实模型、恢复语义、云服务行为或业务正确性已全部验证。
- 安全围栏接入阻塞已部分解除：2026-09-22 云验证中离线源码复测确认 [BASE-ADK] 1.1.13 实际导出 `content_safety`（位于 `[BASE-ADK].tools.builtin_tools.llm_shield`，4 回调齐全），导入需配置 `TOOL_LLM_SHIELD_APP_ID`（必填）及可选 region/api key。云端回调挂载与真实拦截行为仍未验证。详见第八节。

---

### 最终交付前审计补充
- 14 个 Skill 的 YAML frontmatter 已统一为当前加载规范允许的 `name + description`；旧版完整 frontmatter 已备份到 `_backup/cloud-validation/frontmatter-before-normalize/`，不进入交付包。
- `quick_validate.py`：14/14 Skill 通过。
- `test_code_blocks.py`：14 Skill、18 个 Python 代码块，18/18 通过；新增的第 18 块为 guardrails 四回调挂载示例。
- Guardrails 固定版构造验证：`Agent` 四个 callback 字段存在，`content_safety` 四个回调均可调用，挂载后 Agent 构造成功；真实 LLM Shield 请求与云端拦截仍未验证。
- 云验证结构化证据统一为组件状态 `PARTIAL`；清理了未交付 scratch，脱敏了复用资源名称。
- 控制台删除 CR 镜像需要登录，用户接管请求超时；该测试 tag 仍列为唯一残留，未伪造清理成功。

---

## 八、真实火山云验证 + 审计修正（2026-09-22 下午）

### 验证概要
- **目标目录**: `skills/`（14 个组件）
- **Region**: cn-beijing
- **CLI**: [PRODUCT] 0.52.13
- **隔离 venv**: Python 3.13.7, [BASE-ADK] 1.1.13, [PRODUCT]-sdk 0.8.7, google-adk 2.2.0
- **最终统计**: **0 PASS / 14 PARTIAL / 0 BLOCKED / 0 FAIL**

### 关键环境偏差
- 用户指定 project=<project>；共享 Runtime 与 A2A 资源实际落到 project=default，不符合目标环境。Memory/Knowledge 创建命令显式传入 `-p <project>`，但返回记录没有可独立核验的 Project 回读字段，因此只标“归属未确认”，不再笼统声称全部资源都在 default。
- 共享账号 98 Runtime 并发导致模型端点持续 429 RateLimitError（RPM 超限），所有需模型输出的调用链路可达但输出被配额阻塞。

### 第一轮验证（3 分片并行）
- **分片 A**（[BASE-ADK]/sdk/workflow/runtime）：离线全过；runtime 管理闭环（update→release→回滚）实测通过；模型链路均到达 API 但 429。
- **分片 B**（sandbox/skills/memory/knowledge）：sandbox 复用现有 tool 完成 shell 调用+同 session FS 复用；skills upload 创建并删除；memory/KB 创建并删除；RAG/记忆读写受模型 RPM 阻塞。
- **分片 C**（gateway/a2a/identity/guardrails/obs/eval）：gateway 复用现有 MCP 服务完成四层握手+入站鉴权矩阵；a2a Space/Agent 创建并删除；identity 入站认证矩阵；guardrails 离线证伪 content_safety 未导出论断；observability APMPlus OpenAPI 只读调用；evaluation 评测集/评估器 CRUD。

### 审计修正（MainAgent 审计后）
1. **状态降级**：原 4 个 PASS（runtime/a2a/identity/observability）全部降级为 PARTIAL。
2. **project default 事实前置**：报告开头明确声明环境偏差。
3. **CR 镜像清理**：DeleteTag OpenAPI 所有参数组合返回 ResourceNotFound，列为残留，需控制台手动删除。
4. **复用资源重分类**：sandbox/gateway/observability/identity 的复用证据明确标注。
5. **Skill 文件修正**：
   - `[PRODUCT]-skills/SKILL.md`：修复 line 85 model_name 后缺逗号语法错误；重写 §3.2 为 CLI 0.52.13 真实命令，移除不存在的 `--skills` 可执行命令。
   - `[PRODUCT]-guardrails/SKILL.md`：修正"仅需 TOOL_LLM_SHIELD_APP_ID"过度表述；明确"勾选即生效"仅适用托管/低代码；标注云端回调/拦截未验证。
   - `[PRODUCT]-sandbox/SKILL.md`：quota 事实标注为本账号当时状态。
6. **备份迁移**：备份文件移至 `_backup/cloud-validation/`；组件目录 CHANGELOG.md 删除。
7. **交付产物修正**：report.md/runbook.md/evidence.json/resource-ledger.json 全部修正。
8. **凭据扫描**：无 AK/SK/Bearer/API key/token 实际值。
9. **scratch 清理**：/tmp 下所有验证临时文件已删除。

### 资源清理
- 9/10 资源已删除并回查确认
- 1 个 CR 镜像残留（需控制台手动删除）

### 产物
- 验证报告：`docs/cloud-validation/report.md`
- 资源账本：`docs/cloud-validation/resource-ledger.json`
- 证据：`docs/cloud-validation/evidence.json`
- Runbook：`docs/cloud-validation/runbook.md`
- 分片原始结果：`docs/cloud-validation/shard-{A,B,C}.json`

## 九、<PROJECT_NAME>补测与最终门禁审计

验证批次：<TEMP_PREFIX>-<suffix>；目标<PROJECT_NAME>/cn-beijing；固定SDK版本不变。

### 最终状态：0 PASS / 11 PARTIAL / 3 BLOCKED / 0 FAIL

- Memory与Skills初稿误报PASS，均降为PARTIAL：分别缺少真实跨会话记忆读写，以及SkillSpace绑定后的Runtime实际执行。
- Runtime、Sandbox、Knowledge为BLOCKED。CR构建错误、所探测模型429、Tool配额和CLI命令缺口均限定为本轮执行证据，不推断平台完全不支持。
- Graph模型探针实际未构造Workflow，本地Model not found不能归因为另一条Ark请求的429；错误探针保留工作记录但不进入交付。
- Project直接回读<PROJECT_NAME>的有7项平台资源；评测2项只有workspace摘要，严格归属未确认，不再声称全部回读ProjectName=<project>。
- 最终审计时TOS测试ZIP经长度/ETag匹配后单key删除204、HEAD回查404。本轮9个平台资源+1个TOS对象全部有清理记录；历史default CR标签残留未在本次删除。
- Runbook区分系统0.52.13与SDK附带0.8.7，修正memory/skills/eval语法与显式Project/Region要求；缺少关键输入即阻止写入。
- 从分片/合并证据中移除无关客户既有Runtime名称与ID；不纳入工作副本、错误探针、备份、依赖或凭据。

权威状态：`docs/cloud-validation-<PROJECT_NAME>/evidence.json`。
清理明细：`docs/cloud-validation-<PROJECT_NAME>/resource-ledger.json`。
详细报告与摘要：同目录`report.md`、`audit-summary.html`。
最终校验：同目录`audit-checks.json`。
本次是审计修正，不宣称14个Skill已全部完成真实云端验收。

## 2026-09-23 最终验收轮（<PROJECT_NAME> / cn-beijing）

### 状态统计
- PASS: 7（[BASE-ADK], [PRODUCT]-sdk, adk-workflow, [PRODUCT]-runtime, [PRODUCT]-session-memory, [PRODUCT]-knowledge-base, [PRODUCT]-observability）
- PARTIAL: 5（gateway-mcp, a2a-registry, identity-permission, guardrails, evaluation）
- BLOCKED: 2（sandbox, skills — 账号配额）
- FAIL: 0

### 关键突破
1. **CR build CLI bug 定位与绕过**: CLI 0.52.13 误报 "CR instance disappeared while waiting for Running"，volcenginesdkcr ListRegistries 确认实例实际 Running。绕过方案：GetAuthorizationToken → docker login → 本地 docker build → push → runtime update --artifact-url。
2. **全功能 Agent 镜像**: 构建含 LongTermMemory(viking) + KnowledgeBase(viking) + content_safety 4回调 + auto_save_session 的 Agent，镜像 [PRODUCT]/full-agent:202609231250。
3. **SDK 多轮修复**: basic agent 多轮不生效根因是未设 auto_save_session=True；修复后同 session 第二轮正确召回"你叫Alice呀"。
4. **记忆跨会话召回**: viking backend 初始化成功，写入"咖啡+豆豆"→新 session 同 user 召回→异用户返回"没有找到相关记录"。
5. **知识库 RAG 命中**: 修复 KnowledgeBase 缺少 backend_config={} 和 index（从 DATABASE_VIKING_COLLECTION env 读取）后，load_knowledgebase 工具自动挂载，查询返回唯一标记 <PROJECT_NAME>VERIFY2026X7。
6. **模型可用性**: 探测确认 doubao-seed-2-0-lite-260428 / mini 返回 200；此前 429 仅影响 doubao-seed-1-6-250615 等特定模型。

### SKILL 文件修改
- [PRODUCT]-skills/SKILL.md: line85 model_name 后缺逗号修复；CLI 章节重写为 0.52.13 真实路径（无 invoke --skills、无 skill-space 创建命令）
- [PRODUCT]-guardrails/SKILL.md: 旧版"1.1.13 未导出 content_safety"证伪修正为"已导出，需 TOOL_LLM_SHIELD_APP_ID 环境变量"
- [PRODUCT]-sandbox/SKILL.md: quota 标注为本账号当时状态（非产品限制）

### 关键发现（CLI/API 与文档偏差）
- knowledge create -p/--project 被忽略，项目由 --viking-project 决定
- knowledge 文档上传命令是 `add` 不是 `upload`
- content_safety 存在于 [BASE-ADK].tools.builtin_tools.llm_shield（模块级单例），非"未导出"
- mcp service create 所有 backend 都强制 --image-url
- identity authorizer/provider/policy 9 个 OpenAPI action 全 404（控制台能力）
- eval -p 仅 coze 生效，TEA 后端忽略
- observability 入口 span 实为 POST /invoke（非 agent_server_request）

### 资源清理
- 11/11 创建资源已删除（Runtime, KB, CR镜像×3, Skill, Memory, A2A×2, Eval×2）
- 3 项平台限制残留：UserPool（无删除API）、eval实验（无删除API）、viking collection（KB删除不级联）

### 未验证边界
- MCP 自建服务 + tools/call 真实调用
- A2A message/send（Standard-JSON 导入无 supportedInterfaces 端点）
- Identity 完整 authorizer 生命周期（9 API 404）
- Guardrails 云端真实拦截（需有效 LLM Shield App ID）
- Evaluation 终态分数（target 无 actual_output）
- Sandbox 自建 tool 生命周期（配额阻塞）
- Skills SkillSpace 发布绑定调用（配额阻塞）

---

## 〇-D、第五轮：最终验收轮（2026-09-23，自建全功能Agent + 真实云端验证）

### 验证范围
- 14组件在 project=<project> (cn-beijing) 真实云端端到端验证
- 自建全功能Agent镜像（LongTermMemory + KnowledgeBase + content_safety + auto_save_session）
- 自建MCP服务（Python MCP over HTTP, echo/add工具）
- 最终统计：PASS 6 / PARTIAL 6 / BLOCKED 2 / FAIL 0

### PASS 组件（6个）
1. [BASE-ADK]：真实模型输出（17+25=42, 颜色=Red），非硬编码
2. adk-workflow：validate_orchestration.py 8/8；真实Graph function→Agent模型节点（13×7=91）；动态路由
3. [PRODUCT]-runtime：创建(<PROJECT_NAME>)→发布→Ready→invoke成功→版本可逆变更→日志取证→清理
4. [PRODUCT]-session-memory：创建(<PROJECT_NAME>)→绑定→写入→跨session召回(蓝色/豆豆)→异用户隔离→清理
5. [PRODUCT]-knowledge-base：创建(--viking-project <PROJECT_NAME>)→上传文档(<PROJECT_NAME>VERIFY2026X7)→绑定→RAG命中→清理
6. [PRODUCT]-gateway-mcp：自建MCP→四层握手→鉴权矩阵(无/错→401,有效→200)→清理

### PARTIAL 组件（6个）
1. [PRODUCT]-sdk：入站契约PASS；同session多轮上下文未持久化
2. [PRODUCT]-a2a-registry：Space/Agent创建+A2A格式兼容；真正网关message/send受平台限制
3. [PRODUCT]-identity-permission：UserPool创建+入站认证矩阵；authorizer CRUD OpenAPI 404，无删除路径
4. [PRODUCT]-guardrails：离线content_safety 4回调；云端围栏未真正生效（LLM Shield App需控制台）
5. [PRODUCT]-observability：Runtime日志可检索；APMPlus OpenAPI所有端点404
6. [PRODUCT]-evaluation：评测集/评估器/实验已提交；终态分数未确认，<PROJECT_NAME>归属未确认

### BLOCKED（2个，需用户介入）
1. [PRODUCT]-sandbox：QuotaExceeded.Tool（本账号tool配额已满）
2. [PRODUCT]-skills：QuotaExceeded.skillspace（当前11个空间）

### 新增源码文件
- reference-agents/full-feature-agent/ (agent.py + Dockerfile)
- reference-agents/mcp-test-server/ (server.py + Dockerfile)
- reference-agents/a2a-test-server/ (server.py + Dockerfile)

### 关键技术发现
- 两套CLI：系统0.52.13 vs venv 0.8.7，必须用绝对路径
- CR build CLI误报disappeared，改用docker build+push
- 镜像必须linux/amd64
- knowledge create -p被忽略，项目由--viking-project决定
- Runtime不支持agent card（API/CLI创建）

### 资源清理
- 13/15项已清理（87%）
- 2项残留：UserPool（无删除API）、Viking collection（不级联删除）

### 安全修复
- runbook.md移除/tmp/cr_token.json落盘，改用隔离DOCKER_CONFIG+--password-stdin
- 凭据扫描通过：无AK/SK/Bearer/API key泄露
