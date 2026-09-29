"""Component catalog route: GET /api/wizard/components."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from server.wizard.components.catalog import list_components

router = APIRouter(tags=["components"])


@router.get("/components")
async def get_components() -> dict[str, Any]:
    cards = list_components()
    return {"components": cards, "count": len(cards)}


__all__ = ["router"]
