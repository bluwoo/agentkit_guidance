"""Step-3 architecture routes (frontend/03 §2.1).

  POST /api/wizard/architecture/recommend  {goal_card, cases} -> component cards
  GET  /api/wizard/architecture             design-time Topology draft
  PUT  /api/wizard/architecture             save Topology
  POST /api/wizard/architecture/validate   dependency/permission/required check
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.wizard.components.catalog import get_component
from server.wizard.schemas import Topology, ValidationIssue
from server.wizard.store import draft_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/architecture", tags=["architecture"])
TOPOLOGY_KEY = "current"


class RecommendRequest(BaseModel):
    goal_card: dict[str, Any] = Field(default_factory=dict)
    cases: list[dict[str, Any]] = Field(default_factory=list)


# Rule map: GoalCard signal -> component_id. Mirrors design/02 §3.1.
_RULES = [
    ("rag", "knowledge_base:vikingdb"),
    ("tool_call", "gateway:mcp"),
    ("code_exec", "sandbox:code"),
    ("multi_agent", "agent:adk-workflow"),
]


@router.post("/recommend")
async def recommend_components(body: RecommendRequest) -> dict[str, Any]:
    """Recommend components from GoalCard signals.

    Design rule (frontend/03 §2.1): the API only returns resources that really
    exist; when there is no signal we return an empty array and the frontend
    shows guidance text. We never invent a recommendation.
    """
    gc = body.goal_card or {}
    cls = (gc.get("classification") or "").lower()
    recommended: list[dict[str, Any]] = []

    seen = set()
    for signal, cid in _RULES:
        if cls == signal and cid not in seen:
            card = get_component(cid)
            if card:
                recommended.append(card)
                seen.add(cid)

    # Always-on suggestions for a production agent (cheap, true for all):
    if gc:
        for cid in ("observability:apmplus", "identity:permission", "guardrails:firewall"):
            if cid not in seen and (card := get_component(cid)):
                recommended.append(card)
                seen.add(cid)

    return {"recommended": recommended, "count": len(recommended)}


@router.get("")
async def get_topology() -> dict[str, Any]:
    return draft_store.get_draft("topology", TOPOLOGY_KEY) or Topology().model_dump()


@router.put("")
async def put_topology(topology: Topology) -> dict[str, Any]:
    draft_store.put_draft("topology", TOPOLOGY_KEY, topology.model_dump())
    return {"saved": True, "topology": topology.model_dump()}


@router.post("/validate")
async def validate_topology(topology: Topology) -> dict[str, Any]:
    """Real-time design-time validation: required fields, dangling edges,
    permission prerequisites. Returns ValidationIssue list; never raises on a
    merely-incomplete design."""
    issues: list[ValidationIssue] = []
    known_ids = {n.component_id for n in topology.nodes}

    # 1) every edge endpoint must exist
    for e in topology.edges:
        if e.source not in known_ids:
            issues.append(ValidationIssue(
                severity="error", code="edge.source.missing",
                message=f"edge {e.edge_id} source '{e.source}' is not a node",
                component_id=e.source))
        if e.target not in known_ids:
            issues.append(ValidationIssue(
                severity="error", code="edge.target.missing",
                message=f"edge {e.edge_id} target '{e.target}' is not a node",
                component_id=e.target))

    # 2) required fields per node kind
    for n in topology.nodes:
        if not n.label:
            issues.append(ValidationIssue(
                severity="error", code="node.label.missing",
                message="node has empty label", component_id=n.component_id))

    # 3) permission prerequisites: production-facing kinds warn when identity missing
    prod_kinds = {"gateway", "mcp", "knowledge_base", "a2a"}
    kinds_present = {n.kind.value for n in topology.nodes}
    if kinds_present & prod_kinds and "identity" not in kinds_present:
        issues.append(ValidationIssue(
            severity="warning", code="identity.missing",
            message="exposed gateway/mcp/knowledge-base without an identity-permission node"))

    # 4) observability presence (Step4 needs it)
    if topology.nodes and "observability" not in kinds_present:
        issues.append(ValidationIssue(
            severity="warning", code="observability.missing",
            message="no observability node: Step4 trace overlay will have no data source"))

    return {"valid": not any(i.severity == "error" for i in issues),
            "issues": [i.model_dump() for i in issues]}


__all__ = ["router"]
