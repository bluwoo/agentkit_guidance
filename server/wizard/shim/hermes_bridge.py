"""Bridge between the thin FastAPI shim and the Hermes agent loop.

The shim never imports Hermes at module import time: ``RealHermesBridge`` lazily
adds ``vendor/hermes-agent`` to ``sys.path`` and constructs
``run_agent.AIAgent`` on first use. Bridge selection is driven by
``WIZARD_MODE`` (see :mod:`server.wizard.config`):

  * ``local``    — use ``RealHermesBridge`` when LLM env is present; otherwise
                   warn and fall back to ``MockHermesBridge`` (offline dev).
  * ``mock``     — force ``MockHermesBridge`` (tests / demos).
  * ``production`` — require LLM credentials; raise immediately if any are
                   missing. Never silently falls back to the mock bridge.

The mock bridge routes Step1..Step4 keywords to canned, demonstrable guidance so
the whole service can boot and smoke-test offline.

Confirmed Hermes contract (read from vendor/hermes-agent @ fixed commit):
  * ``AIAgent(base_url=, api_key=, provider=, api_mode=, model=)``
  * ``from agent.conversation_loop import run_conversation``
  * ``run_conversation(agent, user_message, system_message=None,
      conversation_history=None, task_id=None, stream_callback=None) -> dict``
  * ``stream_callback(text_delta: str)`` fires per output token.
  * Result envelope: ``{"final_response": str, "completed": bool,
      "failed": bool, "interrupted": bool, "error": Optional[str], ...}``
"""
from __future__ import annotations

import logging
import sys
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from server.wizard.config import Settings, get_settings

logger = logging.getLogger(__name__)

OnDelta = Callable[[str], None] | None


class HermesBridge(Protocol):
    """The minimal surface the shim needs from an agent back-end."""

    name: str

    def new_session(self, session_id: str = "", user_id: str = "") -> str: ...

    def turn(
        self,
        session_id: str,
        user_id: str,
        message: str,
        on_delta: OnDelta = None,
    ) -> dict[str, Any]:
        """Run one turn; return ``{"reply": str, "trace_id": str|None, ...}``."""
        ...

    def close(self) -> None: ...


# --------------------------------------------------------------------------- #
# Mock bridge (default, offline / no credentials)
# --------------------------------------------------------------------------- #
# Deterministic demo script. Keyword routing lets a human drive the four-step
# flow with plain text while keeping the SSE path real.
_STEP_REPLIES = [
    ("step1", (
        "Step1 业务目标：请用一句话描述你要做的 Agent。\n"
        "我会按 grilling 的 design tree 逐题追问：目标用户、业务任务、典型输入、期望产出、非目标。"
    )),
    ("step2", (
        "Step2 验收标准：我们把目标翻译成「可独立验证的结果」。\n"
        "每条验收必须有判断方式：artifact / external_state / llm_judge / rule，且 baseline_locked=true。"
    )),
    ("step3", (
        "Step3 架构设计：基于目标与验收，推荐组件组合。\n"
        "我会从 14 个组件里挑真正需要的；没有信息时返回空数组，不编造。"
    )),
    ("step4", (
        "Step4 测试验证：触发测试调用后，从 APMPlus trace 取数。\n"
        "单次 trace 只用 span 数据；P50/P95/QPS 是独立聚合面板，绝不归属到一次调用。"
    )),
    ("grill", (
        "已开始 grilling：design tree frontier 第一轮。\n"
        "Q1 目标用户是谁？ ➡️ 推荐：明确角色与使用场景。\n"
        "Q2 Agent 替用户完成什么任务？ ➡️ 推荐：一句话动词短语。"
    )),
    ("adr", (
        "domain-modeling：本决策满足 ADR 三条件（难逆/需背景/真实权衡），建议记录。\n"
        "ADR-0001: 采用 Hermes 原生主循环 + 薄 shim 作为 Wizard 底座。"
    )),
    ("glossary", (
        "domain-modeling 术语表（CONTEXT.md 草稿）：\n"
        "**目标用户**: Agent 服务的最终使用者。_Avoid_: 客户, 账号。\n"
        "**验收用例**: 一条独立可验证的成功标准，baseline_locked。"
    )),
]


class MockHermesBridge:
    """Deterministic, credential-free bridge used for local dev + tests."""

    name = "mock-hermes"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._turns: dict[str, int] = {}

    def new_session(self, session_id: str = "", user_id: str = "") -> str:
        if session_id:
            return session_id
        # Generate a unique id so concurrent requests don't share state.
        return f"sess-mock-{uuid.uuid4().hex[:8]}"

    def turn(
        self,
        session_id: str,
        user_id: str,
        message: str,
        on_delta: OnDelta = None,
    ) -> dict[str, Any]:
        msg = (message or "").lower()
        reply = "你好，我是 AgentKit Wizard。说 step1/step2/step3/step4 或 grill/adr/glossary 开始。"
        for kw, text in _STEP_REPLIES:
            if kw in msg:
                reply = text
                break

        if on_delta is not None:
            # Stream the reply in a few chunks so SSE wiring is exercised.
            chunk = max(1, len(reply) // 4)
            for i in range(0, len(reply), chunk):
                on_delta(reply[i : i + chunk])

        with self._lock:
            self._turns[session_id] = self._turns.get(session_id, 0) + 1

        return {
            "reply": reply,
            "session_id": session_id,
            "trace_id": None,
            "mock": True,
        }

    def close(self) -> None:
        return None


# --------------------------------------------------------------------------- #
# Real bridge (lazy Hermes load)
# --------------------------------------------------------------------------- #
@dataclass
class RealHermesBridge:
    """Lazily constructs ``run_agent.AIAgent`` and drives ``run_conversation``."""

    settings: Settings
    name: str = "real-hermes"
    _agent: Any = field(default=None, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def _ensure_agent(self) -> Any:
        if self._agent is not None:
            return self._agent
        with self._lock:
            if self._agent is not None:
                return self._agent
            root = self.settings.hermes_vendor_root
            if root not in sys.path:
                sys.path.insert(0, root)
            # Imported lazily so a missing/broken vendor checkout only breaks
            # the Real bridge, never service startup.
            from agent.conversation_loop import run_conversation as _rc
            from run_agent import AIAgent  # type: ignore

            self._agent = AIAgent(
                base_url=self.settings.llm_base_url or None,
                api_key=self.settings.llm_api_key or None,
                provider=self.settings.llm_provider or None,
                api_mode=self.settings.llm_api_mode or None,
                model=self.settings.llm_model or "",
                quiet_mode=True,
            )
            self._run_conversation = _rc
            logger.info("RealHermesBridge initialized model=%s", self.settings.llm_model)
            return self._agent

    def new_session(self, session_id: str = "", user_id: str = "") -> str:
        agent = self._ensure_agent()
        sid = session_id or getattr(agent, "session_id", "") or "sess-real"
        try:
            agent.session_id = sid
        except Exception:  # pragma: no cover
            pass
        return sid

    def turn(
        self,
        session_id: str,
        user_id: str,
        message: str,
        on_delta: OnDelta = None,
    ) -> dict[str, Any]:
        agent = self._ensure_agent()
        try:
            agent.session_id = session_id or agent.session_id
        except Exception:  # pragma: no cover
            pass

        def _cb(delta: str | None) -> None:
            if on_delta is not None and delta:
                try:
                    on_delta(delta)
                except Exception:  # pragma: no cover
                    logger.debug("on_delta callback raised", exc_info=True)

        result = self._run_conversation(
            agent,
            message,
            conversation_history=None,
            task_id=session_id,
            stream_callback=_cb,
        )
        if not isinstance(result, dict):
            result = {"final_response": str(result)}

        reply = result.get("final_response", "") or ""
        failed = bool(result.get("failed"))
        interrupted = bool(result.get("interrupted"))
        err = result.get("error")

        return {
            "reply": reply,
            "session_id": session_id,
            "trace_id": None,
            "failed": failed,
            "interrupted": interrupted,
            "error": (None if not failed else (err or "agent run failed")),
        }

    def close(self) -> None:
        agent = self._agent
        if agent is not None:
            close = getattr(agent, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:  # pragma: no cover
                    logger.debug("agent close raised", exc_info=True)
        self._agent = None


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
_bridge: HermesBridge | None = None


def get_bridge(settings: Settings | None = None) -> HermesBridge:
    """Return the process-wide bridge, building it from env on first call.

    Behaviour depends on ``WIZARD_MODE``:
      * production — require real Hermes credentials; raise immediately if any
        are missing. Never silently fall back to the mock bridge.
      * local      — use RealHermesBridge when LLM env is present; otherwise warn
        and use MockHermesBridge (the historical dev/offline behaviour).
      * mock       — force MockHermesBridge regardless of LLM env (tests / demos).

    Tests inject a fake bridge via ``set_bridge`` rather than rebuilding this.
    """
    global _bridge
    if _bridge is not None:
        return _bridge
    settings = settings or get_settings()
    mode = settings.mode

    if mode == "production":
        if not settings.real_hermes_enabled or not settings.llm_api_key.strip():
            raise RuntimeError(
                "production mode requires WIZARD_LLM_BASE_URL, WIZARD_LLM_MODEL "
                "and WIZARD_LLM_API_KEY; refusing to fall back to MockHermesBridge"
            )
        _bridge = RealHermesBridge(settings=settings)
    elif mode == "mock":
        logger.info("WIZARD_MODE=mock -> forcing MockHermesBridge")
        _bridge = MockHermesBridge()
    else:  # local
        if settings.real_hermes_enabled:
            _bridge = RealHermesBridge(settings=settings)
        else:
            logger.warning(
                "WIZARD_LLM_BASE_URL/WIZARD_LLM_MODEL unset -> using MockHermesBridge "
                "(deterministic offline replies). Set the env vars to drive real Hermes."
            )
            _bridge = MockHermesBridge()
    return _bridge


def set_bridge(bridge: HermesBridge) -> None:
    """Inject a bridge (tests / custom wiring)."""
    global _bridge
    _bridge = bridge


def reset_bridge() -> None:
    global _bridge
    if _bridge is not None:
        try:
            _bridge.close()
        except Exception:  # pragma: no cover
            pass
    _bridge = None


__all__ = [
    "HermesBridge",
    "MockHermesBridge",
    "RealHermesBridge",
    "get_bridge",
    "reset_bridge",
    "set_bridge",
]
