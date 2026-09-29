"""Component: **veadk** (Volcengine Agent Development Kit).

Per the `veadk` Skill:
  * ``veadk.Agent`` extends Google ADK ``LlmAgent``.
  * ``Runner(agent, app_name)`` manages session/event flow.
  * ``await runner.run(messages=, user_id=, session_id=) -> str`` builds the session
    itself and returns the final text.

Real ``runner.run`` needs a live ARK (doubao) model + AK/SK. We therefore:
  1. Construct a **real** ``veadk.Agent`` (proves the pinned import graph builds).
  2. Wrap it in a ``ScriptedRunner`` exposing the *same* ``run(messages=,
     user_id=, session_id=) -> str`` contract locally, recording every call.
A real model invocation is a documented ``CloudBoundary``.
"""
from __future__ import annotations

from typing import Any, Optional

try:  # pragma: no cover - import guard for environments without the pinned sdk
    from veadk import Agent as VeAgent
    from veadk import Runner as VeRunner
    _VEADK_AVAILABLE = True
except Exception:  # pragma: no cover
    VeAgent = None  # type: ignore
    VeRunner = None  # type: ignore
    _VEADK_AVAILABLE = False


def build_real_agent(instruction: str = "You are a helpful assistant.",
                     tools: Optional[list] = None,
                     name: str = "harness_agent"):
    """Construct a real veadk.Agent (LlmAgent subclass). No model call yet."""
    if not _VEADK_AVAILABLE:
        raise RuntimeError("veadk-python is not installed in this environment")
    return VeAgent(name=name, instruction=instruction, tools=tools or [])


class ScriptedRunner:
    """Local stand-in for ``veadk.Runner`` with the same ``run`` contract.

    It records (messages, user_id, session_id) and returns deterministic text, so
    the Harness integration path can be exercised *without* an ARK model. The real
    ``Runner.run`` would call the LLM; that edge is a ``CloudBoundary``.
    """

    def __init__(self, agent: Any = None, app_name: str = "harness_app",
                 reply: Optional[str] = None):
        self.agent = agent
        self.app_name = app_name
        self._reply = reply or "Hello from scripted veadk runner."
        self.calls: list[dict] = []

    async def run(self, messages: Any, user_id: str = "",
                  session_id: str = "tmp-session", run_config: Any = None) -> str:
        # mirrors veadk/runner.py signature: messages, user_id, session_id, -> str
        self.calls.append({"messages": messages, "user_id": user_id,
                           "session_id": session_id})
        return self._reply


def veadk_status() -> dict:
    return {
        "veadk_importable": _VEADK_AVAILABLE,
        "note": "Real runner.run requires ARK model + VOLCENGINE AK/SK (CloudBoundary).",
    }
