"""Integration tests: business routes via TestClient + MockHermesBridge.

observability / evolution are thin-forwarded to sibling modules; here we stub
their entrypoints with monkeypatch so these tests don't depend on the sibling
modules' internals (which another owner is still writing).
"""
from __future__ import annotations


def test_components_endpoint(client):
    r = client.get("/api/wizard/components")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 14
    assert len(body["components"]) == 14


def test_invoke_endpoint(client):
    r = client.post("/invoke", json={"session_id": "it1", "message": "step3 架构"})
    assert r.status_code == 200
    assert "Step3" in r.json()["reply"]


def test_biz_goal_chat_sse(client):
    # First message starts the grill flow; SSE should carry question events.
    r = client.post("/api/wizard/biz-goal/chat",
                    json={"session_id": "grill-it", "message": ""})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    body = r.text
    assert "event: question" in body
    assert "Q1" in body
    # Follow-up message settles a frontier decision.
    r2 = client.post("/api/wizard/biz-goal/chat",
                     json={"session_id": "grill-it", "message": "1. 运营同学\n2. 聚类工单\n3. 否"})
    assert r2.status_code == 200
    assert "event: point" in r2.text or "event: glossary" in r2.text


def test_goalcard_roundtrip(client):
    card = {"name": "工单聚类", "task": "聚类工单", "target_user": "运营"}
    assert client.put("/api/wizard/biz-goal", json=card).status_code == 200
    got = client.get("/api/wizard/biz-goal").json()
    assert got["task"] == "聚类工单"


def test_architecture_recommend_empty_when_no_signal(client):
    # No GoalCard classification -> only always-on suggestions (observability/identity/guardrails).
    r = client.post("/api/wizard/architecture/recommend",
                    json={"goal_card": {}, "cases": []})
    assert r.status_code == 200
    # Empty/weak signal must never fabricate a RAG/tool component.
    recs = [c["component_id"] for c in r.json()["recommended"]]
    assert "knowledge_base:vikingdb" not in recs


def test_architecture_recommend_rag_signal(client):
    r = client.post("/api/wizard/architecture/recommend",
                    json={"goal_card": {"classification": "rag"}, "cases": []})
    recs = [c["component_id"] for c in r.json()["recommended"]]
    assert "knowledge_base:vikingdb" in recs


def test_architecture_validate_dangling_edge(client):
    topo = {
        "nodes": [{"component_id": "agent:a", "kind": "agent", "label": "A"}],
        "edges": [{"edge_id": "e1", "source": "agent:a", "target": "ghost"}],
    }
    r = client.post("/api/wizard/architecture/validate", json=topo)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert any(i["code"] == "edge.target.missing" for i in body["issues"])


def test_runtime_proxy_rejects_unknown_runtime_id(client):
    r = client.post("/api/wizard/runtime/invoke",
                    json={"runtime_id": "nope", "input": "hi"})
    # Unknown runtime_id -> 400 (whitelist SSRF guard).
    assert r.status_code in (400, 422)


def test_evaluation_datasets_not_connected(client):
    r = client.get("/api/wizard/evaluation/datasets")
    assert r.json()["connected"] is False


def test_observability_trace_stubbed(client, monkeypatch):
    # Stub the lazy-loaded observability service entrypoint.
    import server.wizard.api.routes_observability as obs
    from server.wizard.schemas import TraceOverlay, TraceStatus

    def fake_overlay(runtime_id, trace_id, design_topology):
        return TraceOverlay(trace_id=trace_id, status=TraceStatus.not_configured,
                            error="stubbed")

    monkeypatch.setattr(obs, "_load_service",
                        lambda: ({"get_trace_overlay": fake_overlay,
                                  "get_aggregate_panel": lambda **k: {"connected": False},
                                  "get_logs": lambda **k: {"logs": []}}, None))
    r = client.get("/api/wizard/observability/trace",
                   params={"runtime_id": "r", "trace_id": "t1"})
    assert r.status_code == 200
    assert r.json()["status"] == "not_configured"


def test_evolution_proposal_approve_idempotent(client, monkeypatch):
    # Stub the engine: a tiny in-memory fake satisfying the used methods.
    from server.wizard.schemas import Proposal, ProposalState

    class FakeEngine:
        def __init__(self):
            self.store = {}

        def list_proposals(self):
            return list(self.store.values())

        def register_proposal(self, kind, target, diff="", rationale="", locked_eval_ids=None):
            p = Proposal(id="p1", kind=kind, target=target, diff=diff, rationale=rationale)
            self.store["p1"] = p
            return p

        def approve(self, pid):
            p = self.store[pid]
            if p.state == ProposalState.approved:
                return p  # idempotent
            p.state = ProposalState.approved
            return p

        def reject(self, pid, reason=""):
            p = self.store[pid]
            p.state = ProposalState.rejected
            return p

    import server.wizard.api.routes_evolution as evo
    engine = FakeEngine()
    monkeypatch.setattr(evo, "_load_engine", lambda: (engine, None))

    created = client.post("/api/wizard/evolution/proposals",
                          json={"kind": "memory", "target": "MEMORY.md", "rationale": "x"})
    assert created.status_code == 200
    assert created.json()["proposal"]["state"] == "draft"

    a1 = client.post("/api/wizard/evolution/proposals/p1/approve")
    assert a1.status_code == 200
    assert a1.json()["proposal"]["state"] == "approved"
    assert a1.json()["idempotent"] is True

    # Second approve must be a no-op idempotently.
    a2 = client.post("/api/wizard/evolution/proposals/p1/approve")
    assert a2.status_code == 200
    assert a2.json()["proposal"]["state"] == "approved"
    assert engine.store["p1"].state == ProposalState.approved
