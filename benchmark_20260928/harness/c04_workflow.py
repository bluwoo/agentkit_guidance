"""Component: **adk-workflow** (Google ADK 2.x orchestration).

Per the `adk-workflow` Skill:
  * Primitives come from ``google.adk`` / ``google.adk.workflow`` (NEVER ``veadk.workflow``).
  * Graph Workflow = default for fixed topology; branching via ``Event(route=...)`` + edge dict
    + ``DEFAULT_ROUTE``; parallel fan-out via ``JoinNode``; dynamic via ``@node(rerun_on_resume=True)``
    + ``ctx.run_node()``.
  * Template Sequential/Parallel/Loop still run but raise DeprecationWarning (legacy only).

All workflows below use FunctionNode / pure-function nodes — **no LLM, no cloud** — and are
executed for real on the pinned ``google-adk==2.2.0`` via an InMemorySessionService Runner.
"""
from __future__ import annotations

from typing import Any

from google.adk import Workflow, Event, Context
from google.adk.workflow import node, JoinNode, DEFAULT_ROUTE


# --- Routing graph ------------------------------------------------------
@node(name="classify")
def classify(node_input: str):
    text = node_input.lower()
    if "bug" in text:
        return Event(route="BUG", output=node_input)
    if "help" in text:
        return Event(route="SUPPORT", output=node_input)
    return Event(route="OTHER", output=node_input)


@node(name="handle_bug")
def handle_bug(node_input: str):
    return f"[BUG HANDLER] processing: {node_input}"


@node(name="handle_support")
def handle_support(node_input: str):
    return f"[SUPPORT HANDLER] processing: {node_input}"


@node(name="handle_other")
def handle_other(node_input: str):
    return f"[OTHER HANDLER] processing: {node_input}"


routing_graph = Workflow(
    name="routing_graph",
    edges=[
        ("START", classify),
        (classify, {"BUG": handle_bug, "SUPPORT": handle_support,
                    DEFAULT_ROUTE: handle_other}),
    ],
)


# --- Parallel fan-out + Join -------------------------------------------
@node(name="upper")
def upper(node_input: str):
    return f"A:{node_input.upper()}"


@node(name="length")
def length(node_input: str):
    return f"B:{len(node_input)}"


join = JoinNode(name="join")


@node(name="merge")
def merge(node_input: dict):
    parts = [f"{k}={v}" for k, v in sorted(node_input.items())]
    return "MERGED[" + ", ".join(parts) + "]"


fanout_graph = Workflow(
    name="fanout_graph",
    max_concurrency=2,
    edges=[
        ("START", upper, join),
        ("START", length, join),
        (join, merge),
    ],
)


# --- Dynamic workflow ----------------------------------------------------
@node(name="greet")
def greet(node_input: str):
    return f"Hello {node_input}"


@node(name="format")
def format_node(node_input: str):
    return f"[FORMATTED] {node_input} [/FORMATTED]"


@node(rerun_on_resume=True)
async def dynamic_orchestrate(ctx: Context, node_input: str):
    g = await ctx.run_node(greet, node_input=node_input)
    return await ctx.run_node(format_node, node_input=g)


dynamic_graph = Workflow(name="dynamic_graph", edges=[("START", dynamic_orchestrate)])


# --- Runner harness (model-free) ---------------------------------------
async def run_workflow(workflow: Workflow, user_text: str) -> str:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    app_name, user_id = "harness_wf", "harness_user"
    svc = InMemorySessionService()
    session = await svc.create_session(
        app_name=app_name, user_id=user_id, state={"input_text": user_text})
    runner = Runner(app_name=app_name, agent=workflow, session_service=svc)
    content = types.Content(role="user", parts=[types.Part(text=user_text)])

    final_text, final_output = "", None
    async for ev in runner.run_async(user_id=user_id, session_id=session.id,
                                    new_message=content):
        if ev.content and ev.content.parts:
            for part in ev.content.parts:
                if part.text:
                    final_text = part.text
        if getattr(ev, "output", None) is not None:
            final_output = ev.output
    return final_text if final_text else str(final_output)
