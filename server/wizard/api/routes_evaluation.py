"""Step-2 acceptance / evaluation routes (frontend/03 §2.1 + §5).

  GET/PUT /api/wizard/evaluation/cases        AcceptanceCase CRUD
  POST    /api/wizard/evaluation/recommend    suggest judgment type from GoalCard
  GET     /api/wizard/evaluation/datasets     -> {connected:false} when unlinked
  POST    /api/wizard/evaluation/import-cases stub
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.wizard.api.routes_runtime_proxy import proxy_invoke
from server.wizard.schemas import (
    AcceptanceCase,
    EvaluationCaseResult,
    EvaluationRun,
    JudgmentType,
    RuntimeInvokeRequest,
)
from server.wizard.store import draft_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])
CASES_KEY = "current"


class RecommendRequest(BaseModel):
    goal_card: dict[str, Any] = Field(default_factory=dict)
    cases: list[AcceptanceCase] = Field(default_factory=list)


@router.get("/cases")
async def get_cases() -> dict[str, Any]:
    data = draft_store.get_draft("cases", CASES_KEY) or {"cases": []}
    return data


@router.put("/cases")
async def put_cases(cases: list[AcceptanceCase]) -> dict[str, Any]:
    """Replace the local case list. ``baseline_locked`` stays per-case; the
    self-evolution engine may never rewrite a locked case (enforced there)."""
    data = {"cases": [c.model_dump() for c in cases]}
    draft_store.put_draft("cases", CASES_KEY, data)
    return {"saved": len(cases)}


@router.post("/recommend")
async def recommend_judgment(body: RecommendRequest) -> dict[str, Any]:
    """Suggest a judgment type per goal-card signal. No external service — a
    deterministic rule map. Never fabricates an evaluator the platform lacks."""
    gc = body.goal_card or {}
    cls = (gc.get("classification") or "").lower()
    hints: list[dict[str, str]] = []
    if cls == "rag":
        hints.append({"judgment_type": JudgmentType.artifact.value,
                      "reason": "RAG: assert the answer cites the retrieved slice"})
    if cls in ("tool_call", "multi_agent"):
        hints.append({"judgment_type": JudgmentType.rule.value,
                      "reason": "tool_call: assert isError=false on tools/call + downstream state"})
    if cls == "code_exec":
        hints.append({"judgment_type": JudgmentType.artifact.value,
                      "reason": "code_exec: assert the produced artifact/tests pass"})
    hints.append({"judgment_type": JudgmentType.llm_judge.value,
                   "reason": "semantic quality coverage via built-in evaluator + human calibration"})
    return {"recommendations": hints}


@router.get("/datasets")
async def list_datasets() -> dict[str, Any]:
    """Not linked to the AgentKit eval service in this stage -> honest stub."""
    return {"connected": False, "datasets": []}


class ImportCasesRequest(BaseModel):
    dataset_id: str = ""
    cases: list[AcceptanceCase] = Field(default_factory=list)


class RunEvaluationRequest(BaseModel):
    runtime_id: str
    cases: list[AcceptanceCase] = Field(default_factory=list)
    user_id: str = "wizard-evaluator"
    session_id: str = ""


def _judge(case: AcceptanceCase, actual: str, status_code: int) -> EvaluationCaseResult:
    expected = case.expected.strip()
    detail = case.judgment_detail or {}
    if case.judgment_type in (JudgmentType.rule, JudgmentType.artifact):
        mode = str(detail.get("operator") or "contains")
        if mode == "equals":
            passed = actual.strip() == expected
            reason = "actual output equals expected output" if passed else "actual output differs from expected output"
        elif mode == "status_code":
            wanted = int(detail.get("status_code", 200))
            passed = status_code == wanted
            reason = f"HTTP status {status_code}; expected {wanted}"
        else:
            passed = bool(expected) and expected.casefold() in actual.casefold()
            reason = "expected text appears in actual output" if passed else "expected text was not found in actual output"
        evidence = {"operator": mode, "expected": expected, "status_code": status_code}
    elif case.judgment_type == JudgmentType.external_state:
        passed = False
        reason = "external-state checker is not configured for this case"
        evidence = {"configured": False, "required": detail}
    else:
        passed = False
        reason = "LLM-as-Judge is not configured for this case"
        evidence = {"configured": False, "required": detail}
    return EvaluationCaseResult(
        eval_id=case.eval_id,
        passed=passed,
        judgment_type=case.judgment_type,
        actual_output=actual,
        evidence=evidence,
        reason=reason,
    )


@router.post("/run")
async def run_evaluation(body: RunEvaluationRequest) -> dict[str, Any]:
    """Run cases against a real allowlisted target Runtime and judge outputs.

    A failed or unconfigured judge stays failed.  The endpoint never interprets
    an Agent's completion claim as evidence.
    """
    run_id = f"eval-{uuid.uuid4().hex[:12]}"
    session_id = body.session_id or run_id
    results: list[EvaluationCaseResult] = []
    last_trace_id: str | None = None
    for case in body.cases:
        response = await proxy_invoke(RuntimeInvokeRequest(
            runtime_id=body.runtime_id,
            input=case.input_sample,
            user_id=body.user_id,
            session_id=f"{session_id}-{case.eval_id}",
            stream=False,
        ))
        last_trace_id = response.trace_id or last_trace_id
        if response.error:
            results.append(EvaluationCaseResult(
                eval_id=case.eval_id,
                passed=False,
                judgment_type=case.judgment_type,
                actual_output=response.output,
                evidence={"status_code": response.status_code, "trace_id": response.trace_id},
                reason=response.error,
            ))
        else:
            result = _judge(case, response.output, response.status_code)
            result.evidence["trace_id"] = response.trace_id
            results.append(result)
    run = EvaluationRun(
        run_id=run_id,
        runtime_id=body.runtime_id,
        trace_id=last_trace_id,
        passed=sum(1 for item in results if item.passed),
        failed=sum(1 for item in results if not item.passed),
        results=results,
    )
    draft_store.put_draft("evaluation-run", "latest", run.model_dump())
    return run.model_dump()


@router.get("/runs/latest")
async def latest_evaluation_run() -> dict[str, Any]:
    return draft_store.get_draft("evaluation-run", "latest") or {}


@router.post("/import-cases")
async def import_cases(body: ImportCasesRequest) -> dict[str, Any]:
    """Stub: the eval service is not connected. We record the request and
    return not_connected; we do not pretend the import happened."""
    return {
        "imported": 0,
        "connected": False,
        "note": "evaluation service not connected; cases kept locally only",
        "requested": len(body.cases),
    }


__all__ = ["router"]
