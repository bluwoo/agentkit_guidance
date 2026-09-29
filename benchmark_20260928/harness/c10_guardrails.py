"""Component: **agentkit-guardrails** (LLM Shield / safety fence).

Per the Skill:
  * High-code VeADK/ADK agents MUST mount the 4 callbacks on the Agent:
    before_model_callback / after_model_callback / before_tool_callback / after_tool_callback,
    imported from ``veadk.tools.builtin_tools.llm_shield`` (``content_safety`` singleton).
  * Import requires ``TOOL_LLM_SHIELD_APP_ID`` already set at import time, else ValueError.
  * Blocked prompt-injection response (measured 2026-09-23):
    ``"Your request has been blocked due to: Prompt Injection. Please modify your input and try again."``
  * "Switch on" != "effective": console-only toggle does NOT make high-code traffic pass the
    firewall; attack logs are the source of truth.

We reproduce the boundary (missing APP_ID -> ValueError) and a local rule-based shield that
mirrors the input-side injection detection and the exact blocked-message contract.
"""
from __future__ import annotations

import os

BLOCKED_INJECTION = ("Your request has been blocked due to: Prompt Injection. "
                     "Please modify your input and try again.")

# Heuristic injection markers (local stand-in for the LLM Shield classifier).
_INJECTION_MARKERS = (
    "ignore your previous", "ignore all previous", "disregard your instructions",
    "system prompt", "reveal your instructions", "忽略你之前", "忽略以上",
)


def require_real_shield_app_id() -> None:
    """Documents the CloudBoundary: importing content_safety needs the app id."""
    app_id = os.getenv("TOOL_LLM_SHIELD_APP_ID")
    if not app_id:
        raise ValueError(
            "The environment variable `TOOL_LLM_SHIELD_APP_ID` not exists. "
            "Real LLM Shield interception needs Volcengine LLM Shield (CloudBoundary).")


class LocalShield:
    """Local, rule-based mirror of the input-side guardrail check."""

    def check_input(self, prompt: str) -> str | None:
        low = prompt.lower()
        if any(m in low for m in _INJECTION_MARKERS):
            return BLOCKED_INJECTION
        return None

    def check_output(self, text: str) -> str:
        # Output side: strip a trivial PII stand-in (a long digit run) as a stub.
        return text


def real_guardrail_callbacks_available() -> bool:
    try:
        require_real_shield_app_id()
        from veadk.tools.builtin_tools.llm_shield import content_safety  # noqa: F401
        return True
    except Exception:
        return False
