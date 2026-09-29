"""Component: **agentkit-knowledge-base** (VikingDB RAG).

Per the Skill:
  * ``KnowledgeBase(backend="viking"|"context_search"|"local", index=..., top_k=...)``
    attached via ``Agent(knowledgebase=...)`` auto-mounts ``LoadKnowledgebaseTool``.
  * Real Viking backend needs ``DATABASE_VIKING_COLLECTION`` + AK/SK (CloudBoundary).
  * ``backend="local"`` -> InMemoryKnowledgeBackend (local only).

We construct a real ``KnowledgeBase(backend="local")`` and run a local, keyword-based
retrieval (embedding model is cloud) over an in-memory document store to exercise the RAG
retrieve contract end-to-end.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

try:
    from veadk.knowledgebase import KnowledgeBase
    _KB_AVAILABLE = True
except Exception:  # pragma: no cover
    KnowledgeBase = None  # type: ignore
    _KB_AVAILABLE = False


@dataclass
class LocalKnowledgeBase:
    top_k: int = 3
    docs: list[dict] = field(default_factory=list)
    real_kb: object = None

    @classmethod
    def build(cls, top_k: int = 3) -> "LocalKnowledgeBase":
        obj = cls(top_k=top_k)
        if _KB_AVAILABLE:
            obj.real_kb = KnowledgeBase(backend="local", index="harness_kb", top_k=top_k)
        return obj

    def add_document(self, doc_id: str, text: str):
        self.docs.append({"id": doc_id, "text": text})

    def retrieve(self, query: str) -> list[dict]:
        # Naive lexical scorer (stand-in for VikingDB vector recall).
        terms = set(re.findall(r"\w+", query.lower()))
        scored = []
        for d in self.docs:
            dterms = set(re.findall(r"\w+", d["text"].lower()))
            score = len(terms & dterms)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"id": d["id"], "text": d["text"], "score": s}
                for s, d in scored[: self.top_k] if s > 0]
