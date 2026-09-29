"""grill-with-docs compatibility scheduling adapter.

The upstream ``grill-with-docs`` skill says (verbatim):

    Call the Skill tool twice, for "grilling" and "domain-modeling".

That targets a host that has a "Skill tool". Hermes has no such tool, so this
adapter translates the instruction into two in-process sub-flows within one
conversation turn:

  1. **grilling** — design-tree frontier. We keep a fixed design tree of
     GoalCard decisions; the *frontier* is every decision whose prerequisites
     are already settled. A round asks the whole frontier at once as numbered
     questions ``Q1/Q2...`` each with a recommended answer. The user's answers
     settle decisions and push the frontier outward; we recompute and ask the
     next round until the frontier is empty.
  2. **domain-modeling** — as terms crystallise, we emit glossary events (a
     lazily-created CONTEXT.md) and propose an ADR only when all three
     conditions hold (hard to reverse / surprising without context / real
     trade-off).

The entry point is **explicit**: the frontend calls
``/api/wizard/biz-goal/chat`` which calls :meth:`GrillAdapter.start` — matching
``disable-model-invocation: true`` (the flow does not auto-start).

A ``FactDispatcher`` seam is provided for grilling's "find facts yourself"
rule; under the Mock bridge we never actually spawn a sub-agent, we just record
the fact query as an open dependency.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from server.wizard.store.draft_store import get_session_state, put_session_state


# --------------------------------------------------------------------------- #
# Design tree (GoalCard decisions)
# --------------------------------------------------------------------------- #
@dataclass
class Decision:
    key: str
    title: str
    body: str
    recommended: str
    prereqs: list[str] = field(default_factory=list)
    settled: str | None = None  # the user's answer text once settled


# The GoalCard design tree (mirrors design/02-eval-driven-flow.md Step1).
# Order here is irrelevant; the frontier is computed from ``prereqs``.
def _build_tree() -> list[Decision]:
    return [
        Decision(
            key="target_user",
            title="目标用户是谁",
            body="这个 Agent 服务谁？角色与使用场景是什么？",
            recommended="一个明确的角色 + 一句场景，如「运营同学，在飞书里批量整理客服工单」。",
            prereqs=[],
        ),
        Decision(
            key="task",
            title="业务任务是什么",
            body="Agent 要替用户完成的核心动作是什么？用一个动词短语。",
            recommended="「把一段客户反馈聚类成工单并起草回复」。",
            prereqs=[],
        ),
        Decision(
            key="migration",
            title="是否存量迁移",
            body="你已有现成 Agent 吗？如果有，是什么框架（LangChain / LangGraph / ADK / Strands / Dify）？",
            recommended="「否」——全新构建；若是存量，框架名即可。",
            prereqs=[],
        ),
        Decision(
            key="typical_input",
            title="典型输入长什么样",
            body="用户会怎么发起？有没有附件 / 文件 / 多轮上下文？",
            recommended="一条自由文本 + 可选工单 JSON。",
            prereqs=["task"],
        ),
        Decision(
            key="expected_output",
            title="期望产出 / 成功标准",
            body="什么样算完成？一句话成功标准。",
            recommended="「输出聚类结果 + 每条带一条草稿回复，人工确认后发送」。",
            prereqs=["task"],
        ),
        Decision(
            key="non_goals",
            title="非目标 / 边界",
            body="明确不做什么，防止 scope 蔓延。",
            recommended="「不直接自动发送回复；不处理非工单类反馈」。",
            prereqs=["target_user", "task"],
        ),
        Decision(
            key="classification",
            title="任务类型归类",
            body="这更像哪一类：rag（知识问答）/ tool_call（调工具）/ code_exec（跑代码）/ multi_agent（多智能体）？",
            recommended="按主路径判断；多数工单聚类属 tool_call。",
            prereqs=["task", "expected_output"],
        ),
        Decision(
            key="long_running",
            title="是否长链路任务",
            body="跨系统排障 / 日志分析 / 代码迁移类？长链路易漂移，需要 Sidecar 治理四件套。",
            recommended="「否」；若单次要跨多个下游并等待 > 数分钟则「是」。",
            prereqs=["task"],
        ),
    ]


# Decisions whose settlement qualifies for an ADR (all three ADR conditions:
# hard to reverse + surprising + real trade-off). This is a deliberately small,
# conservative set — most answers are glossary, not architecture decisions.
_ADR_WORTHY = {
    "migration": "迁移到 AgentKit 的框架选择",
    "long_running": "是否引入 Sidecar 治理四件套",
    "classification": "任务主路径的架构形态",
}


# --------------------------------------------------------------------------- #
# Fact dispatcher seam (grilling: find facts yourself, never ask the user)
# --------------------------------------------------------------------------- #
class FactDispatcher(Protocol):
    def dispatch(self, query: str) -> str:  # pragma: no cover - interface
        ...


class MockFactDispatcher:
    """Records a fact query without spawning a real sub-agent (offline)."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def dispatch(self, query: str) -> str:
        self.queries.append(query)
        return f"(fact lookup queued: {query})"


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
@dataclass
class GrillState:
    decisions: dict[str, str] = field(default_factory=dict)  # key -> answer
    round_no: int = 0
    started: bool = False
    glossary: dict[str, str] = field(default_factory=dict)  # term -> definition
    adrs: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decisions": self.decisions,
            "round_no": self.round_no,
            "started": self.started,
            "glossary": self.glossary,
            "adrs": self.adrs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GrillState:
        if not data:
            return cls()
        return cls(
            decisions=dict(data.get("decisions", {})),
            round_no=int(data.get("round_no", 0)),
            started=bool(data.get("started", False)),
            glossary=dict(data.get("glossary", {})),
            adrs=list(data.get("adrs", [])),
        )


# --------------------------------------------------------------------------- #
# Adapter
# --------------------------------------------------------------------------- #
EventSink = Callable[[str, dict[str, Any]], None]


class GrillAdapter:
    """Translates grill-with-docs into an in-process two-sub-flow state machine."""

    def __init__(self, fact_dispatcher: FactDispatcher | None = None) -> None:
        self._tree = _build_tree()
        self.fact_dispatcher = fact_dispatcher or MockFactDispatcher()

    # -- persistence helpers --
    def _load(self, session_id: str) -> GrillState:
        return GrillState.from_dict(get_session_state(session_id))

    def _save(self, session_id: str, state: GrillState) -> None:
        put_session_state(session_id, state.to_dict())

    # -- frontier computation --
    def _frontier(self, state: GrillState) -> list[Decision]:
        out: list[Decision] = []
        for d in self._tree:
            if d.key in state.decisions:
                continue
            if all(p in state.decisions for p in d.prereqs):
                out.append(d)
        return out

    # -- entry point (explicit, disable-model-invocation) --
    def start(self, session_id: str, sink: EventSink) -> None:
        """Begin (or restart) the interview; emit the first frontier round."""
        state = GrillState()
        state.started = True
        state.round_no = 1
        frontier = self._frontier(state)
        sink("grill_start", {"round": state.round_no, "count": len(frontier)})
        self._emit_round(frontier, sink)
        self._save(session_id, state)

    def _emit_round(self, frontier: list[Decision], sink: EventSink) -> None:
        for i, d in enumerate(frontier, start=1):
            sink(
                "question",
                {
                    "qid": f"Q{i}",
                    "key": d.key,
                    "title": d.title,
                    "body": d.body,
                    "recommended": d.recommended,
                },
            )

    # -- answer handling: grilling + domain-modeling in one turn --
    def handle_message(
        self, session_id: str, user_text: str, sink: EventSink
    ) -> dict[str, Any]:
        """Process a user reply. Returns a summary; structured events go to sink."""
        state = self._load(session_id)
        if not state.started:
            # Explicit-entry safety: a chat message before "start" kicks off.
            self.start(session_id, sink)
            state = self._load(session_id)
            return {"started": True}

        # 1) grilling: settle the frontier decisions the user just answered.
        answered = self._parse_answers(user_text, self._frontier(state))
        for key, answer in answered.items():
            state.decisions[key] = answer
            # emit a confirmed point event
            sink("point", {"key": key, "text": answer, "confirmed": True})

        # 2) domain-modeling: extract resolved terms into the glossary.
        self._update_glossary(user_text, state, sink)

        # 3) domain-modeling: propose ADRs for freshly-settled ADR-worthy keys.
        self._maybe_propose_adrs(answered, state, sink)

        # 4) recompute frontier -> next round, or finish.
        state.round_no += 1
        frontier = self._frontier(state)
        if frontier:
            sink("round", {"round": state.round_no, "count": len(frontier)})
            self._emit_round(frontier, sink)
        else:
            sink("done", {"message": "frontier empty: shared understanding reached"})

        self._save(session_id, state)
        return {
            "settled": list(answered.keys()),
            "remaining": len(frontier),
            "finished": not frontier,
        }

    # -- parsing: best-effort; the user can also just talk freely --
    def _parse_answers(self, user_text: str, frontier: list[Decision]) -> dict[str, str]:
        """Map free-text onto the open frontier decisions.

        Heuristic: a frontier decision is considered answered if the user's
        message is non-empty and we have no structured per-question delimiter.
        We attach the whole message to the first unsettled decision and, when
        multiple frontier questions are open, split on numbered markers
        (``1.`` / ``Q1`` / line breaks). A deterministic, testable fallback.
        """
        text = (user_text or "").strip()
        if not text or not frontier:
            return {}

        # Try to split by explicit "Q1"/"1." markers.
        pieces = re.split(r"(?:^|\n)\s*(?:Q?(\d+)[\.\):]\s*)", text)
        # pieces = [pre, num1, body1, num2, body2, ...]
        chunks: dict[int, str] = {}
        if len(pieces) >= 3:
            it = iter(pieces[1:])
            for num_str, body in zip(it, it):
                try:
                    chunks[int(num_str)] = body.strip()
                except ValueError:  # pragma: no cover
                    continue

        answered: dict[str, str] = {}
        for i, d in enumerate(frontier, start=1):
            if chunks.get(i):
                answered[d.key] = chunks[i]
            elif len(frontier) == 1:
                answered[d.key] = text
            # else: leave unanswered (frontier keeps it open)
        return answered

    def _update_glossary(self, user_text: str, state: GrillState, sink: EventSink) -> None:
        """Heuristic term extraction: any decision answer becomes a glossary
        entry keyed by its decision title. Keeps CONTEXT.md lazily populated.
        """
        for key, answer in state.decisions.items():
            term = {
                "target_user": "目标用户",
                "task": "业务任务",
                "non_goals": "非目标",
            }.get(key)
            if term and term not in state.glossary:
                state.glossary[term] = answer
                sink("glossary", {"term": term, "definition": answer})

    def _maybe_propose_adrs(
        self, answered: dict[str, str], state: GrillState, sink: EventSink
    ) -> None:
        for key, answer in answered.items():
            if key in _ADR_WORTHY and not any(a.get("key") == key for a in state.adrs):
                title = _ADR_WORTHY[key]
                adr = {
                    "key": key,
                    "title": title,
                    "status": "proposed",
                    "context": answer,
                    "conditions_met": ["hard_to_reverse", "surprising_without_context", "real_tradeoff"],
                }
                state.adrs.append(adr)
                sink("adr", adr)

    # -- quick-mode: build a GoalCard-shaped draft from settled decisions --
    def goal_card_from_state(self, state: GrillState) -> dict[str, Any]:
        d = state.decisions
        return {
            "name": d.get("task", ""),
            "target_user": d.get("target_user", ""),
            "task": d.get("task", ""),
            "typical_input": d.get("typical_input", ""),
            "expected_output": d.get("expected_output", ""),
            "non_goals": [d["non_goals"]] if d.get("non_goals") else [],
            "long_running": d.get("long_running", "").lower() in ("是", "yes", "true", "long"),
            "migration": d.get("migration") or None,
            "classification": d.get("classification") or None,
        }


__all__ = ["FactDispatcher", "GrillAdapter", "GrillState", "MockFactDispatcher"]
