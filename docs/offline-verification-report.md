# 离线验证报告 — [PRODUCT] [DELIVERY] Skill 库

> 生成日期：2026-09-18（Asia/Shanghai）
> 验证方式：独立临时 venv 安装精确版本，执行真实 `import` / `inspect.signature` / `py_compile` / `ast` 解析
> 约束：未使用 grep 计数证明；所有签名均通过 `inspect.signature()` 实际执行获取；未触发 LLM / 云资源调用
> 测试脚本：`docs/verification/test_imports.py` / `test_signatures.py` / `test_code_blocks.py` / `test_session_semantics.py` / `run_all.sh`
> 结果文件：`docs/verification/results.json`（机器可读汇总）、`docs/verification/test_log.txt`（完整日志）

---

## 1. 测试环境

| 项目 | 值 |
|---|---|
| venv 路径 | `/tmp/[PRODUCT]_verify_venv` |
| Python 版本 | **3.13.7** |
| 安装方式 | `pip install [BASE-ADK]-python==1.1.13 [PRODUCT]-sdk-python==0.8.7` |
| [BASE-ADK]-python | **1.1.13** |
| [PRODUCT]-sdk-python | **0.8.7** |
| google-adk | **2.2.0**（[BASE-ADK] 依赖自动安装） |
| 一键运行 | `bash docs/verification/run_all.sh`（使用现有精确版本环境；可通过 `VERIFY_PYTHON` 指定。环境缺失或版本不符会失败，不自动修改全局环境） |

---

## 2. Import 测试结果（方法：import，25/25 全部 PASS）

对 14 个 Skill 中出现的全部第三方 import，在 venv 中逐条实际执行 `from xxx import yyy`。

| # | Import 语句 | 方法 | 结果 |
|---|---|---|---|
| 1 | `from [BASE-ADK] import Agent, Runner` | import | **PASS** |
| 2 | `from [BASE-ADK] import Agent` | import | **PASS** |
| 3 | `from [PRODUCT].apps import [PRODUCT]SimpleApp` | import | **PASS** |
| 4 | `from [PRODUCT].apps import [PRODUCT]AgentServerApp` | import | **PASS** |
| 5 | `from google.genai import types` | import | **PASS** |
| 6 | `from google.adk.agents import RunConfig` | import | **PASS** |
| 7 | `from google.adk.agents.run_config import StreamingMode` | import | **PASS** |
| 8 | `from google.adk.agents import SequentialAgent` | import | **PASS** |
| 9 | `from google.adk.agents import ParallelAgent` | import | **PASS** |
| 10 | `from google.adk.agents import LoopAgent` | import | **PASS** |
| 11 | `from google.adk import Agent` | import | **PASS** |
| 12 | `from google.adk import Workflow` | import | **PASS** |
| 13 | `from google.adk import Event` | import | **PASS** |
| 14 | `from google.adk.workflow import node` | import | **PASS** |
| 15 | `from google.adk.agents.remote_a2a_agent import RemoteA2aAgent` | import | **PASS** |
| 16 | `from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset` | import | **PASS** |
| 17 | `from google.adk.tools.mcp_tool.mcp_toolset import StreamableHTTPConnectionParams` | import | **PASS** |
| 18 | `from [BASE-ADK].knowledgebase import KnowledgeBase` | import | **PASS** |
| 19 | `from [BASE-ADK].tools.builtin_tools.run_code import run_code` | import | **PASS** |
| 20 | `from [BASE-ADK].memory.long_term_memory import LongTermMemory` | import | **PASS** |
| 21 | `from [BASE-ADK].integrations.[PRODUCT] import create_[PRODUCT]_app` | import | **PASS** |
| 22 | `from [BASE-ADK].integrations.[PRODUCT] import run_[PRODUCT]_app` | import | **PASS** |
| 23 | `from [PRODUCT].auth._openapi import OpenApiClient` | import | **PASS** |
| 24 | `from [PRODUCT].sdk.mcp.client import [PRODUCT]MCPClient` | import | **PASS** |
| 25 | `from google.adk import Context` | import | **PASS** |

**总计：25/25 PASS，0 FAIL。** （原报告中 `from google.adk.context import Context` 已修正为 `from google.adk import Context`，该模块在 google-adk 2.2.0 中从顶层 re-export。）

---

## 3. Session 语义结论（方法：inspect + ast，8/8 检查 PASS）

### 3.1 源码事实（基于 `/tmp/[PRODUCT]_verify_venv` 实际安装版本）

| 事实 | 源码位置 | 证据 |
|---|---|---|
| `Runner.__init__` 的 `auto_create_session` 默认值为 `False` | `google/adk/runners.py:203` | `inspect.signature(ADKRunner.__init__).parameters['auto_create_session'].default == False` |
| `_get_or_create_session` 仅在 `self.auto_create_session` 为 `True` 时调 `create_session`，否则 `raise SessionNotFoundError` | `google/adk/runners.py:874-881` | AST 解析：`if self.auto_create_session:` 分支内调 `create_session`，`else` 分支 `raise SessionNotFoundError` |
| [BASE-ADK] `Runner.__init__` 未向 `super().__init__` 传 `auto_create_session=True` | `[BASE-ADK]/runner.py:454-462` | AST 解析：`super().__init__(...)` 调用无 `auto_create_session` 关键字参数 |
| [BASE-ADK] `Runner.run()` 显式调用 `short_term_memory.create_session(...)` | `[BASE-ADK]/runner.py:526-529` | AST 解析：`run` 方法体内有 `self.short_term_memory.create_session(...)` 调用 |
| [BASE-ADK] `Runner` 未用 `def` 覆盖 `run_async`（仅在 `__init__` 中用 `MethodType` 包装父类方法） | `[BASE-ADK]/runner.py:464-466` | AST 解析：`class Runner` 方法清单无 `run_async` 定义 |

### 3.2 准确结论

- **`runner.run(messages=...)` 自动建 session**：是。但这不是通过 `auto_create_session=True` 机制，而是 [BASE-ADK] 覆盖版 `run()` 在内部显式调用 `self.short_term_memory.create_session(...)`，且 `session_id` 有默认值 `tmp-session-<时间戳>`。调用方可以不传 `session_id`。
- **`runner.run_async(user_id=..., session_id=..., new_message=...)` 需要预建 session**：是。`run_async` 继承 ADK 父类，`auto_create_session` 默认 `False`（[BASE-ADK] 未覆盖），若 session 不存在，`_get_or_create_session` 会 `raise SessionNotFoundError`。流式用法必须先 `await runner.short_term_memory.create_session(...)`，或改用非流式 `run()`。

> 修正说明：原报告第 87 行称"run_async 内部调用 _get_or_create_session 自动创建 session，无需手动建 session"是**过度推断**。`_get_or_create_session` 确实被调用，但它只在 `auto_create_session=True` 时创建，默认 `False`。本版结论基于源码默认值，不推断。

### 3.3 测试脚本

- `docs/verification/test_session_semantics.py`：用 `ast.parse(inspect.getsource(...))` 解析 `_get_or_create_session`、`run`、`__init__`，8 项断言全部 PASS。
- 未实际调用 LLM：仅做静态源码分析 + inspect 签名读取。

---

## 4. 签名比对（方法：inspect.signature，36/36 检查 PASS）

通过 `inspect.signature()` 实际执行获取，并对关键参数做**参数与默认值检查 + 默认值断言**（不只测方法名存在）。

### 4.1 [BASE-ADK].runner.Runner

| 方法 | 关键断言 | 结果 |
|---|---|---|
| `Runner.__init__` | `agent=None`, `short_term_memory=None`, `app_name=None`, `user_id='[BASE-ADK]_default_user'`, `upload_inline_data_to_tos=False` | **PASS** |
| `Runner.run` | `messages` 必填；`user_id=''`；`session_id='tmp-session-<时间戳>'`（动态）；`run_config=None`；`save_tracing_data=False` | **PASS** |
| `Runner.run_async`（继承自 ADKRunner，被 MethodType 包装） | `user_id`/`session_id` 必填且 KEYWORD_ONLY；`invocation_id=None`；`new_message=None`；`run_config=None`；`yield_user_message=False` | **PASS** |

### 4.2 google.adk.runners.Runner（父类）

| 断言 | 结果 |
|---|---|
| `session_service` 必填（无默认值） | **PASS** |
| `auto_create_session` 默认值 `False` | **PASS** |

### 4.3 [PRODUCT].apps

| 类/方法 | 关键断言 | 结果 |
|---|---|---|
| `[PRODUCT]SimpleApp.__init__` | 无必填参数（除 self） | **PASS** |
| `[PRODUCT]SimpleApp.entrypoint` / `run` / `ping` | 方法存在 | **PASS** |
| `[PRODUCT]AgentServerApp.__init__` | 可导入（见 import #4） | **PASS** |

### 4.4 [BASE-ADK].integrations.[PRODUCT]

| 函数 | 关键断言 | 结果 |
|---|---|---|
| `create_[PRODUCT]_app` | `root_agent=None`；`enable_feishu=False`；`enable_studio_tools=False`；`enable_studio_routes=False` | **PASS** |
| `run_[PRODUCT]_app` | `app` 必填（POSITIONAL_OR_KEYWORD）；`host=None`；`port=None` | **PASS** |

### 4.5 google.adk / google.genai

| 断言 | 结果 |
|---|---|
| `StreamingMode.NONE / SSE / BIDI` 枚举成员存在 | **PASS** |
| `Runner.run.session_id` 默认值以 `tmp-session-` 开头（时间戳） | **PASS** |

---

## 5. Python 代码块语法校验（方法：py_compile，15/15 PASS）

对 14 个 Skill 中所有 ` ```python ` 代码块提取后，用 `py_compile.compile()` 校验语法（只校验语法，不执行代码）。

| Skill | 块# | 方法 | 行数 | 结果 |
|---|---|---|---|---|
| adk-workflow | 0 | py_compile | 47 | **PASS** |
| adk-workflow | 1 | py_compile | 67 | **PASS** |
| [PRODUCT]-evaluation | 0 | py_compile | ~43 | **PASS** |
| [PRODUCT]-gateway-mcp | 0 | py_compile | ~54 | **PASS** |
| [PRODUCT]-guardrails | 0 | py_compile | ~42 | **PASS** |
| [PRODUCT]-identity-permission | 0 | py_compile | ~44 | **PASS** |
| [PRODUCT]-knowledge-base | 0 | py_compile | ~52 | **PASS** |
| [PRODUCT]-observability | 0 | py_compile | ~44 | **PASS** |
| [PRODUCT]-runtime | 0 | py_compile | ~50 | **PASS** |
| [PRODUCT]-sandbox | 0 | py_compile | ~53 | **PASS** |
| [PRODUCT]-sdk | 0 | py_compile | ~57 | **PASS** |
| [PRODUCT]-session-memory | 0 | py_compile | ~63 | **PASS** |
| [PRODUCT]-skills | 0 | py_compile | ~45 | **PASS** |
| [BASE-ADK] | 0 | py_compile | ~23 | **PASS** |
| [BASE-ADK] | 1 | py_compile | ~14 | **PASS** |

**总计：15/15 PASS，0 FAIL。**（原 `[PRODUCT]-identity-permission` 的 `await` 顶层问题已修复为 `async def` 包装。）

---

## 6. 流式（run_async / SSE）示例修正

14 个 Skill 中，9 个 Skill 的代码块包含注释掉的流式 SSE 示例。本次统一修正：

| 问题 | 修正 |
|---|---|
| `[PRODUCT]-runtime/SKILL.md` 原注释称"run_async 内部自动调 _get_or_create_session，无需手动建 session" | 改为准确描述：`auto_create_session=False` 默认，session 不存在会 `SessionNotFoundError`，必须先显式建 session |
| 全部 9 个 Skill 的流式示例缺 session 创建步骤 | 在 `content = types.Content(...)` 前补入 `await runner.short_term_memory.create_session(...)` 调用 |
| `[PRODUCT]-sdk/SKILL.md` 已有文字说明但代码缺 create_session | 补入 `create_session` 调用 |

修正后所有流式示例均显式预建 session，与 `run_async` 语义一致。非流式 `runner.run(messages=...)` 示例保持不变（其内部自动建 session）。

---

## 7. 覆盖率与未覆盖项（诚实声明）

| 验证层级 | 覆盖范围 | 方法 | 结果 |
|---|---|---|---|
| 真实 import | 25 个 import | `exec(stmt)` | 25/25 PASS |
| inspect.signature | 36 项参数/默认值断言 | `inspect.signature()` + 绑定检查 | 36/36 PASS |
| py_compile | 15 个 Python 代码块 | `py_compile.compile()` | 15/15 PASS |
| ast 源码分析 | `_get_or_create_session` / `run` / `__init__` session 逻辑 | `ast.parse(inspect.getsource())` | 8/8 PASS |
| **运行时调用** | — | 未实际调用 LLM / 模型 API / 启动 FastAPI server / 端到端 invoke | 未覆盖 |

**未覆盖项：**
- 未实际发起 `runner.run()` 调用（需要模型 endpoint 凭据，环境变量为 `MODEL_AGENT_API_KEY` 及相关模型配置，本次未配置）。
- `@app.entrypoint` 装饰器仅确认方法存在且签名匹配，未启动 server 验证 HTTP 路由注册。
- `KnowledgeBase` / `LongTermMemory` / `OpenApiClient` / `[PRODUCT]MCPClient` 仅 import PASS，未实例化（需要外部后端）。

---

## 8. 测试脚本与结果文件清单

| 文件 | 说明 |
|---|---|
| `docs/verification/test_imports.py` | 25 个 import 测试 |
| `docs/verification/test_signatures.py` | 关键函数签名 inspect + 参数与默认值检查断言 |
| `docs/verification/test_code_blocks.py` | 14 Skill 全部 python 代码块 py_compile |
| `docs/verification/test_session_semantics.py` | session 语义 ast 分析 |
| `docs/verification/run_all.sh` | 一键运行全部测试，输出 JSON |
| `docs/verification/results.json` | 机器可读汇总（overall 84 PASS / 0 FAIL） |
| `docs/verification/test_log.txt` | 完整运行日志 |

**一键运行**：
```bash
bash docs/verification/run_all.sh
```

---

## 9. 版本固定清单（14 个 Skill frontmatter 统一）

```
[BASE-ADK]-python==1.1.13; [PRODUCT]-sdk-python==0.8.7; google-adk==2.2.0; API 2025-10-30; [BASE-AGENT] v0.21.1(e83b1d51)
```
