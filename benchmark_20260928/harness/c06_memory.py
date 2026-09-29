"""Component: **agentkit-session-memory** (three-layer memory).

Per the Skill:
  * Session layer (PostgreSQL/MySQL) = "conversation ticket" keyed by
    (app_name, user_id, session_id).
  * Short-term context (Runner memory) = "working memory" for one run.
  * Long-term memory (mem0 / viking / local) = cross-session "diary"; written via
    ``await runner.save_session_to_long_term_memory(session_id=, user_id=)``.
  * ``LongTermMemory(backend=...)`` — default is ``opensearch``; production must be explicit.
    ``viking_mem`` is deprecated -> forwards to ``viking``.

We construct a **real** ``LongTermMemory(backend="local")`` (InMemoryLTMBackend) and provide a
local three-layer store for the session/short-term/long-term split. Cloud mem0/viking backends
are a documented CloudBoundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field

try:
    from veadk.memory.long_term_memory import LongTermMemory
    _LTM_AVAILABLE = True
except Exception:  # pragma: no cover
    LongTermMemory = None  # type: ignore
    _LTM_AVAILABLE = False


@dataclass
class LocalThreeLayerMemory:
    """A local, in-process realization of the three-layer model."""

    app_name: str = "harness_app"
    sessions: dict[str, list[str]] = field(default_factory=dict)       # session layer
    short_term: dict[str, list[str]] = field(default_factory=dict)    # per-run working memory
    long_term: dict[str, list[str]] = field(default_factory=dict)     # user_id -> facts
    real_ltm: object = None

    @classmethod
    def build(cls, app_name: str = "harness_app") -> "LocalThreeLayerMemory":
        obj = cls(app_name=app_name)
        if _LTM_AVAILABLE:
            # backend="local" -> InMemoryLTMBackend (no cloud)
            obj.real_ltm = LongTermMemory(backend="local", index=app_name)
        return obj

    def append_session(self, user_id: str, session_id: str, text: str):
        self.sessions.setdefault(f"{user_id}/{session_id}", []).append(text)

    def remember(self, user_id: str, fact: str):
        self.long_term.setdefault(user_id, []).append(fact)

    def recall(self, user_id: str) -> list[str]:
        return list(self.long_term.get(user_id, []))

    async def save_session_to_long_term_memory(self, session_id: str, user_id: str):
        # Mirrors Runner.save_session_to_long_term_memory(session_id, user_id) contract.
        for msg in self.sessions.get(f"{user_id}/{session_id}", []):
            if msg not in self.long_term.setdefault(user_id, []):
                self.long_term[user_id].append(msg)
        return {"session_id": session_id, "user_id": user_id, "saved": True}
