"""Step-1 business-goal routes (frontend/03 §2.1).

  POST /api/wizard/biz-goal/chat             SSE grill interview (grill adapter)
  POST /api/wizard/biz-goal/points/confirm   user confirms/adjusts points
  POST /api/wizard/biz-goal/adr              ADR draft from confirmed points
  GET  /api/wizard/biz-goal/glossary
  POST /api/wizard/biz-goal/generate         quick-mode GoalCard draft
  GET  /api/wizard/biz-goal                  read GoalCard draft
  PUT  /api/wizard/biz-goal                  save GoalCard draft
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.wizard.grill.adapter import GrillAdapter
from server.wizard.schemas import ConfirmedPoint, GoalCard
from server.wizard.store import draft_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/biz-goal", tags=["biz-goal"])

# A single adapter instance; it is stateless except for the fact dispatcher.
_adapter = GrillAdapter()

GOALCARD_KEY = "current"


class ChatRequest(BaseModel):
    session_id: str = ""
    message: str = ""


class PointsConfirmRequest(BaseModel):
    session_id: str = "default"
    points: list[ConfirmedPoint] = Field(default_factory=list)


class AdrRequest(BaseModel):
    session_id: str = "default"
    title: str = ""
    context: str = ""


class GlossaryItem(BaseModel):
    term: str
    definition: str = ""


class GlossaryRequest(BaseModel):
    session_id: str = "default"
    items: list[GlossaryItem] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    name: str = ""
    description: str = ""


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def biz_goal_chat(body: ChatRequest) -> StreamingResponse:
    """SSE-stream the grill interview. First call starts the flow; follow-ups
    settle the frontier and emit the next round + domain-modeling events."""
    session_id = body.session_id or "default"
    events: list[str] = []

    def sink(kind: str, payload: dict[str, Any]) -> None:
        events.append(_sse(kind, payload))

    state = draft_store.get_session_state(session_id)
    if not state or not state.get("started"):
        _adapter.start(session_id, sink)
    else:
        _adapter.handle_message(session_id, body.message, sink)

    async def stream():
        for chunk in events:
            yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/points/confirm")
async def confirm_points(body: PointsConfirmRequest) -> dict[str, Any]:
    """Persist confirmed points and fold them into the GoalCard draft."""
    existing = draft_store.get_draft("goalcard", GOALCARD_KEY) or {}
    confirmed = [p.model_dump() for p in body.points if p.confirmed]
    existing["confirmed_points"] = confirmed
    # Best-effort: pull task/target_user from confirmed points when present.
    for p in body.points:
        if p.id == "task" and p.confirmed:
            existing["task"] = p.text
        if p.id == "target_user" and p.confirmed:
            existing["target_user"] = p.text
    draft_store.put_draft("goalcard", GOALCARD_KEY, existing)
    return {"saved": len(confirmed), "draft": existing}


@router.post("/adr")
async def propose_adr(body: AdrRequest) -> dict[str, Any]:
    """Return an ADR draft. The three ADR conditions (hard to reverse /
    surprising / real trade-off) are already enforced by the adapter; here we
    just materialize a proposed ADR and persist it."""
    draft = {
        "title": body.title or "Untitled decision",
        "context": body.context,
        "status": "proposed",
    }
    existing = draft_store.get_draft("adr", body.session_id) or []
    if isinstance(existing, list):
        existing.append(draft)
    else:
        existing = [draft]
    draft_store.put_draft("adr", body.session_id, existing)
    return {"adr": draft, "total": len(existing)}


@router.get("/glossary")
async def get_glossary(session_id: str = "default") -> dict[str, Any]:
    data = draft_store.get_draft("glossary", session_id) or {"items": []}
    return data


@router.put("/glossary")
async def put_glossary(body: GlossaryRequest) -> dict[str, Any]:
    data = {"items": [i.model_dump() for i in body.items]}
    draft_store.put_draft("glossary", body.session_id, data)
    return {"saved": len(data["items"])}


@router.post("/generate")
async def quick_generate(body: GenerateRequest) -> dict[str, Any]:
    """Prompt fast-mode: synthesize a first GoalCard draft from a one-liner.

    This is a deterministic scaffold (not a fabrication): it copies the user's
    own words into the card and leaves the rest empty for the user to fill.
    """
    card = GoalCard(name=body.name, task=body.description).model_dump()
    draft_store.put_draft("goalcard", GOALCARD_KEY, card)
    return {"goal_card": card}


@router.get("")
async def get_goalcard() -> dict[str, Any]:
    return draft_store.get_draft("goalcard", GOALCARD_KEY) or GoalCard().model_dump()


@router.put("")
async def put_goalcard(card: GoalCard) -> dict[str, Any]:
    draft_store.put_draft("goalcard", GOALCARD_KEY, card.model_dump())
    return {"saved": True, "goal_card": card.model_dump()}


__all__ = ["router"]
