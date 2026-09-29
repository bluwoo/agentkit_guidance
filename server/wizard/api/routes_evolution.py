"""Thin self-evolution proposal routes (frontend/03 §5 + design 01 §4.5).

  GET  /api/wizard/evolution/proposals              list
  POST /api/wizard/evolution/proposals              create (draft)
  POST /api/wizard/evolution/proposals/{id}/approve
  POST /api/wizard/evolution/proposals/{id}/reject
  POST /api/wizard/evolution/trigger                failure -> auto-draft proposal
  GET  /api/wizard/evolution/proposals/{id}/regression  run independent regression

Forwards to ``server.wizard.evolution.proposals.ProposalEngine`` (another
module). Lazy import; missing module -> not_configured. Approve/reject are
idempotent (the engine already treats repeat approvals as no-ops) and we append
an audit-log line on every transition.

Closed-loop safety:
  * ``/trigger`` only *proposes* (register -> security scan -> pending).  A
    malicious diff lands in ``rejected``, never pending.
  * Nothing here auto-promotes to ``live``.  Regression passes stay in
    ``regressing`` unless ``EVOLUTION_AUTO_LIVE=true`` (explicitly dangerous,
    default off); a human ``mark_live`` is the normal path.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evolution", tags=["evolution"])

_AUDIT: list[dict[str, Any]] = []


def _audit(action: str, proposal_id: str, state: str) -> None:
    _AUDIT.append({
        "ts": datetime.now(UTC).isoformat(),
        "action": action,
        "proposal_id": proposal_id,
        "state": state,
    })


def _load_engine():
    """Return (engine, None) or (None, error). Never raises."""
    try:
        from server.wizard.evolution.proposals import get_default_engine  # noqa: WPS433
        return get_default_engine(), None
    except Exception as e:  # pragma: no cover
        return None, f"evolution engine unavailable: {e}"


class CreateProposalRequest(BaseModel):
    kind: str = "memory"
    target: str = ""
    diff: str = ""
    rationale: str = ""


class RejectRequest(BaseModel):
    reason: str = ""


class TriggerRequest(BaseModel):
    """Failure signal that auto-drafts a self-evolution proposal.

    The HTTP entry carries just the failure essentials; the richer programmatic
    entry (``on_eval_failure``) also accepts full span lists and the design
    topology.  Here we rebuild a minimal rule-judged AcceptanceCase.
    """
    case_id: str
    observed: str = ""
    expected: str = ""
    trace_id: str = ""


@router.get("/proposals")
async def list_proposals() -> dict[str, Any]:
    engine, err = _load_engine()
    if err:
        return {"connected": False, "proposals": [], "note": err}
    items = engine.list_proposals()
    return {"proposals": [p.model_dump() for p in items], "count": len(items)}


@router.post("/proposals")
async def create_proposal(req: CreateProposalRequest) -> dict[str, Any]:
    engine, err = _load_engine()
    if err:
        raise HTTPException(status_code=503, detail=err)
    from server.wizard.schemas import ProposalKind
    try:
        kind = ProposalKind(req.kind)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"unknown proposal kind '{req.kind}'")
    try:
        p = engine.register_proposal(kind=kind, target=req.target,
                                     diff=req.diff, rationale=req.rationale)
    except ValueError as e:
        # baseline-locked red line -> 409, message only (no stack)
        raise HTTPException(status_code=409, detail=str(e))
    _audit("create", p.id, p.state.value)
    return {"proposal": p.model_dump()}


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str) -> dict[str, Any]:
    engine, err = _load_engine()
    if err:
        raise HTTPException(status_code=503, detail=err)
    try:
        p = engine.approve(proposal_id)  # idempotent in the engine
    except KeyError:
        raise HTTPException(status_code=404, detail="proposal not found")
    _audit("approve", p.id, p.state.value)
    return {"proposal": p.model_dump(), "idempotent": True, "audit_tail": _AUDIT[-1]}


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, req: RejectRequest) -> dict[str, Any]:
    engine, err = _load_engine()
    if err:
        raise HTTPException(status_code=503, detail=err)
    try:
        p = engine.reject(proposal_id, reason=req.reason)  # idempotent
    except KeyError:
        raise HTTPException(status_code=404, detail="proposal not found")
    _audit("reject", p.id, p.state.value)
    return {"proposal": p.model_dump(), "idempotent": True, "audit_tail": _AUDIT[-1]}


@router.post("/trigger")
async def trigger_evolution(req: TriggerRequest) -> dict[str, Any]:
    """Failure-driven entry: draft (and scan) ONE proposal from a failed case.

    Returns the created proposal.  A clean scan lands it in ``pending``; a
    security hit lands it in ``rejected``.  Never auto-lives.
    """
    engine, err = _load_engine()
    if err:
        raise HTTPException(status_code=503, detail=err)
    from server.wizard.evolution.trigger import on_eval_failure
    from server.wizard.schemas import AcceptanceCase, JudgmentType

    case = AcceptanceCase(
        eval_id=req.case_id,
        expected=req.expected,
        judgment_type=JudgmentType.rule,
    )
    try:
        p = on_eval_failure(
            case=case,
            observed=req.observed,
            expected=req.expected,
            trace_spans=None,
            topo=None,
            engine=engine,
            trace_id=req.trace_id,
        )
    except ValueError as e:
        # baseline-locked red line -> 409
        raise HTTPException(status_code=409, detail=str(e))
    _audit("trigger", p.id, p.state.value)
    return {"proposal": p.model_dump(), "state": p.state.value}


@router.get("/proposals/{proposal_id}/regression")
async def run_proposal_regression(proposal_id: str) -> dict[str, Any]:
    """Trigger the independent regression run for a staged/regressing proposal.

    Runs the injected RegressionRunner (RealRegressionRunner shells out to
    pytest).  A passing run does NOT auto-live unless ``EVOLUTION_AUTO_LIVE``
    is explicitly set; otherwise the proposal stays in ``regressing`` awaiting
    a human ``mark_live``.
    """
    engine, err = _load_engine()
    if err:
        raise HTTPException(status_code=503, detail=err)
    try:
        p = engine.run_regression(proposal_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="proposal not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    _audit("regression", p.id, p.state.value)
    return {
        "proposal": p.model_dump(),
        "regression_report": p.regression_report,
        "auto_live": engine._should_auto_live(),  # expose the gate for the UI
    }


__all__ = ["router"]
