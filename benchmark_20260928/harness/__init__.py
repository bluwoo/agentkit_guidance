"""AgentKit minimal Harness — 14 components wired together.

A from-scratch integration example covering every formal AgentKit component:
veadk, agentkit-sdk, runtime, adk-workflow, skills, session-memory, gateway-mcp,
a2a-registry, sandbox, guardrails, identity-permission, knowledge-base,
observability, evaluation.

Cloud-dependent edges are flagged (see contract.CloudBoundary); nothing here calls
Volcengine.
"""
from . import contract  # noqa: F401

__all__ = ["contract"]
__version__ = "0.1.0"
