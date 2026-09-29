# 迭代2 最终总结报告（final_iteration2_report）

- 报告时间：2026-09-28（CST）
- 报告性质：**只写报告，未修改任何代码/Skill**。全部数字与结论来自本仓库既有证据文件（journal / audit / iteration2 各产物），未联网、未读取任何秘密文件。
- 统一验证证据：`iteration2/verification/verify_report.json`（generated_at `2026-09-28T22:35:16`，`ok: true`）。

---

## 1. 执行范围

本轮（迭代2）在第一轮"14 组件全量 Harness + 独立审计"基线上，做了三件事并收口为一次机器可复验：

1. **Skill 文档修正与瘦身**：依据 `audit/audit_report.md` 不足清单完成正式 Skill 修正（B1/H1/H2/H3/M3 + 基准产物 M1/M2），并把 ~12 个 Skill 里重复的 Runner/SSE/签名验证样板收敛为共享 reference（证据：`audit/fix_log.md`、`iteration2/reports/template_inventory.md`、`iteration2/reports/skill_refactor_log.md`）。
2. **离线安全防护（Slice B）**：在 `harness/c09_sandbox.py` 内自包含实现默认拒绝（deny-by-default）的应用层 guard，并提供进程内 `guard.py` 与 13 个正负向测试（证据：`iteration2/security/README.md`、`tests/test_sandbox_security.py`）。
3. **评测/知识库实证回写（Slice D）+ 冷启动复验**：在严格离线（导入即剥离 VOLCENGINE/ARK/AK/SK/API_KEY/DATABASE/TOOL_CODE 等环境变量）条件下探测 eval SDK 与 KB local 后端，把"local ≠ 离线可用"等实证结论回写进对应 Skill；随后做了一次 clean-room 冷启动复验（证据：`iteration2/evaluation/evidence/*`、`iteration2/cold_start/cold_start_journal.md`、`result.json`）。

**钉版环境基线**（全程一致）：Python 3.12.14（uv 安装）、`veadk-python==1.1.13` + `veadk-python[extensions]==1.1.13`、`agentkit-sdk-python==0.8.7`、`google-adk==2.2.0`、`mcp==1.26.0`、pytest 9.1.1、公开 `agentkit-cli 0.52.13`。已知无害告警：`google-adk==2.2.0` 的 `BaseAgentConfig` DeprecationWarning（4 条，未被静默）。

---

## 2. 已修复项逐条对应用户 10 点

| # | 用户 mandate 点（以审计不足清单 + 迭代2 切片为据） | 修复内容 | 证据 | 状态 |
|---|---|---|---|---|
| 1 | 离线 local 后端漏 `[extensions]`（B1，Blocker） | veadk / session-memory / knowledge-base §2 依赖段均补：本地/离线用 `backend="local"` 必须 `uv add 'veadk-python[extensions]==1.1.13'`，裸装构造 local 后端会 ImportError；session-memory 另补基础包行 | `audit/fix_log.md` 表 B1；`skills/README.md` §4 | ✅ 已修 |
| 2 | a2a CLI 与公开 0.52.13 漂移未收口（H1） | a2a-registry §3.2 顶部新增「CLI 版本前提」警示框：内部命令未在公开 CLI 实测，先 `agentkit --version`，不支持则走 §3.4 控制台或 §3.5 SDK | `fix_log.md` 表 H1；`skill_refactor_log.md` §2 保留项 | ✅ 已修 |
| 3 | 无跨 Skill 导航（H2） | 新增 `skills/README.md`：依赖分层图、5 阶段阅读顺序、14 篇"离线可跑 vs 必须云凭据"对照表、统一版本基线、6 条跨件关键约束 | `fix_log.md` 表 H2；`backup_skills/README.md`（该导航文件本体） | ✅ 已修（冷启动第二轮首读即此文件） |
| 4 | identity 两套钉版易装错（H3） | §2 明确 0.8.7 为新项目默认/推荐、0.6.2 仅历史教学复现；§3.3 私有 import 标注"仅诊断/联调" | `fix_log.md` 表 H3 | ✅ 已修 |
| 5 | sdk 示例写死 `/data/sessions.db`（M3） | 默认改为 `sqlite+aiosqlite:///./.sessions.db`（相对路径，本地免 root）；生产绝对路径写法保留在注释 | `fix_log.md` 表 M3 | ✅ 已修 |
| 6 | c05 skills 零行为测试（M1）+ c12 措辞高估（M2） | 新增 `tests/test_skills.py` 6 用例（`skills_field_from_env` 设/未设/去空白、Registry publish/list/execute、missing KeyError、unknown space）；c12 覆盖描述改为"真实构造 + 本地词法桩检索" | `fix_log.md` 表 M1/M2；`journal/pytest_output.txt`（34→40） | ✅ 已修 |
| 7 | 重复 SSE/inspect 样板冗余（M4/L3） | 12 个正式 Skill 瘦身：删除注释掉的 SSE 块与 inspect 行，改为跳转 `skills/references/runner-entrypoint.md` + 可执行 `verify_runner_signature.py`；独有约束一字未删 | `template_inventory.md` §1/§4；`skill_refactor_log.md` §1（3359→2980 行，净 −379）、§3（9/9 相对链接无断链）、§4（范围内零残留） | ✅ 已修 |
| 8 | CloudBoundary 只是人工约定、无机器强制（L4 升级） | `harness/c09_sandbox.py` 四层 deny-by-default：出站 TCP connect、云写 CLI（aws/gcloud/tosutil/huggingface/twine/npm/docker/git push）、秘密路径读取（~/.zshrc、~/.aws、~/.ssh 等）、read-only 写；默认全阻断，逐层 `allow_*` 或 master env 解除；另附进程内 `guard.py` fixture | `iteration2/security/README.md` 矩阵；`verify_report.json` benchmark_tests 含 13 个安全用例（40+13=53） | ✅ 已修（应用层，见 §5 边界声明） |
| 9 | evaluation 代码可复制性低（评分 2/5）+ KB "local 可离线"误导 | 实证探测：KB `backend="local"` 构造需 Ark token（FileNotFoundError）、`add_from_text` 走 embedding HTTP（APIConnectionError）——结论回写 knowledge-base Skill；本地实现 reference 评测（ExactMatch + token_overlap_stub）9 个测试；官方 google.adk PrebuiltMetrics 全部 LLM/Vertex 后台、veadk BaseEvaluator 需 LLM，标注为云边界 | `iteration2/evaluation/evidence/kb_local_probe.txt`、`eval_sdk_probe.txt`、`local_eval_report.json` | ✅ 已修 |
| 10 | 无统一验证入口、冷启动效果未复验 | 新建 `iteration2/verification/verify_all.py`（6 项机器检查：结构/代码块/pytest 三套件/秘密扫描/重复 Skill/相对链接），输出 `verify_report.json`；并完成第二次 clean-room 冷启动 | `verification/README.md`；`verify_report.json`（`ok: true`）；`cold_start/result.json` | ✅ 已修 |

**本轮明确未做、如实标注**（见 `fix_log.md` §未修正项）：M4 之外的逐文件大改已在第 7 点完成；evaluation 引入真实 eval SDK 重写示例超出范围（仅做边界标注与本地 reference）；L1–L3 低优先项（journal 小错、inspect 收敛已随第 7 点完成）保持现状。

---

## 3. 当前统一验证数字（verify_report.json，2026-09-28 22:35:16）

六项检查全部 `ok: true`，总退出码 0：

| 检查项 | 数字 | 结果 |
|---|---|---|
| skill_structure | 正式 `skills/` 目录 14/14：SKILL.md 存在、frontmatter 含 name+description、name 与目录名一致 | ✅ |
| code_blocks | 扫描 32 个文件、74 个围栏块、4 个占位符骨架跳过；```python 块 `compile()` 全过、```yaml 块解析全过 | ✅ 0 失败 |
| pytest · benchmark_tests（`tests/`） | **53 passed / 0 failed**，11.2s（尾部：53 passed, 4 warnings in 10.33s） | ✅ rc=0 |
| pytest · iteration2_evaluation | **9 passed / 0 failed**，102.3s（KB 导入较慢，可容忍） | ✅ rc=0 |
| pytest · iteration2_cold_start | **7 passed / 0 failed**，3.7s | ✅ rc=0 |
| secret_scan | 6 类模式（aws AKIA / 私钥块 / GitHub / Slack / OpenAI / aws_secret 赋值）命中 **0**；只报 file:line+模式名，从不打开 `~/.aws`、`~/.ssh`、shell profile | ✅ |
| duplicate_skills | 扫 14 个 Skill 目录：无重名、无内容哈希重复（已排除 backup_skills/\_backup/.venv/.git/缓存/zip） | ✅ |
| reference_links | 正式 Skill 内 Markdown 相对链接 **9 条全落盘**，0 断链 | ✅ |

**合计 69 个 pytest 用例（53+9+7）全部通过**。对比第一轮验收基线 40 passed：增量 13 个全部来自 Slice B 安全防护用例（`tests/test_sandbox_security.py`），无回归。

---

## 4. 第二次冷启动 vs 第一次：量化对比（注意任务规模不同，仅作方向性判断）

| 指标 | 第一次（`journal/execution_journal.md`） | 第二次（`iteration2/cold_start/result.json`） | 变化 |
|---|---|---|---|
| 起止时间 | 2026-09-28 17:05:49 → 17:23 | 2026-09-28 22:18:02 → 22:28:03 | — |
| 总耗时 | 约 **18–19 分钟**（含下载 Python 3.12.14 的 2m43s 环境搭建） | **10.0 分钟** | 方向性缩短 |
| 工具轮次（估算） | 约 **30 轮** | **21 轮** | 方向性减少 |
| 读了几篇正式 Skill | **14 篇全读** | **6 篇**（veadk / session-memory / knowledge-base / sandbox / observability / adk-workflow）；首读入口 `skills/README.md`，未读其余 8 篇 | 14→6 |
| 交付测试 | 首跑 32/2 → 修复后 **34 passed**；基准验收后补 skills 测试到 **40 passed** | **7 passed / 0 failed**（2.75s） | 34/40 vs 7 |
| 环境搭建 | 从零建 venv、装钉版依赖、踩 py3.14→3.12 坑 | 直接复用既有 `.venv`（Python 3.12.14） | 第二次不含环境成本 |
| 离线姿态 | 未显式剥离云环境变量 | **导入即剥离** VOLCENGINE/ARK/AK/SK/API_KEY/DATABASE/TOOL_CODE | 第二次更严格 |

**必须声明的口径限制（不能过度归因）**：

- **任务规模根本不同**：第一次是**全量 14 组件 Harness**（16 个 .py 模块 + 7 个测试文件 + 总装流水线）；第二次是一个**小场景（≥3 组件、实际 5 组件）的离线集成系统**（veadk 底座 + adk-workflow 条件路由 Graph + 子进程沙箱 + 内存 span recorder + ExactMatch 评测），且主动放弃了 memory/KB 真读写（见 §5）。
- 因此 19→10 分钟、30→21 轮、14→6 篇 Skill 的**改善不能直接等同于"Skill 套件效率提升了 X%"**；它只能支持一个方向性结论：**新增的 `skills/README.md` 导航入口 + 离线/云对照表，让一个干净室代理不再需要全读 14 篇即可选定 6 篇并跑通 7 个测试**。
- 两组数字的"测试通过率"也不可比：40 测的是全量契约桩+真跑，7 测的是小场景离线行为。共同可信的点是：**两次都 0 failed、0 云凭据使用、0 明文秘密**。

---

## 5. 仍受产品/凭据限制（CloudBoundary，本轮未也无法在本环境突破）

1. **`veadk.Agent` 裸构造即触发 `model_post_init → get_ark_token()`** 抛 FileNotFoundError；冷启动用显式占位 `model_api_key="local-offline-placeholder-not-a-secret"`（非真密钥、不发网络）绕过构造——真实模型调用仍必须云凭据。
2. **`LongTermMemory(backend="local")`** 在剥离凭据环境下构造期抛 FileNotFoundError（要 AK/SK / VeFaaS IAM file `/var/run/secrets/iam/credential`）；冷启动据此放弃真实记忆读写。
3. **`KnowledgeBase(backend="local")`** 实证（`kb_local_probe.txt`，2026-09-28T12:09Z）：内存存储但 embedding 走 Ark 云端点——构造即 FileNotFoundError；即便绕过构造，`add_from_text` → `APIConnectionError`、`search` 不可用。**"local"只代表本地内存索引，不代表离线可召回**，此结论已回写 Skill。
4. **真云沙箱**：`veadk.tools.sandbox.code_sandbox` 导入即要求 `TOOL_CODE_SANDBOX_URL`；本地只以 `subprocess` 复现"同 session FS 复用 / 跨 session 隔离"语义。
5. **安全 guard 的诚实边界**：`iteration2/security/README.md` 明确——这是**应用层 Python 解释器内补丁**，不是内核级沙箱（macOS 无 seccomp/landlock）；原始 syscall 绕过、DNS（UDP/53）、ICMP 不在拦截承诺内；guard 只匹配路径字符串、从不打开秘密文件本身。
6. **评测云边界**：`google.adk.evaluation` 的 PrebuiltMetrics（response_match/rubric/hallucinations/tool_trajectory/user_simulator/multi_turn_*）全部 LLM/Vertex 后台，无离线确定性指标；`veadk.evaluation.BaseEvaluator.generate_outputs` 需跑 agent → 需 LLM/凭据。本地产出仅为 reference/contract 跑分。
7. 其余第一轮即标注的云写动作本轮原样保留为 CloudBoundary：Runtime Create/Release/Invoke 真调用、远端 MCP_ENDPOINT、A2A 注册到空间、LLM Shield 真拦截（缺 `TOOL_LLM_SHIELD_APP_ID` 抛 ValueError 已实测）、APMPlus OpenAPI 查询、在线评测平台。
8. `mem0ai==0.1.118` 未安装，mem0 后端路径不可用。

---

## 6. 新发现与回写（相对第一轮的增量）

1. **KB/LTM "local 后端"口径修正（最重要）**：第一轮在未剥离凭据环境下构造 `LongTermMemory(local)`/`KnowledgeBase(local)` 成功；第二轮严格离线实证证明其 embedding/凭据路径仍在云端。差异根源是冷启动时**导入即剥离云环境变量**——已回写 `knowledge-base` Skill 为"local ≠ 离线可用"，并在 `skills/README.md` §3 离线表里保留了"真构造 vs 云读写"的区分表述，避免新手把"能 new 出来"误读为"能离线召回"。
2. **veadk.Agent 离线构造法**：显式传 `model_api_key` 优先级最高，可用占位串跳过 `get_ark_token()` 完成离线构造（`issubclass(Agent, LlmAgent)=True` 已验）。这是第一轮不知道、第二轮探出来的可复用技巧。
3. **Python 教学级坑**：`__main__` 里实例变量命名 `sys` 会遮蔽 `import sys`，导致子进程 `sys.executable` 解析失败——改名 `system` 解决（冷启动返工记录）。
4. **ADK 节点返回值落点**：纯 `@node` 函数返回字符串进 `event.output` 而非 `content.parts[].text`，取值需"text 优先、否则回退 `str(event.output)`"。
5. **文档瘦身收益实测**：12 个 Skill 从 3359 行压到 2980 行（净 −379），同时 9 条相对链接零断链、独有约束（400 规则、四层 MCP 验收、§10.5 云校正、0.52.13 CLI、单次 trace vs 聚合铁律等）grep 全部命中保留——证明样板收敛没有牺牲组件特有知识。
6. **机器安全 guard 有效但层级有限**：负向（默认拦 `EgressBlocked`）与正向（解除后同一代码抛真实 `OSError/gaierror` 而非 `EgressBlocked`）成对证明阻断来自 guard 本身而非环境无网；13 个测试锁死。

---

## 7. 产物清单（本轮交付全部落在 `benchmark_20260928/iteration2/` 与正式 `skills/` 目录）

**iteration2 目录内**：
- `reports/template_inventory.md`、`reports/skill_refactor_log.md`、`reports/final_iteration2_report.md`（本文件）
- `security/`：`README.md`（四层 deny 矩阵）、`guard.py`（进程内 fixture）、`__init__.py`
- `verification/`：`README.md`、`verify_all.py`（6 项检查）、`verify_report.json`（机器可读结果）
- `cold_start/`：`cold_start_agent.py`（离线集成系统）、`test_cold_start.py`（7 测）、`cold_start_journal.md`、`result.json`、运行时生成的 `workspaces/`
- `evaluation/`：`evidence/{kb_local_probe.txt, eval_sdk_probe.txt, local_eval_report.json}`、`reference/reference_eval.py`、`scripts/{probe_kb_local.py, run_local_eval.py}`、`tests/{test_kb_local_contract.py (4), test_local_eval_reference.py (5)}`、`pre_edit/`（evaluation + knowledge-base 改前备份）
- `backup_skills/`：14 个正式 Skill 改前原样备份 + 导航 README + 模板（未新建备份目录，复用此处）

**正式 `skills/` 目录内（文档侧交付）**：
- 新增 `skills/README.md`（总入口导航）
- 新增 `skills/references/runner-entrypoint.md` + `verify_runner_signature.py`（chmod +x）
- 新增 `agentkit-observability/references/span-attributes-and-query-api.md`、`agentkit-a2a-registry/references/agentcard-schema.md`、`agentkit-identity-permission/references/e2e-acceptance.md`
- 12 个正式 Skill 的 §2/§3 按 §2 表修正与瘦身（evaluation/knowledge-base 由 Slice D 改，含 KB 离线回写）

---

## 8. 复现命令（在 `agentkit_dev_skills/` 根目录执行）

```bash
# 0) 统一验证入口（推荐先跑这一条；6 项检查全过才退出码 0）
benchmark_20260928/.venv/bin/python \
  benchmark_20260928/iteration2/verification/verify_all.py

# 1) 第一轮全量基准测试（53 passed）
benchmark_20260928/.venv/bin/python -m pytest benchmark_20260928/tests -q

# 2) 安全防护专项（13 个正负向用例）
benchmark_20260928/.venv/bin/python -m pytest \
  benchmark_20260928/tests/test_sandbox_security.py -q

# 3) 评测/知识库离线契约测试（9 passed；KB 导入较慢约 100s）
benchmark_20260928/.venv/bin/python -m pytest \
  benchmark_20260928/iteration2/evaluation/tests -q

# 4) 第二次冷启动场景测试（7 passed）
benchmark_20260928/.venv/bin/python -m pytest \
  benchmark_20260928/iteration2/cold_start/test_cold_start.py -v

# 5) Runner 钉版签名自检（exit=0 即三契约断言全过）
benchmark_20260928/.venv/bin/python \
  benchmark_20260928/../skills/references/verify_runner_signature.py
#   注：正式 skills/ 目录位于仓库根，按实际安装路径替换；等价于
#   python -m skills.references.verify_runner_signature

# 6) KB 离线实证探针（复现"local ≠ 离线可用"）
benchmark_20260928/.venv/bin/python \
  benchmark_20260928/iteration2/evaluation/scripts/probe_kb_local.py
```

预期：全部命令退出码 0；`verify_all.py` 输出与 `verify_report.json` 一致（14/14 结构、74 块 0 失败、69 用例 0 failed、秘密 0 命中、9/9 链接）。任何真实云写动作在本环境都会被 guard 或 CloudBoundary 拦在边界，不会创建云资源。
