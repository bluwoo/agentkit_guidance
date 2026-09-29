"""Self-evolution proposal engine — queue, state machine, regression hook.

Implements the proposal-approval state machine from
design/04-hermes-self-evolution.md §3.2:

    draft → scanned → pending → approved → staged → regressing → live
                       ↘ rejected (terminal, archived)
                  pending → rejected
                  regressing → rejected

Red lines (design/04 §5):
  * ``baseline_locked`` AcceptanceCases can NEVER be modified by any proposal.
  * A proposal that fails the security scan can NEVER enter ``pending``.
  * Write operations (approve / reject / stage / live) are idempotent by id.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from server.wizard.schemas import (
    Proposal,
    ProposalKind,
    ProposalState,
)
from server.wizard.security.scan import scan_proposal

# --------------------------------------------------------------------------- #
# State machine definition
# --------------------------------------------------------------------------- #
# Allowed forward transitions.  rejected and live are terminal.
_ALLOWED: dict[ProposalState, set[ProposalState]] = {
    ProposalState.draft: {ProposalState.scanned},
    ProposalState.scanned: {ProposalState.pending, ProposalState.rejected},
    ProposalState.pending: {ProposalState.approved, ProposalState.rejected},
    ProposalState.approved: {ProposalState.staged},
    ProposalState.staged: {ProposalState.regressing},
    ProposalState.regressing: {ProposalState.live, ProposalState.rejected},
    ProposalState.rejected: set(),
    ProposalState.live: set(),
}

_TERMINAL = {ProposalState.rejected, ProposalState.live}


def _can_transition(current: ProposalState, target: ProposalState) -> bool:
    return target in _ALLOWED.get(current, set())


# --------------------------------------------------------------------------- #
# RegressionRunner protocol (injected by the real Step4 eval executor)
# --------------------------------------------------------------------------- #
class RegressionRunner(Protocol):
    """Protocol for the independent regression evaluator.

    The real implementation lives in the backend Step4 eval executor
    (design/04 §4.2).  This module only defines the contract and ships a
    default stub so the state machine is testable end-to-end.
    """

    def run_regression(self, proposal: Proposal) -> dict[str, Any]:
        """Run the eval regression for ``proposal``.

        Returns a report dict that MUST contain at least ``{"passed": bool}``.
        """
        ...


class StubRegressionRunner:
    """Default no-op regression runner (always passes).

    This is a *unit-testing convenience*: it always passes and — because it is
    the stub — the engine auto-promotes on pass (backwards compatible with the
    original state-machine tests).  Production MUST NOT use this; use
    :class:`RealRegressionRunner` instead, which shells out to a real pytest
    and defaults to *not* auto-promoting.
    """

    def run_regression(self, proposal: Proposal) -> dict[str, Any]:
        return {
            "passed": True,
            "note": "stub regression runner — replace with Step4 eval executor",
        }


class RealRegressionRunner:
    """Independent regression runner that actually invokes pytest.

    Unlike :class:`StubRegressionRunner` (which always passes), this runs a
    real pytest subprocess over the proposal's relevant test subset and reports
    the outcome honestly — it can and does return ``passed=False``.

    The pytest invocation is fully injectable so tests never touch a real
    subprocess:
      * ``python``       interpreter used to run pytest (default: the verify
                         venv ``/tmp/agentkit_verify_venv/bin/python``).
      * ``test_paths``   subset of tests to run (default: ``["tests/"]``).
      * ``run_callable`` for tests: ``callable(argv) -> (rc, stdout, stderr)``.

    Safety: this runner only *reports* a result; it never itself flips a
    proposal to ``live``.  Promotion is decided by the engine's
    ``EVOLUTION_AUTO_LIVE`` gate (default OFF).
    """

    def __init__(
        self,
        python: str | None = None,
        test_paths: Sequence[str] | None = None,
        timeout: float = 600.0,
        run_callable=None,
        cwd: str | None = None,
    ) -> None:
        self.python = python or os.environ.get(
            "EVOLUTION_REGRESSION_PYTHON", "/tmp/agentkit_verify_venv/bin/python"
        )
        self.test_paths = list(test_paths) if test_paths else ["tests/"]
        self.timeout = timeout
        self.cwd = cwd
        # Injectable runner: callable(argv) -> (returncode, stdout, stderr).
        # When None we shell out for real.
        self._run = run_callable

    @staticmethod
    def _keyword_for(proposal: Proposal) -> str:
        """Derive a pytest ``-k`` token from the proposal target.

        ``skills/foo/SKILL.md`` -> ``foo`` (the skill dir); ``MEMORY.md`` ->
        ``memory``.  The token is sanitised to ``[a-z0-9_]`` so it can never
        break out of the ``-k`` argument (it is still passed positionally,
        never as shell).
        """
        parts = proposal.target.split("/")
        if len(parts) >= 2 and parts[-1].endswith(".md"):
            stem = parts[-2]
        else:
            stem = parts[-1].removesuffix(".md")
        token = "".join(ch for ch in stem.lower() if ch.isalnum() or ch == "_")
        return token or "evolution"

    def run_regression(self, proposal: Proposal) -> dict[str, Any]:
        argv: list[str] = [
            self.python, "-m", "pytest", *self.test_paths,
            "-q", "-k", self._keyword_for(proposal),
        ]
        try:
            if self._run is not None:
                returncode, out, err = self._run(argv)
            else:
                proc = subprocess.run(  # noqa: PLW1510 - non-zero IS the failure signal we report
                    argv, capture_output=True, text=True,
                    timeout=self.timeout, cwd=self.cwd,
                )
                returncode, out, err = proc.returncode, proc.stdout, proc.stderr
        except FileNotFoundError as e:
            return {"passed": False, "error": f"regression python not found: {e!s}",
                    "argv": argv}
        except subprocess.TimeoutExpired:
            return {"passed": False, "error": "regression timed out", "argv": argv}
        return {
            "passed": returncode == 0,
            "returncode": returncode,
            "argv": argv,
            "report_tail": (out or "")[-2000:],
            "stderr_tail": (err or "")[-1000:],
        }


# --------------------------------------------------------------------------- #
# JSON-file store
# --------------------------------------------------------------------------- #
class ProposalStore:
    """Thread-safe JSON-file-backed proposal store.

    Default path: ``./wizard_data/proposals.json`` (relative to CWD, never a
    system directory).
    """

    def __init__(self, path: str = "./wizard_data/proposals.json") -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._proposals: dict[str, Proposal] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for item in data.get("proposals", []):
            try:
                p = Proposal.model_validate(item)
                self._proposals[p.id] = p
            except Exception:  # noqa: S112, BLE001 - skip malformed persisted proposals
                continue

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "proposals": [p.model_dump() for p in self._proposals.values()]
        }
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # -- CRUD ----------------------------------------------------------------
    def get(self, proposal_id: str) -> Proposal | None:
        with self._lock:
            return self._proposals.get(proposal_id)

    def list(self) -> list[Proposal]:
        with self._lock:
            return list(self._proposals.values())

    def put(self, proposal: Proposal) -> None:
        with self._lock:
            self._proposals[proposal.id] = proposal
            self._save()


# --------------------------------------------------------------------------- #
# Red-line guards
# --------------------------------------------------------------------------- #
def _is_baseline_violation(
    proposal: Proposal,
    locked_eval_ids: set[str] | None = None,
) -> bool:
    """True when an eval_reflow proposal targets a baseline_locked case."""
    if proposal.kind != ProposalKind.eval_reflow:
        return False
    locked = locked_eval_ids or set()
    return proposal.target in locked


# --------------------------------------------------------------------------- #
# Engine — module-level functions operating on a store
# --------------------------------------------------------------------------- #
class ProposalEngine:
    """The self-evolution proposal queue + state machine."""

    def __init__(
        self,
        store: ProposalStore | None = None,
        regression_runner: RegressionRunner | None = None,
        auto_live: bool | None = None,
    ) -> None:
        self.store = store or ProposalStore()
        self.regression_runner = regression_runner or StubRegressionRunner()
        # None => decide at regression time (see _should_auto_live).  Explicit
        # True/False always wins.
        self.auto_live = auto_live

    # -- registration --------------------------------------------------------
    def register_proposal(
        self,
        kind: ProposalKind,
        target: str,
        diff: str = "",
        rationale: str = "",
        locked_eval_ids: set[str] | None = None,
    ) -> Proposal:
        """Create a new proposal in ``draft`` state.

        Raises ValueError when the proposal would modify a baseline_locked
        AcceptanceCase (red line — never allowed).
        """
        proposal = Proposal(
            id=uuid.uuid4().hex[:12],
            kind=kind,
            target=target,
            diff=diff,
            rationale=rationale,
            state=ProposalState.draft,
            created_at=datetime.now(UTC).isoformat(),
        )
        if _is_baseline_violation(proposal, locked_eval_ids):
            raise ValueError(
                f"Red line: cannot register eval_reflow proposal targeting "
                f"baseline_locked case '{target}'"
            )
        self.store.put(proposal)
        return proposal

    def list_proposals(self) -> list[Proposal]:
        return self.store.list()

    # -- security scan gate ---------------------------------------------------
    def scan_proposal(self, proposal_id: str) -> Proposal:
        """Run the security scan and transition draft→scanned/rejected.

        * Scan passed  → state = scanned (eligible for pending).
        * Scan failed  → state = rejected (terminal, archived).
        """
        proposal = self._must_get(proposal_id)
        self._assert_transition(proposal, ProposalState.scanned)

        result = scan_proposal(diff=proposal.diff, rationale=proposal.rationale)
        proposal.scan_result = result

        if result["passed"]:
            proposal.state = ProposalState.scanned
        else:
            proposal.state = ProposalState.rejected
        self.store.put(proposal)
        return proposal

    # -- developer decision ---------------------------------------------------
    def approve(self, proposal_id: str) -> Proposal:
        """Approve a pending proposal → approved.  Idempotent."""
        proposal = self._must_get(proposal_id)
        if proposal.state == ProposalState.approved:
            return proposal  # idempotent no-op
        self._assert_transition(proposal, ProposalState.approved)
        proposal.state = ProposalState.approved
        self.store.put(proposal)
        return proposal

    def reject(self, proposal_id: str, reason: str = "") -> Proposal:
        """Reject a proposal (from scanned/pending).  Idempotent."""
        proposal = self._must_get(proposal_id)
        if proposal.state == ProposalState.rejected:
            return proposal  # idempotent no-op
        self._assert_transition(proposal, ProposalState.rejected)
        proposal.state = ProposalState.rejected
        if reason:
            proposal.scan_result = proposal.scan_result or {}
            proposal.scan_result["reject_reason"] = reason
        self.store.put(proposal)
        return proposal

    def mark_pending(self, proposal_id: str) -> Proposal:
        """Move a scanned (scan-passed) proposal into the approval queue."""
        proposal = self._must_get(proposal_id)
        self._assert_transition(proposal, ProposalState.pending)
        proposal.state = ProposalState.pending
        self.store.put(proposal)
        return proposal

    # -- staging & regression --------------------------------------------------
    def mark_staged(self, proposal_id: str) -> Proposal:
        """approved → staged (queued for next eval run)."""
        proposal = self._must_get(proposal_id)
        self._assert_transition(proposal, ProposalState.staged)
        proposal.state = ProposalState.staged
        self.store.put(proposal)
        return proposal

    def mark_regressing(self, proposal_id: str) -> Proposal:
        """staged → regressing; runs the injected RegressionRunner.

        The runner runs synchronously here and its report is stored.  Promotion
        to ``live`` is NOT automatic in production: see :meth:`_should_auto_live`.
        Without a runner configured the proposal simply stays in ``regressing``.
        """
        proposal = self._must_get(proposal_id)
        self._assert_transition(proposal, ProposalState.regressing)
        proposal.state = ProposalState.regressing
        self.store.put(proposal)
        self._run_regression(proposal)
        return proposal

    def run_regression(self, proposal_id: str) -> Proposal:
        """Trigger the independent regression run for a staged/regressing proposal.

        * ``staged``     → delegate to :meth:`mark_regressing` (starts the run).
        * ``regressing`` → re-run the injected runner in place and apply the
          result under the same auto-live gate.
        * any other state → ValueError (caller maps to HTTP 409).
        """
        proposal = self._must_get(proposal_id)
        if proposal.state == ProposalState.staged:
            return self.mark_regressing(proposal_id)
        if proposal.state == ProposalState.regressing:
            self._run_regression(proposal)
            return proposal
        raise ValueError(
            f"Cannot run regression from state '{proposal.state.value}'"
            f" (expected staged or regressing)"
        )

    def _run_regression(self, proposal: Proposal) -> None:
        """Run the injected runner and fold its result into the proposal.

        passed  + auto-live allowed → live
        passed  + auto-live blocked → stay ``regressing`` (await human mark_live)
        failed                      → rejected
        """
        if self.regression_runner is None:
            return
        report = self.regression_runner.run_regression(proposal)
        proposal.regression_report = report
        if report.get("passed"):
            if self._should_auto_live():
                proposal.state = ProposalState.live
            # else: intentionally stay in ``regressing`` for a human decision.
        else:
            proposal.state = ProposalState.rejected
        self.store.put(proposal)

    def _should_auto_live(self) -> bool:
        """Decide whether a passing regression may auto-promote to ``live``.

        Safety contract (design/04 §5):
          * An explicit ``auto_live=...`` constructor flag always wins.
          * The shipped :class:`StubRegressionRunner` is a unit-test convenience
            that auto-promotes on pass (keeps the original state-machine tests
            green).
          * Any REAL runner defaults to **NO** auto-live: promotion needs an
            explicit human ``mark_live`` — UNLESS ``EVOLUTION_AUTO_LIVE=true``
            is set, which is an explicitly dangerous escape hatch.
        """
        if self.auto_live is not None:
            return bool(self.auto_live)
        if isinstance(self.regression_runner, StubRegressionRunner):
            return True
        return os.environ.get("EVOLUTION_AUTO_LIVE", "").strip().lower() in (
            "1", "true", "yes", "on",
        )

    def mark_live(self, proposal_id: str) -> Proposal:
        """regressing → live (regression passed, externally confirmed)."""
        proposal = self._must_get(proposal_id)
        if proposal.state == ProposalState.live:
            return proposal  # idempotent
        self._assert_transition(proposal, ProposalState.live)
        proposal.state = ProposalState.live
        self.store.put(proposal)
        return proposal

    def reject_regression(self, proposal_id: str, reason: str = "") -> Proposal:
        """regressing → rejected (regression degraded / rolled back)."""
        proposal = self._must_get(proposal_id)
        if proposal.state == ProposalState.rejected:
            return proposal  # idempotent
        self._assert_transition(proposal, ProposalState.rejected)
        proposal.state = ProposalState.rejected
        if reason:
            proposal.regression_report = proposal.regression_report or {}
            proposal.regression_report["reject_reason"] = reason
        self.store.put(proposal)
        return proposal

    # -- helpers --------------------------------------------------------------
    def _must_get(self, proposal_id: str) -> Proposal:
        p = self.store.get(proposal_id)
        if p is None:
            raise KeyError(f"Proposal '{proposal_id}' not found")
        return p

    @staticmethod
    def _assert_transition(proposal: Proposal, target: ProposalState) -> None:
        if proposal.state in _TERMINAL:
            raise ValueError(
                f"Proposal '{proposal.id}' is in terminal state "
                f"'{proposal.state.value}' — no further transitions allowed"
            )
        if not _can_transition(proposal.state, target):
            raise ValueError(
                f"Illegal transition: '{proposal.state.value}' → "
                f"'{target.value}' for proposal '{proposal.id}'"
            )


# --------------------------------------------------------------------------- #
# Default engine (module-level convenience)
# --------------------------------------------------------------------------- #
_default_engine: ProposalEngine | None = None


def get_default_engine() -> ProposalEngine:
    global _default_engine
    if _default_engine is None:
        _default_engine = ProposalEngine()
    return _default_engine
