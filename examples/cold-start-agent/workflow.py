"""Google ADK Graph：分类 -> 两个显式分支 + DEFAULT_ROUTE 兜底。

编排原语一律从 ``google.adk`` / ``google.adk.workflow`` 导入（不写 veadk.workflow）。
全部为无模型 FunctionNode，离线可真实运行。

关键（审计 D1 修复）：Graph 不再自建 InMemory Runner，而是复用调用方传入的
**持久化 ``session_service``（即 veADK ShortTermMemory 背后的 DatabaseSessionService）**，
使节点对 ``session.state`` 的读写真正落到 sqlite，跨请求/重建实例可召回。

绑定约定（钉版 google-adk 2.2.0）：
- 根单参节点入参命名为 ``node_input``；
- 类型标注为 ``Context`` 的参数由引擎自动注入，用于读写 ``session.state``。
"""

from __future__ import annotations

from google.adk import Context, Event, Workflow
from google.adk.runners import Runner
from google.adk.workflow import DEFAULT_ROUTE, node
from google.genai import types

APP_NAME = "cold_start_demo"


@node(name="classify")
def classify(node_input: str) -> Event:
    """按关键词路由：含 bug->BUG，含 help->SUPPORT，否则走 DEFAULT_ROUTE。"""
    t = (node_input or "").lower()
    if "bug" in t:
        return Event(route="BUG", output=node_input)
    if "help" in t:
        return Event(route="SUPPORT", output=node_input)
    return Event(route="OTHER", output=node_input)


def _bump(state, branch: str, text: str) -> None:
    """在持久化 session.state 上累计轮次与历史（Runner 结束后落库）。

    注意：钉版 2.2.0 必须写 ``context.state``（State 对象），写
    ``context.session.state`` 不会被回写/落库（已实测）。
    """
    state["turn_count"] = state.get("turn_count", 0) + 1
    state["last_branch"] = branch
    history = list(state.get("history", []))
    history.append({"branch": branch, "text": text})
    state["history"] = history  # 赋值而非 in-place append，State 才会追踪落库


@node(name="handle_bug")
def handle_bug(node_input: str, context: Context) -> str:
    _bump(context.state, "BUG", node_input)
    return f"[BUG] 已登记缺陷单: {node_input}"


@node(name="handle_support")
def handle_support(node_input: str, context: Context) -> str:
    _bump(context.state, "SUPPORT", node_input)
    return f"[SUPPORT] 已转人工支持: {node_input}"


@node(name="handle_other")
def handle_other(node_input: str, context: Context) -> str:
    _bump(context.state, "OTHER", node_input)
    return f"[OTHER] 已归档通用队列: {node_input}"


# 条件路由表：显式 DEFAULT_ROUTE 作为未命中兜底。
routing_workflow = Workflow(
    name="routing_workflow",
    edges=[
        ("START", classify),
        (
            classify,
            {
                "BUG": handle_bug,
                "SUPPORT": handle_support,
                DEFAULT_ROUTE: handle_other,
            },
        ),
    ],
)


async def run_routing(text: str, *, user_id: str, session_id: str, session_service) -> str:
    """用**复用的持久化 session_service** 真实执行 Graph，返回分支文本与当前轮次。

    不再自建 InMemorySessionService：会话状态直接读写在调用方传入的
    DatabaseSessionService 上，从而贯穿 HTTP 请求并落 sqlite。
    """
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    # 把本轮输入放进 state，供根节点 node_input 绑定。
    session.state["node_input"] = text

    runner = Runner(
        app_name=APP_NAME,
        agent=routing_workflow,
        session_service=session_service,
    )
    content = types.Content(role="user", parts=[types.Part(text=text)])
    final = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final = part.text
        if getattr(event, "output", None) is not None:
            final = str(event.output)

    turn = session.state.get("turn_count", 0)
    # Runner 内部持久化的是它自己取到的 session 对象；预取的 session 不更新，
    # 故轮次要在 run 结束后重新 get_session 读取（已实测）。
    after = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if after is not None:
        turn = after.state.get("turn_count", turn)
    return f"{final} | turn={turn}"
