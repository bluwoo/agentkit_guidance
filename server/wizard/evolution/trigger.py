"""Failure-driven self-evolution trigger — the missing closed loop.

Up to now the proposal engine was only reachable by hand-crafted API calls.
``on_eval_failure`` wires a *failing acceptance case* (or a trace that ended in
an ERROR span) into the proposal queue:

  1. Analyse the failure signal (judgment type + ERROR spans + topology).
  2. Draft exactly ONE proposal:
       * ERROR span in the trace   → ``skill``   (add a step / guidance that
                                          handles the observed error).
       * non-locked case with a    → ``eval_reflow`` (ADD a NEW non-baseline
         boundary hint                boundary case; the baseline itself is
                                          never edited).
       * otherwise                 → ``memory``  (long-term note: the case's
                                          failure pattern / the context that
                                          tripped it).
  3. Register (``draft``) → security scan → (scan passed) ``mark_pending``.

Hard guarantees (design/04-hermes-self-evolution.md §5):
  * The trigger ONLY proposes. It never edits a ``baseline_locked`` case,
    never touches permissions / deploy credentials, never promotes anything to
    ``live``.
  * A malicious diff (private key / prompt-injection, e.g. smuggled in via an
    adversarial ``observed`` string) is caught by the security scan and lands
    in ``rejected`` — it never reaches ``pending``.
  * Production promotion still requires:
        pending → (human) approve → staged → independent regression
                → (human) live.
    ``EVOLUTION_AUTO_LIVE`` defaults to OFF.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from server.wizard.evolution.proposals import ProposalEngine, get_default_engine
from server.wizard.schemas import (
    AcceptanceCase,
    ObservedSpan,
    Proposal,
    ProposalKind,
    ProposalState,
    Topology,
)


# --------------------------------------------------------------------------- #
# Signal analysis helpers
# --------------------------------------------------------------------------- #
def _as_case(case: AcceptanceCase | Mapping[str, Any]) -> AcceptanceCase:
    if isinstance(case, AcceptanceCase):
        return case
    return AcceptanceCase.model_validate(dict(case))


def _iter_error_spans(trace_spans: Iterable[Any] | None) -> list[ObservedSpan]:
    """Return the ERROR spans from a (possibly dict) span list."""
    errors: list[ObservedSpan] = []
    if not trace_spans:
        return errors
    for raw in trace_spans:
        try:
            span = (raw if isinstance(raw, ObservedSpan)
                    else ObservedSpan.model_validate(dict(raw)))
        except Exception:  # noqa: BLE001, S112 - tolerate malformed span payloads
            continue
        if getattr(span.status, "code", "") == "ERROR":
            errors.append(span)
    return errors


def _choose_kind(case: AcceptanceCase, has_error_span: bool) -> ProposalKind:
    """Pick exactly one proposal kind from the failure signal.

    A ``baseline_locked`` case can NEVER produce an ``eval_reflow`` proposal
    (the baseline is read-only): it degrades to ``skill`` (on error) or
    ``memory`` (otherwise).
    """
    if has_error_span:
        return ProposalKind.skill
    if not case.baseline_locked and case.boundary_case:
        return ProposalKind.eval_reflow
    return ProposalKind.memory


def _target_for(kind: ProposalKind, case: AcceptanceCase) -> str:
    if kind == ProposalKind.memory:
        return "MEMORY.md"
    if kind == ProposalKind.skill:
        return f"skills/{case.eval_id}/SKILL.md"
    # eval_reflow: reflow the failing case's eval suite by ADDING a new
    # non-baseline boundary sub-case.  Targeting the case id itself means the
    # engine's baseline guard fires immediately if the deployment locked it.
    return case.eval_id


# --------------------------------------------------------------------------- #
# Unified-diff style text builders
# --------------------------------------------------------------------------- #
def _unified(path: str, additions: list[str]) -> str:
    lines = [f"--- a/{path}", f"+++ b/{path}",
             "@@ proposed self-evolution additions (review before live) @@"]
    for line in additions:
        lines.append(f"+ {line}" if line else "+")
    return "\n".join(lines) + "\n"


def _build_diff(
    kind: ProposalKind,
    case: AcceptanceCase,
    observed: str,
    expected: str,
    trace_id: str,
    error_spans: list[ObservedSpan],
) -> str:
    observed_s = (observed or "").strip()
    expected_s = (expected or "").strip()

    if kind == ProposalKind.memory:
        return _unified("MEMORY.md", [
            f"## Failure memory: {case.eval_id}",
            f"- judgment_type: {case.judgment_type.value}",
            f"- expected: {expected_s}",
            f"- observed: {observed_s}",
            (f"- pattern: '{case.eval_id}' fails when runtime output diverges from "
             f"expected (trace {trace_id}); record context to stabilise."),
        ])

    if kind == ProposalKind.skill:
        first_err = error_spans[0] if error_spans else None
        err_name = getattr(first_err, "name", "") or "<span>"
        err_msg = (getattr(first_err.status, "error_message", "") or "").strip()
        return _unified(
            f"skills/{case.eval_id}/SKILL.md", [
                f"## Debugging step for '{case.eval_id}'",
                (f"- When trace {trace_id} shows ERROR span '{err_name}' "
                 f"(msg: {err_msg or 'n/a'}), retry with explicit guidance:"),
                f"- expected: {expected_s}",
                f"- observed: {observed_s}",
            ],
        )

    # eval_reflow — propose a NEW non-baseline boundary case.
    return _unified("eval_cases.md", [
        "## Suggested new boundary case (DO NOT modify baseline)",
        f"- id: {case.eval_id}__boundary_suggested",
        f"- input: {case.input_sample}",
        f"- expected: {expected_s}",
        f"- observed: {observed_s}",
        "- judgment_type: rule",
        f"- rationale: boundary gap '{case.boundary_case}' tripped in trace {trace_id}",
    ])


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def on_eval_failure(
    case: AcceptanceCase | Mapping[str, Any],
    observed: str,
    expected: str,
    trace_spans: Iterable[Any] | None = None,
    topo: Topology | Mapping[str, Any] | None = None,
    engine: ProposalEngine | None = None,
    locked_eval_ids: set[str] | None = None,
    trace_id: str = "",
) -> Proposal:
    """Analyse a failed eval case / error trace and register ONE proposal.

    Args:
        case: the failing AcceptanceCase (pydantic object or dict).
        observed: what the runtime actually produced.
        expected: what the case expected.
        trace_spans: optional list of ObservedSpan / dicts; any ``ERROR`` span
            drives a ``skill`` proposal.
        topo: optional design Topology (accepted; currently advisory only —
            it never auto-edits the graph).
        engine: ProposalEngine to use (defaults to the shared default engine).
        locked_eval_ids: deployment-locked eval ids; an ``eval_reflow``
            proposal targeting one raises ValueError (red line).
        trace_id: trace correlation id, echoed into the rationale.

    Returns:
        The created :class:`Proposal`.  Its state is:
          * ``pending`` when the security scan passed (awaiting human approval);
          * ``rejected`` when the scan caught a red-line pattern (e.g. an
            adversarial ``observed`` carrying a private key / injection).

    Raises:
        ValueError: if the resulting proposal would target a baseline_locked /
            locked eval id via ``eval_reflow`` (the engine's red-line guard).
    """
    case_obj = _as_case(case)
    error_spans = _iter_error_spans(trace_spans)
    has_error = bool(error_spans)
    kind = _choose_kind(case_obj, has_error)
    target = _target_for(kind, case_obj)
    trace_ref = trace_id or "unknown"
    diff = _build_diff(kind, case_obj, observed, expected, trace_ref, error_spans)

    rationale = (
        f"Auto-triggered by failing acceptance case '{case_obj.eval_id}' "
        f"(trace_id={trace_ref}, judgment_type={case_obj.judgment_type.value}). "
        f"observed={observed!r} expected={expected!r}. "
        f"Generated proposal kind={kind.value}. "
        f"This is a proposal ONLY: it does not modify the baseline, does not "
        f"touch permissions or deploy credentials, and must pass human approve "
        f"-> staged -> independent regression before it can ever go live."
    )

    engine = engine or get_default_engine()
    proposal = engine.register_proposal(
        kind=kind,
        target=target,
        diff=diff,
        rationale=rationale,
        locked_eval_ids=locked_eval_ids,
    )
    # draft -> scanned / rejected (security gate).
    proposal = engine.scan_proposal(proposal.id)
    # Only a clean scan may enter the approval queue.
    if proposal.state == ProposalState.scanned:
        proposal = engine.mark_pending(proposal.id)
    return proposal


__all__ = ["on_eval_failure"]
