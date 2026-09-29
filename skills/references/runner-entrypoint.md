# 共享权威参考：VeADK Runner 入口（非流式 / SSE 流式 / 签名验证）

> 本文件是 AgentKit 14 个组件 Skill **共用的 Runner 入口样板的唯一权威来源**。
> 各组件 Skill 的「代码集成」只保留**自身特有的工具/能力装配**，遇到下面这些通用片段时直接跳转本文件，不要复制粘贴。
>
> - 钉版：`veadk-python==1.1.13`、`agentkit-sdk-python==0.8.7`、`google-adk==2.2.0`（与离线验证 results.json 84/84 通过一致，2026-09-18）。
> - 签名实测：2026-09-28 在 `benchmark_20260928/.venv`（Python 3.12）用 `inspect.signature` 复核通过，见下方 §3。
> - 来源：`veadk/runner.py`、`veadk/apps.py`（AgentkitSimpleApp）；离线核验报告 `docs/offline-verification-report.md` / `docs/verification/results.json`。

---

## 1. 何时读本文件

只要在写一个被 `AgentkitSimpleApp` 包装、用 `Runner` 托管的 Agent 入口，就用这里的骨架。各组件 Skill 在「代码集成」一节通常长这样：

```python
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()
agent = Agent(name="...", instruction="...", tools=[<本组件特有工具>])  # ← 各组件唯一不同的地方
runner = Runner(agent=agent, app_name="...")

@app.entrypoint
async def run(payload, headers):
    result = await runner.run(messages=payload["prompt"],
                              user_id=headers["user_id"],
                              session_id=headers["session_id"])
    return result

app.run(host="0.0.0.0", port=8000)
```

各 Skill **只写 `agent = Agent(...)` 里自己的特有装配**（MCPToolset / run_code / LongTermMemory / content_safety 回调 / …），其余通用结构一律引用本文件。

---

## 2. 非流式（推荐，最简单）

`runner.run(messages=)` 是 VeADK 对 ADK Runner 的封装：**自动建 session、自动把 str 转成 `types.Content`、返回最终文本 `str`**。这是 90% 场景应选的写法。

```python
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()
agent = Agent(name="my_agent", instruction="你是一个助手")
runner = Runner(agent=agent, app_name="my_app")

@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],          # str | list[str] | MediaMessage
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result                            # 返回 str

app.run(host="0.0.0.0", port=8000)
```

**为什么用它**：它内部已经 `short_term_memory.create_session()`，不会抛 `SessionNotFoundError`。

---

## 3. 权威签名（inspect 实测 2026-09-28）

```
Runner.run(self,
    messages: str | list[str] | MediaMessage | list[MediaMessage | str],   # 必填
    user_id: str = '',
    session_id: str = 'tmp-session-<时间戳>',     # 缺省自动生成；内部 create_session
    run_config: RunConfig | None = None,
    save_tracing_data: bool = False,
    upload_inline_data_to_tos: bool = False,
    run_processor: BaseRunProcessor | None = None,
) -> str

Runner.run_async(self, *,
    user_id: str, session_id: str,                 # 关键字必传
    invocation_id: str | None = None,
    new_message: types.Content | None = None,      # 必须是 types.Content，不能传裸 str
    state_delta: dict | None = None,
    run_config: RunConfig | None = None,
    yield_user_message: bool = False,
) -> AsyncGenerator[Event, None]
```

复跑验证（等价于过去散落在 ~11 个 Skill 里的 `python3 -c "...inspect.signature(Runner.run)"`）：

```bash
# 用 benchmark_20260928/.venv（已装钉版依赖）；或任意装了 veadk-python==1.1.13 的环境
python3 skills/references/verify_runner_signature.py
```

脚本会断言：`Runner.run` 含 `messages/user_id/session_id`、`Runner.run_async` 是关键字-only 且 `new_message` 注解为 `types.Content`，并打印实测签名。退出码非 0 即说明钉版漂移，需重新核对。

---

## 4. 流式 SSE（逐事件推送，才需要 run_async）

只有需要逐事件 yield 时才用 `run_async`。它**继承 Google ADK 父类**，有两个非平凡契约：

1. `new_message` 必须是 `types.Content`（不能传裸字符串）。
2. `auto_create_session` **未被 veadk 覆盖，默认 False**——session 不存在会 `raise SessionNotFoundError`。**必须先显式 `create_session`**，否则别用流式、回到 §2 的 `runner.run(messages=)`。

```python
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp
from google.genai import types
from google.adk.agents import RunConfig
from google.adk.agents.run_config import StreamingMode

app = AgentkitSimpleApp()
agent = Agent(name="my_agent", instruction="你是一个助手")
runner = Runner(agent=agent, app_name="my_app")

# 流式入口（先预建 session，再手动构造 Content）
@app.entrypoint
async def run_stream(payload, headers):
    await runner.short_term_memory.create_session(   # ← session 预建，不可省
        app_name=runner.app_name,
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    content = types.Content(
        role="user",
        parts=[types.Part(text=payload["prompt"])],
    )
    async for event in runner.run_async(
        user_id=headers["user_id"],
        session_id=headers["session_id"],
        new_message=content,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        yield event.model_dump_json(exclude_none=True, by_alias=True)

app.run(host="0.0.0.0", port=8000)
```

> 部署侧：Runtime 调用走 SSE 时，SDK 侧即 `RunConfig(streaming_mode=StreamingMode.SSE)`。详见 `agentkit-runtime` / `agentkit-sdk`。

---

## 5. 四条跨组件硬契约（各 Skill 必须遵守，细节归各 Skill）

下面四条不是“Runner 样板”，是各组件**独有但跨套件一致**的约束。它们的权威定义在本文件，但**深度示例留在归属 Skill**，不要在入口骨架里展开。

| 契约 | 硬规则 | 深度示例 / 归哪个 Skill |
|---|---|---|
| **鉴权 400** | 入口拿到的 `user_id`/`session_id` 是会话路由标识，**不是授权依据**。缺这两个 header 时应返回 `400`，**不回落 `"default"`、不生成随机标识**（否则不同用户聚合到同一会话造成数据泄漏）。 | `agentkit-sdk` §3.2（`JSONResponse(status_code=400, ...)` 完整实现）、`agentkit-identity-permission`（401/403 验收矩阵） |
| **session 预建** | 用 `run_async` 前必须 `await runner.short_term_memory.create_session(...)`；`runner.run(messages=)` 则内部自动建。 | 本文件 §4；`agentkit-sdk` §3.2 注释流 |
| **记忆落库** | 长期记忆不会自动落库，需在每轮结束显式 `await runner.save_session_to_long_term_memory(session_id=..., user_id=...)`（协程），或配 `MemoryAutoSavePolicy`。 | `agentkit-session-memory` §3.2 / §4.6；`veadk` §5/§7 |
| **短期会话持久化** | `auto_save_session=True` **只控制保存时机、不指定 backend**。要跨请求持久化必须显式 `ShortTermMemory(db_url=...)` 并传给 `Runner(short_term_memory=...)`；SQLite 用 `sqlite+aiosqlite:////绝对路径`（4 斜杠）。 | `agentkit-sdk` §3.2 / §10（含 `isinstance(..., DatabaseSessionService)` 断言） |

> **Workflow 版本差异**（Google ADK 2.2.0 vs 官网 2.10.0）不属于本 Runner 入口，归 `adk-workflow`（`max_parallel_workers` 仅 2.10.0 有；本钉版用 `Workflow(max_concurrency=N)`）。

---

## 6. 入口装饰器速查（AgentkitSimpleApp）

| 装饰器 / 调用 | 作用 |
|---|---|
| `app = AgentkitSimpleApp()` | 应用容器，薄包装，不改 VeADK 行为 |
| `@app.entrypoint` | 定义入口函数 `(payload, headers)`；可 `return str` 或 `async yield` SSE 事件 |
| `@app.ping` | 健康检查，返回 `"pong!"` |
| `app.run(host="0.0.0.0", port=8000)` | 启动本地服务（容器须监听 8000） |

请求契约（全套件一致）：Header `user_id` / `session_id`；Body `prompt`（+ 可选 `files` 多模态）。健康检查路径 `/ping`。
