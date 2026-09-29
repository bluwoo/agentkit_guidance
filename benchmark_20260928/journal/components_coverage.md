# 组件覆盖矩阵（components_coverage）

覆盖状态图例：
- **完整（真实）**：本地真实运行/构造，不依赖云。
- **Mock/契约桩**：用本地桩复现接口契约，云端行为标注边界。
- **边界标注**：该组件的核心写/调用必须云凭据，Harness 只到"需要凭据"这一边界。

| # | 组件 | 实现文件 | 对应测试 | 覆盖状态 |
|---|---|---|---|---|
| 1 | veadk | `harness/c01_veadk.py` | `test_components_import.py`、`test_integration.py` | **完整（真实构造）**：真实 `veadk.Agent` 可构造；`Runner.run` 用 `ScriptedRunner` 复现 `run(messages=,user_id=,session_id=)->str` 契约；真实 LLM 调用=边界标注 |
| 2 | agentkit-sdk | `harness/c02_sdk_app.py` | `test_sdk_runtime.py` | **完整**：`@entrypoint/@ping/app.run` 契约 + 缺 user/session_id 返回 400（不回落 default） |
| 3 | agentkit-runtime | `harness/c03_runtime.py` | `test_sdk_runtime.py`、`test_integration.py` | **Mock/契约桩 + 边界**：Runtime 描述子、OpenAPI 清单、`/invoke` curl 契约；Create/Release/Invoke 真调用=边界标注 |
| 4 | adk-workflow | `harness/c04_workflow.py` | `test_workflow.py` | **完整（真实运行）**：真实 google-adk==2.2.0 Graph 路由/并行 Join/Dynamic，无模型跑通 |
| 5 | agentkit-skills | `harness/c05_skills.py` | `test_components_import.py`、`test_skills.py` | **Mock/契约桩 + 行为测试**：SkillSpace/Skill 注册、`skills=[SKILL_SPACE_ID]` 加载门（`skills_field_from_env` 设/未设两种情况已测）、`execute_skill` 正常与 KeyError 路径；真实 upload/ListSkillsBySpaceId=边界标注 |
| 6 | agentkit-session-memory | `harness/c06_memory.py` | `test_memory_kb_obs_eval.py` | **完整（真实 local 后端）**：真实 `LongTermMemory(backend="local")` + 三层记忆本地实现 + `save_session_to_long_term_memory`；mem0/viking=边界标注 |
| 7 | agentkit-gateway-mcp | `harness/c07_mcp_gateway.py` | `test_mcp_a2a_sandbox.py` | **Mock/契约桩**：本地 JSON-RPC MCP（initialize/tools/list/tools/call）+ Bearer 入站 + 四层验收 + 无 key 401；远端 MCP_ENDPOINT=边界标注 |
| 8 | agentkit-a2a-registry | `harness/c08_a2a.py` | `test_mcp_a2a_sandbox.py` | **Mock/契约桩**：AgentCard schema（protocolVersion 0.3.0 / JSONRPC）、JSON-RPC message/send、`_GatewayPathRewrite`；注册到 A2A 空间=边界标注 |
| 9 | agentkit-sandbox | `harness/c09_sandbox.py` | `test_mcp_a2a_sandbox.py` | **完整（本地真跑）**：子进程真执行代码 + 同 session FS 复用 / 跨 session 隔离；真云沙箱 AGENTKIT_TOOL_ID=边界标注 |
| 10 | agentkit-guardrails | `harness/c10_guardrails.py` | `test_security.py`、`test_integration.py` | **Mock/契约桩 + 边界**：4 回调契约 + 规则桩拦截注入 + 实测拦截文案；`content_safety` 真导入需 `TOOL_LLM_SHIELD_APP_ID`=边界标注（已验证缺即 ValueError） |
| 11 | agentkit-identity-permission | `harness/c11_identity.py` | `test_security.py`、`test_integration.py` | **Mock/契约桩**：入站 Bearer/JWT 验签、Cedar Allow/Deny、4 层验收矩阵（401/401/200/403）；真 UserPool/SSO/JWKS=边界标注 |
| 12 | agentkit-knowledge-base | `harness/c12_knowledge.py` | `test_memory_kb_obs_eval.py` | **真实构造 + 本地词法桩检索**：真实 `KnowledgeBase(backend="local")` 可构造（`InMemoryKnowledgeBackend`）；检索路径为自写词法打分器（真实对象仅 `search` 方法，未在测试中调用 SDK 检索）；VikingDB=边界标注 |
| 13 | agentkit-observability | `harness/c13_observability.py` | `test_memory_kb_obs_eval.py`、`test_integration.py` | **Mock/契约桩**：内存 span recorder（gen_ai.* 属性）+ 单次 trace duration=span 差、P50/P95 聚合分离；APMPlus OpenAPI 查询=边界标注 |
| 14 | agentkit-evaluation | `harness/c14_evaluation.py` | `test_memory_kb_obs_eval.py` | **Mock/契约桩**：Dataset/ExactMatch/LLM-judge-stub/Experiment 本地跑分；在线评测平台=边界标注 |

## 总装

- 集成链路：`harness/app.py::MinimalHarness.handle()` 把 14 个组件串成单请求流水线：
  identity(auth) → guardrails(input) → knowledge-base → veadk/sdk agent run → session-memory → guardrails(output) → observability。
- 云端边界清单：`MinimalHarness.cloud_boundary_report()`。

## 测试结果

- 命令：`benchmark_20260928/.venv/bin/python -m pytest tests/ -p no:cacheprovider`
- 结果：**40 passed, 0 failed**（完整输出见 `journal/pytest_output.txt`；基准验收后新增 `test_skills.py` 6 个行为测试，原 34 → 40）。
- 需要云端凭据的用例数量：0（全部以桩/契约/边界形式覆盖，无真实云调用）。
