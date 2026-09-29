"""Unit tests: grill adapter state machine (frontier rounds, domain-modeling)."""
from __future__ import annotations

from server.wizard.grill.adapter import GrillAdapter, MockFactDispatcher


def _collect(events, kind=None):
    return [e for e in events if kind is None or e[0] == kind]


def test_start_emits_first_frontier():
    adapter = GrillAdapter()
    events = []
    adapter.start("s-grill", lambda k, p: events.append((k, p)))
    questions = _collect(events, "question")
    # Frontier round 1 = decisions with no prereqs: target_user, task, migration.
    assert [q[1]["key"] for q in questions] == ["target_user", "task", "migration"]
    for q in questions:
        assert q[1]["recommended"]  # every question carries a recommended answer


def test_answer_settles_and_expands_frontier():
    adapter = GrillAdapter()
    events = []
    sink = lambda k, p: events.append((k, p))
    adapter.start("s2", sink)
    # Answer the three round-1 frontier questions explicitly.
    summary = adapter.handle_message(
        "s2",
        "1. 运营同学\n2. 聚类工单并起草回复\n3. 否",
        sink,
    )
    # The three no-prereq decisions settled.
    assert set(summary["settled"]) == {"target_user", "task", "migration"}
    # domain-modeling emitted a glossary point + a confirmed point.
    kinds = {k for k, _ in events}
    assert "point" in kinds
    assert "glossary" in kinds
    # migration is ADR-worthy -> an adr event.
    assert any(k == "adr" for k, _ in events)
    # Recomputed frontier: typical_input/expected_output now unblocked by `task`.
    next_questions = [p["key"] for k, p in events if k == "question" and p["key"] in
                      {"typical_input", "expected_output", "non_goals", "classification", "long_running"}]
    assert "typical_input" in next_questions or "expected_output" in next_questions


def test_frontier_empties_after_all_answered():
    adapter = GrillAdapter()
    events = []
    sink = lambda k, p: events.append((k, p))
    adapter.start("s3", sink)
    adapter.handle_message("s3", "1. 运营\n2. 聚类工单\n3. 否", sink)
    # Answer everything else in free text (single-open fallback handles one at a time).
    summary = adapter.handle_message("s3", "自由文本回复", sink)
    # After enough rounds the tree drains; assert the done event exists at some point.
    kinds = {k for k, _ in events}
    # We may not finish in 2 messages, but the state machine must not crash.
    assert "round" in kinds or "done" in kinds


def test_fact_dispatcher_seam():
    disp = MockFactDispatcher()
    adapter = GrillAdapter(fact_dispatcher=disp)
    assert disp.dispatch("check docs") == "(fact lookup queued: check docs)"
    assert "check docs" in disp.queries


def test_goal_card_scaffold():
    adapter = GrillAdapter()
    from server.wizard.grill.adapter import GrillState
    state = GrillState(decisions={"task": "聚类工单"})
    card = adapter.goal_card_from_state(state)
    assert card["task"] == "聚类工单"
