"""Aggregate Wizard business router mounted under ``/api/wizard``."""
from fastapi import APIRouter

from server.wizard.api import (
    routes_architecture,
    routes_biz_goal,
    routes_components,
    routes_evaluation,
    routes_evolution,
    routes_observability,
    routes_runtime_proxy,
)


def build_wizard_router() -> APIRouter:
    router = APIRouter()
    router.include_router(routes_biz_goal.router)
    router.include_router(routes_evaluation.router)
    router.include_router(routes_components.router)
    router.include_router(routes_architecture.router)
    router.include_router(routes_runtime_proxy.router)
    router.include_router(routes_observability.router)
    router.include_router(routes_evolution.router)
    return router


__all__ = ["build_wizard_router"]
