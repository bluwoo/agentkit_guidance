# [PRODUCT] 14 组件 Skill 独立核验报告（v2 修正版）

- 核验日期：2026-09-18（v2 修正：基于 [BASE-ADK] 原始源码重验 Runner API）
- 核验范围：`skills/` 下 14 个 [PRODUCT] 组件 Skill
- 事实基准（权威优先级从高到低）：
  1. **[BASE-ADK] 原始源码**（github.com/volcengine/[BASE-ADK]-python，commit main）— 最高权威
     - `[BASE-ADK]/runner.py` — Runner.run / run_async 签名与行为
     - `[BASE-ADK]/agent.py` — Agent 类继承关系
     - `[BASE-ADK]/integrations/[PRODUCT]/app.py` — create_[PRODUCT]_app 工厂函数
     - `[BASE-ADK]/memory/long_term_memory.py` — 长期记忆后端工厂
  2. **Google ADK 官方源码/文档** — 父类行为（run_async / types.Content）
  3. **火山引擎官方文档**（<INTERNAL_HOST>.com）— 平台侧 API 与控制台操作
  4. **shard 摘要文档** — 仅作辅助参考，与源码不一致时以源码为准
- 云凭据状态：**本阶段未执行云联调，火山引擎凭据可用性尚未核验**。所有"可运行"代码/CLI/curl 示例仅做静态核验与源码签名核验。

---

## 0. 全局结论（v2 修正）

**v1 核验报告存在严重事实错误**：将 [BASE-ADK] Runner 的 `run(messages=...)` 方法误判为"编造API"，强制将10个Skill改为 `run_async(new_message=...)`。经直接读取 [BASE-ADK] 原始源码（`[BASE-ADK]/runner.py`）确认：

- **[BASE-ADK] Runner 确实有 `async def run(messages: RunnerMessage, ...) -> str` 方法**，这是真实存在的公开 API
- 上一轮"修正"引入了更严重的错误：`run_async(new_message=纯字符串)` 是错的——ADK 父类的 `run_async` 要求 `new_message` 必须是 `types.Content` 类型
- v2 已回滚全部10个Skill的错误修改，恢复为正确的 [BASE-ADK] `run()` 用法，并补充流式场景的 `run_async` 正确写法

示例状态统一四档标注约定：
- 【源码核验-签名匹配】：已通过 `inspect.signature` 或直接阅读 [BASE-ADK] 源码确认方法签名与参数类型完全匹配。
- 【源码核验-需ADK Content构造】：需使用 ADK 父类 `run_async`，`new_message` 必须构造为 `types.Content`，且需预建 session。
- 【需云凭据联调】：依赖真实云端 Runtime / MCP 服务 / 内部 CLI 凭据，本阶段未执行联调。
- 【待核验】：import 路径或构造参数未在源码中直接确认，需安装后实测。

---

## 1. 核心修正：[BASE-ADK] Runner vs Google ADK Runner 完整对比

### 1.1 方法签名对比（基于 [BASE-ADK]/runner.py 原始源码）

| 维度 | [BASE-ADK] `runner.run()` | ADK 父类 `runner.run_async()` |
|---|---|---|
| **定义位置** | `[BASE-ADK]/runner.py`，[BASE-ADK] Runner 类自身方法 | `google.adk.runners.Runner`，ADK 父类 |
| **方法签名** | `async def run(self, messages: RunnerMessage, user_id: str = "", session_id: str = "", run_config: RunConfig | None = None, ...) -> str` | `async def run_async(self, *, user_id: str, session_id: str, new_message: types.Content, run_config: RunConfig | None = None)` → AsyncGenerator[Event] |
| **消息类型** | `RunnerMessage` = `str | list[str] | MediaMessage | list[MediaMessage] | list[MediaMessage|str]` | 必须是 `google.genai.types.Content` 对象 |
| **Session 管理** | 自动通过 `short_term_memory.create_session()` 创建 | 需预先创建 session |
| **消息转换** | 内部自动 `_convert_messages()` 转 ADK Content | 调用方需自行构造 |
| **返回值** | `str`（最终文本输出，自动聚合，提取最后一个非thought文本） | `AsyncGenerator[Event]`（事件流） |
| **流式支持** | 不支持（内部聚合为单字符串） | 支持 SSE 流式输出 |
| **适用场景** | 简单调用、测试、脚本、非流式 entrypoint | 流式输出、Studio 集成、需要逐事件处理 |
| **内部实现** | 自动建session → 转Content → 遍历 `self.run_async(...)` → 提取文本 → 返回 str | 直接遍历执行 Agent 事件流 |

### 1.2 正确使用方式

**简单调用（推荐，绝大多数场景）**：
```python
from [BASE-ADK] import Agent, Runner

runner = Runner(agent=agent, app_name="my_app")
result = await runner.run(
    messages="你好，请介绍一下你自己",
    user_id="user-001",
    session_id="session-001",
)
print(result)  # str 类型的最终回答
```

**流式 SSE 输出（需要逐事件推送时）**：
```python
from [BASE-ADK] import Agent, Runner
from google.genai import types
from google.adk.agents import RunConfig
from google.adk.agents.run_config import StreamingMode

runner = Runner(agent=agent, app_name="my_app")

# new_message 必须是 types.Content，不是纯字符串！
content = types.Content(
    role="user",
    parts=[types.Part(text="你好，请介绍一下你自己")]
)

async for event in runner.run_async(
    user_id="user-001",
    session_id="session-001",
    new_message=content,
    run_config=RunConfig(streaming_mode=StreamingMode.SSE),
):
    yield event.model_dump_json(exclude_none=True, by_alias=True)
```

### 1.3 可重验验证命令

```bash
# 验证 [BASE-ADK] Runner.run 方法存在且签名正确
python3 -c "from [BASE-ADK].runner import Runner; import inspect; print(inspect.signature(Runner.run))"
# 预期输出包含：(self, messages: RunnerMessage, user_id: str = '', session_id: str = ..., ...) -> str

# 验证 [BASE-ADK] Runner 继承自 ADK Runner
python3 -c "from [BASE-ADK].runner import Runner; print(Runner.__mro__[:3])"
# 预期输出：(<class '[BASE-ADK].runner.Runner'>, <class 'google.adk.runners.Runner'>, ...)

# 验证 run_async 来自父类
python3 -c "from [BASE-ADK].runner import Runner; import inspect; print(inspect.signature(Runner.run_async))"
# 预期输出包含：(*, user_id: str, session_id: str, new_message: google.genai.types.Content, ...)
```

---

## 2. 全局问题清单（v2 修正后）

### 2.1 【已修正·v1严重错误】runner.run(messages=...) 不是编造API

- **v1错误结论**：声称 `runner.run(messages=...)` 是编造API，真实调用只有 `run_async(new_message=...)`
- **源码事实**（[BASE-ADK]/runner.py）：
  ```python
  class Runner(ADKRunner):
      async def run(
          self,
          messages: RunnerMessage,
          user_id: str = "",
          session_id: str = f"tmp-session-{formatted_timestamp()}",
          run_config: RunConfig | None = None,
          save_tracing_data: bool = False,
          upload_inline_data_to_tos: bool = False,
          run_processor: "BaseRunProcessor | None" = None,
      ) -> str:
  ```
  源码中 `save_tracing_file()`、`save_eval_set()`、`save_session_to_long_term_memory()` 的示例全部用 `asyncio.run(runner.run(messages="Hi!", session_id=session_id))`。
- **v2修正**：全部10个Skill已回滚为 `runner.run(messages=...)` 写法，标注【源码核验-签名匹配】。流式场景补充 `run_async` + `types.Content` 的正确写法。

### 2.2 【已确认·正确保留】RemoteA2aAgent 导入路径

- v1修正正确：`RemoteA2aAgent` 来自 `google.adk.agents.remote_a2a_agent`（子模块），不是 [BASE-ADK] 自身。
- [BASE-ADK] 的多 Agent 编排类（SequentialAgent/ParallelAgent/LoopAgent）也来自 Google ADK（`google.adk.agents`），[BASE-ADK] Agent 继承 LlmAgent 因此兼容。

### 2.3 【已确认·正确保留】域名澄清

- 控制面 OpenAPI：`[PRODUCT].cn-beijing.volcengineapi.com`
- 工具执行 Endpoint：`<INTERNAL_HOST>.com`（InvokeTool/AsyncExecCommand/ViewAsyncCommand）
- 已部署 Runtime 调用域名：由 `GetRuntime.Endpoint` 返回
- 以上澄清正确，予以保留。

### 2.4 【已确认·正确保留】观测字段标注

- 日志字段 10 个（apmplus-server / apmplus-server-log）已列全。
- 埋点（Trace/Span）字段详情未获取，不可当开发契约。
- 以上标注正确，予以保留。

### 2.5 【已确认·正确保留】ADK workflow 子页面 dead link

- adk.dev/workflows/ 子页面多次尝试 link dead，编排组件以 [BASE-ADK] 真实 import 为准。
- 以上警告正确，予以保留。

---

## 3. 逐 Skill 核验结果表（v2 修正后）

| # | Skill | 结论 | Runner 用法状态 | 其他问题 |
|---|---|---|---|---|
| 1 | [PRODUCT]-runtime | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释中给出 `run_async + types.Content` 正确写法 | 域名澄清保留；CLI/curl 标【需云凭据联调】 |
| 2 | [PRODUCT]-sdk | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)` 为默认示例；流式示例注释中给出正确 `run_async` 写法；API 表格补充两种方法对比 | 域名澄清保留；CLI 标【需云凭据联调】 |
| 3 | [BASE-ADK] | 已补充 | 已补充 `run()` 方法说明与验证命令；补充 `run_async` 需 `types.Content` 说明 | create_[PRODUCT]_app 9 参数表正确；run_code import 标待实测 |
| 4 | adk-workflow | 通过（保留v1修正） | 无 Runner 调用代码示例（专注编排模式） | RemoteA2aAgent 子模块导入正确；子页面 dead 警告保留 |
| 5 | [PRODUCT]-sandbox | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | ToolType 枚举说明保留；CLI 标【需云凭据联调】 |
| 6 | [PRODUCT]-knowledge-base | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | KnowledgeBase import 标【待核验】 |
| 7 | [PRODUCT]-a2a-registry | 通过（标注保留） | 无 Runner 调用代码示例（CLI 为主） | registry-endpoint 存疑警告保留；CLI 标【需云凭据联调】 |
| 8 | [PRODUCT]-skills | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | 三种挂载 CLI 标【需云凭据联调】 |
| 9 | [PRODUCT]-gateway-mcp | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | MCPToolset 类名标【待核验】；curl 标【需云凭据联调】 |
| 10 | [PRODUCT]-identity-permission | 通过（标注保留） | 无 Runner 调用代码示例（身份配置为主） | 内部私有模块警告保留；CLI 标【需云凭据联调】 |
| 11 | [PRODUCT]-guardrails | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | curl 标【需云凭据联调】 |
| 12 | [PRODUCT]-evaluation | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | curl 标【需云凭据联调】 |
| 13 | [PRODUCT]-observability | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确 | 10日志字段表 + 埋点未获取警告保留；curl 标【需云凭据联调】 |
| 14 | [PRODUCT]-session-memory | 已修正 | 【源码核验-签名匹配】已恢复 `runner.run(messages=...)`；流式示例注释正确；`save_session_to_long_term_memory` 签名已核验 | viking_mem 废弃说明保留；curl 标【需云凭据联调】 |

---

## 4. 关键事实复核表（v2 修正后）

| 检查项 | 基准值（源码/官方） | 结果 |
|---|---|---|
| API Version | `2025-10-30`（14 个 Skill frontmatter 均一致） | 通过 |
| Region | `cn-beijing` | 通过 |
| 控制面 Endpoint | `[PRODUCT].cn-beijing.volcengineapi.com` | 已澄清 |
| 工具执行 Endpoint | `<INTERNAL_HOST>.com` | 已澄清 |
| **[BASE-ADK] Runner.run 存在** | `async def run(messages: RunnerMessage, ...) -> str`（[BASE-ADK]/runner.py） | 【源码核验-签名匹配】 |
| **[BASE-ADK] Runner.run 返回值** | `str`（最终文本，非事件流） | 【源码核验-签名匹配】 |
| **[BASE-ADK] Runner.run session 行为** | 自动通过 `short_term_memory.create_session()` 创建 | 【源码核验-签名匹配】 |
| **ADK run_async 消息类型** | 必须是 `types.Content`，不是纯字符串 | 【源码核验-签名匹配】 |
| **ADK run_async session 要求** | 需预先创建 session | 【源码核验-签名匹配】 |
| [BASE-ADK] Agent 继承 | `google.adk.agents.LlmAgent` | 已核验（[BASE-ADK]/agent.py） |
| RemoteA2aAgent 导入 | `google.adk.agents.remote_a2a_agent` | 已核验 |
| create_[PRODUCT]_app 参数数 | 9 个（root_agent/display_names/app/agent_draft/enable_feishu/enable_studio_tools/enable_studio_routes/identity/harness_extension） | 已核验（integrations/[PRODUCT]/app.py） |
| 日志 10 字段 | attribute/file_line/file_name/hostname/log_level/message/resource/service/source/trace_id | 已列全 |

---

## 5. 修正记录（v2 就地修改汇总）

### 5.1 回滚 v1 错误修改（10个Skill）

| Skill | 修改内容 |
|---|---|
| [PRODUCT]-runtime | 3.2 代码示例：删除"Runner 无 run(messages=) 同步方法"错误注释；改为 `await runner.run(messages=payload["prompt"], ...)` 直接返回字符串；补充流式 SSE 注释示例（`run_async + types.Content`）；补充 `from google.genai import types` import |
| [PRODUCT]-sdk | 3.2 代码示例：默认改为 `runner.run(messages=...)` 非流式写法；流式示例注释化并修正为 `types.Content`；删除"Runner 无 run(messages=) 同步方法"错误注释；API 表格补充两种 Runner 方法对比；排障条目补充 `new_message` 类型说明 |
| [PRODUCT]-sandbox | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |
| [PRODUCT]-knowledge-base | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |
| [PRODUCT]-session-memory | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)` 并保留 `save_session_to_long_term_memory` 调用；补充流式注释示例 |
| [PRODUCT]-skills | 3.3 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |
| [PRODUCT]-gateway-mcp | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |
| [PRODUCT]-guardrails | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |
| [PRODUCT]-evaluation | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |
| [PRODUCT]-observability | 3.2 代码示例：删除"runner.run(messages=) 为编造"错误注释；改为 `runner.run(messages=...)`；补充流式注释示例与 types import |

### 5.2 补充修正（[BASE-ADK] Skill）

| 修改内容 |
|---|
| 5.1 输入部分：补充 Runner 两种调用方式对比（`run()` vs `run_async()`）及各自参数要求 |
| 8. 可执行验证：补充 `inspect.signature(Runner.run)` 验证命令及预期输出 |

---

## 6. 遗留与未闭环项（如实说明）

- **本阶段未执行云联调**：所有 curl / CLI / 端到端示例仅静态核验与源码签名核验，真实云端联调未执行，凭据可用性尚未核验。
- **观测埋点（Trace/Span）字段**：外部 APMPlus / [BASE-ADK] 文档站子页未获取，**不可当开发契约**；如需前端 trace 覆盖层数据契约，须先取得真实字段定义。
- **adk.dev/workflows 子页面**：link dead，动态编排参数表（max_iterations 等）仍为待核验。
- **identity-permission 的 Workload* API 与 `_openapi`/`sdk.mcp.client` 私有模块**：属内部版 SDK，未在官方 OpenAPI 分片出现。
- **a2a-registry 的 `--registry-endpoint` 取值**：来自内部 lark 文档，未在官方分片核验。
- **knowledge-base 的 `[BASE-ADK].knowledgebase.KnowledgeBase` import**：未在源码中直接确认，标【待核验】。
- **流式 `run_async` 中的 session 创建**：[BASE-ADK] `run()` 内部自动建 session，`run_async` 需调用方确保 session 存在（或通过 `short_term_memory.create_session()` 手动创建），具体 session 创建 helper 的 import 路径待实测。

---

## 措辞与契约修正记录（2026-09-18）

- 云凭据状态一行由「本阶段未执行云联调，凭据可用性尚未核验」对齐为「本阶段未执行云联调，火山引擎凭据可用性尚未核验」（D类措辞）。
- 本报告涉及的 14 个 Skill 中，[PRODUCT]-runtime / [PRODUCT]-a2a-registry / [PRODUCT]-sdk / [PRODUCT]-sandbox 四处代码注释「（无云凭据）」已同步改为「（本阶段未执行云联调，火山引擎凭据可用性尚未核验）」。
- 只改措辞，不改变核验结论；原有「【需云凭据联调】/待核验」标注保留。
