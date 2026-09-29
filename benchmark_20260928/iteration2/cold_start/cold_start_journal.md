# Cold Start 复验日志（clean-room）

- 开始时间：2026-09-28 22:18:02 CST
- 结束时间：2026-09-28 22:28:03 CST
- 总耗时：约 10.0 分钟
- 工具轮次估算：约 21 轮（含探测/读 Skill/写码/跑测/返工）
- 环境：`benchmark_20260928/.venv/bin/python`（Python 3.12.14，veadk-python==1.1.13，google-adk==2.2.0，agentkit-sdk 0.8.7，pytest 9.1.1）
- 安全姿态：全程离线；模块导入即剥离 VOLCENGINE/ARK/AK/SK/API_KEY/DATABASE/TOOL_CODE 等环境变量；未读 shell profile/Cookie/JWT；未创建/调用任何云资源；所有写入仅落在 `iteration2/cold_start/`。
- 未读：`journal/`、`audit/`、`iteration2/reports/`、`iteration2/backup_skills/`、benchmark harness 源码；未先读统一 verify_all 实现。

## 1. 先读入口 README，再按需选 Skill

入口：`skills/README.md`（依赖分层图 + 离线/云凭据表 + 跨组件约束）。

据此先做实证探测（venv 实际可 import 的符号），再决定读哪些正式组件 Skill。

### 实际读取的正式组件 Skill（共 6 篇，未全读 14 篇）

| Skill | 为什么读 / 用途 |
|---|---|
| `veadk` | 底座层：搞清楚 `veadk.Agent`/`Runner` 主体与离线边界。 |
| `agentkit-session-memory` | README 离线表称 `LongTermMemory(backend="local")` 可真构造，需核实。 |
| `agentkit-knowledge-base` | 同上，核实 `KnowledgeBase(backend="local")` 能否离线召回。 |
| `agentkit-sandbox` | 核实"子进程真执行 + 同 session FS 复用/隔离"的离线语义边界。 |
| `agentkit-observability` | 核实"内存 span recorder / 单次 trace vs 聚合分离"离线能力。 |
| `adk-workflow` | README 称 google-adk 2.2.0 Graph/Join/Dynamic 无模型真跑；需要正确的离线 Graph/运行引导。 |

另读了 `adk-workflow/scripts/validate_orchestration.py`（该 Skill 自带的离线验证脚本）仅用于学习 `InMemorySessionService + Runner + run_async` 的正确引导写法，随后自写场景，未照抄为答案。

### 未读的 8 篇
agentkit-sdk、agentkit-runtime、agentkit-skills、gateway-mcp、a2a-registry、agentkit-guardrails、agentkit-identity-permission、agentkit-evaluation（评测指标改用对 google.adk.evaluation 的实证探测 + 自实现 ExactMatch）。

## 2. 关键探测与结论（实证，非猜测）

- `veadk.memory.LongTermMemory(backend="local")` **构造期即抛** `FileNotFoundError`（找 AK/SK / VeFaaS IAM file）——和 KB 同类："local"只是内存存储，embedding/凭据仍走云端。**放弃真实记忆读写**。
- `KnowledgeBase(backend="local")`：该 Skill 末尾 iteration2 实测回写已明确"local ≠ 离线可用"（embedding 仍走 Ark 云端点），**不假装召回成功，放弃 KB**。
- `veadk.tools.sandbox.code_sandbox` 导入即要求 `TOOL_CODE_SANDBOX_URL`（云沙箱）；改用本地 `subprocess` 实现 sandbox SKILL §1/§8 的离线语义。
- `veadk.Agent()` 裸构造即触发 `model_post_init → get_ark_token()` 抛 FileNotFoundError。

## 3. 首次失败与返工/绕路

1. **LongTermMemory(local) 构造失败**（FileNotFoundError）→ 绕路：放弃 memory 真读写，不纳入场景。
2. **KnowledgeBase local 不可离线召回**（Skill 自述）→ 放弃 KB，避免假造召回。
3. **`veadk.Agent(...)` 裸构造要云 token** → 返工：按其源码注释"显式 model_api_key 优先级最高"，传本地占位串 `model_api_key="local-offline-placeholder-not-a-secret"`（非真实密钥、不发网络，已实测），构造离线成功，`issubclass(Agent, LlmAgent)=True`。
4. **`__main__` 里实例变量命名 `sys` 遮蔽了 `import sys`**，导致子进程里 `sys.executable` 报 `'OfflineAgentSystem' object has no attribute 'executable'` → 返工：实例改名 `system`。
5. **节点返回串进了 `event.output` 而非 `content.parts[].text`**，导致结果文本为空 → 返工：按 SKILL 参考的合并方式（text 优先，否则回退 str(output)）返回。

## 4. 未经 Skill 支撑的猜测（已自我修正/标注）

- 起初按 README 乐观表以为 memory/KB 的 `backend="local"` 可直接离线读写；实证（+ KB Skill 自述）证明是云 embedding 陷阱，已改正为不纳入。
- 对 `UnsafeLocalCodeExecutor.execute_code(invocation_context, code_execution_input)` 的重型 `InvocationContext` 构造，没有硬猜；改用本地 `subprocess` 忠实复现 sandbox 文档化离线语义。
- 沙箱 session FS 用"按传入 session_id 键控的工作目录"本地实现（对应 SKILL 的"同 session 复用、跨 session 隔离"），属本地最小实现，未冒充云沙箱。

## 5. 因 Skill 指引避免的问题

- 用 `google.adk` 而非 `veadk.workflow` 导入编排原语（adk-workflow §1：`veadk.workflow` 不存在）。
- 节点用纯 `@node` 函数、不调模型；运行用 `InMemorySessionService + Runner.run_async`（来自 Skill 参考脚本的引导写法），而非自己猜 Context 构造。
- 不把 README"local 后端"误当离线可用；KB Skill 回写直接避免了"假造召回成功"。
- 不写 AK/SK 明文；显式占位 key 仅为满足本地构造、不触网。

## 6. 产物与验证

产物（均在 `iteration2/cold_start/`）：
- `cold_start_agent.py`：离线集成系统（veadk 底座 + adk-workflow 条件路由 Graph + 子进程沙箱 + 内存 span recorder + ExactMatch 评测）。
- `test_cold_start.py`：7 个 pytest。
- `workspaces/`：sandbox 会话工作目录（运行时生成）。

实际运行：`pytest test_cold_start.py -v` → **7 passed, 0 failed**（2.75s）。
