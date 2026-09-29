"""Integration tests: the self-evolution closed loop.

Exercises the full human-in-the-loop chain end to end:

    failing case --on_eval_failure--> pending -> approve -> staged
                 -> independent regression -> (human) live

and proves the two safety properties:
  * a failing regression never reaches ``live``;
  * a passing regression does NOT auto-promote unless EVOLUTION_AUTO_LIVE is
    explicitly set (default off).
"""
from __future__ import annotations

import pytest

from server.wizard.evolution.proposals import (
    ProposalEngine,
    ProposalStore,
    StubRegressionRunner,
)
from server.wizard.evolution.trigger import on_eval_failure
from server.wizard.schemas import (
    AcceptanceCase,
    JudgmentType,
    ProposalKind,
    ProposalState,
)


class _ControllableRunner:
    """A non-stub runner whose pass/fail we control per test."""

    def __init__(self, passed: bool = True) -> None:
        self.passed = passed
        self.calls = 0

    def run_regression(self, proposal):
        self.calls += 1
        return {"passed": self.passed, "note": "controllable fake runner",
                "proposal_id": proposal.id}


@pytest.fixture
def engine(tmp_path):
    store = ProposalStore(str(tmp_path / "proposals.json"))
    return ProposalEngine(store=store, regression_runner=StubRegressionRunner())


def _draft_pending(engine) -> str:
    """Register -> scan -> mark_pending a clean memory proposal, return id."""
    case = AcceptanceCase(eval_id="eval_loop_001", expected="ok",
                          judgment_type=JudgmentType.rule)
    p = on_eval_failure(case=case, observed="bad", expected="ok",
                        trace_spans=None, engine=engine, trace_id="t-loop")
    assert p.state == ProposalState.pending
    return p.id


class TestFullLoop:
    def test_pending_to_live_full_chain(self, engine):
        pid = _draft_pending(engine)
        engine.approve(pid)            # pending -> approved
        engine.mark_staged(pid)        # approved -> staged
        p = engine.mark_regressing(pid)  # staged -> regressing -> live (stub)
        assert p.state == ProposalState.live

    def test_approve_idempotent(self, engine):
        pid = _draft_pending(engine)
        p1 = engine.approve(pid)
        p2 = engine.approve(pid)  # repeat must be a no-op, not an error
        assert p1.state == p2.state == ProposalState.approved

    def test_regression_failure_never_live(self, tmp_path):
        """A non-stub runner that FAILS must land the proposal in rejected."""
        store = ProposalStore(str(tmp_path / "p.json"))
        runner = _ControllableRunner(passed=False)
        eng = ProposalEngine(store=store, regression_runner=runner)
        pid = _draft_pending(eng)
        eng.approve(pid)
        eng.mark_staged(pid)
        p = eng.mark_regressing(pid)
        assert p.state == ProposalState.rejected
        assert p.regression_report["passed"] is False


class TestNoAutoLiveByDefault:
    def test_passing_regression_stays_regressing_when_env_unset(
        self, tmp_path, monkeypatch
    ):
        """Production default: even a PASSING regression does NOT auto-live."""
        monkeypatch.delenv("EVOLUTION_AUTO_LIVE", raising=False)
        store = ProposalStore(str(tmp_path / "p.json"))
        runner = _ControllableRunner(passed=True)  # non-stub, passes
        eng = ProposalEngine(store=store, regression_runner=runner)
        pid = _draft_pending(eng)
        eng.approve(pid)
        eng.mark_staged(pid)
        p = eng.mark_regressing(pid)
        # Regression ran and passed, but we must STOP at regressing.
        assert p.state == ProposalState.regressing
        assert runner.calls == 1
        # A human must then explicitly confirm live.
        p = eng.mark_live(pid)
        assert p.state == ProposalState.live

    def test_auto_live_only_when_env_explicitly_true(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("EVOLUTION_AUTO_LIVE", "true")
        store = ProposalStore(str(tmp_path / "p.json"))
        runner = _ControllableRunner(passed=True)
        eng = ProposalEngine(store=store, regression_runner=runner)
        pid = _draft_pending(eng)
        eng.approve(pid)
        eng.mark_staged(pid)
        p = eng.mark_regressing(pid)
        assert p.state == ProposalState.live  # only because the escape hatch is on

    def test_auto_live_any_other_value_stays_off(self, tmp_path, monkeypatch):
        monkeypatch.setenv("EVOLUTION_AUTO_LIVE", "false")
        store = ProposalStore(str(tmp_path / "p.json"))
        runner = _ControllableRunner(passed=True)
        eng = ProposalEngine(store=store, regression_runner=runner)
        pid = _draft_pending(eng)
        eng.approve(pid)
        eng.mark_staged(pid)
        p = eng.mark_regressing(pid)
        assert p.state == ProposalState.regressing


class TestHttpClosedLoop:
    def test_trigger_endpoint_creates_pending_proposal(self, client, tmp_path, monkeypatch):
        import server.wizard.api.routes_evolution as evo

        store = ProposalStore(str(tmp_path / "p.json"))
        eng = ProposalEngine(store=store, regression_runner=_ControllableRunner())
        monkeypatch.setattr(evo, "_load_engine", lambda: (eng, None))

        r = client.post("/api/wizard/evolution/trigger", json={
            "case_id": "eval_http_001",
            "observed": "wrong output",
            "expected": "right output",
            "trace_id": "trace-http",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["state"] == "pending"
        assert body["proposal"]["kind"] == ProposalKind.memory.value

    def test_regression_endpoint_runs_and_respects_gate(
        self, client, tmp_path, monkeypatch
    ):
        import server.wizard.api.routes_evolution as evo

        monkeypatch.delenv("EVOLUTION_AUTO_LIVE", raising=False)
        store = ProposalStore(str(tmp_path / "p.json"))
        runner = _ControllableRunner(passed=True)
        eng = ProposalEngine(store=store, regression_runner=runner)
        monkeypatch.setattr(evo, "_load_engine", lambda: (eng, None))

        # get the proposal to staged
        pid = _draft_pending(eng)
        eng.approve(pid)
        eng.mark_staged(pid)

        r = client.get(f"/api/wizard/evolution/proposals/{pid}/regression")
        assert r.status_code == 200
        body = r.json()
        # passed, but auto-live off => stays regressing
        assert body["proposal"]["state"] == "regressing"
        assert body["regression_report"]["passed"] is True
        assert body["auto_live"] is False
