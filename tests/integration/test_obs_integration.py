"""Integration test: full trace overlay pipeline with mocked APMPlus client.

Monkeypatches the APMPlusClient transport to return fixture JSON instead of
hitting the real cloud.
"""
import json
from pathlib import Path

import server.wizard.observability.apmplus_client as apmplus_client_module
from server.wizard.observability.apmplus_client import APMPlusClient, APMPlusResponse
from server.wizard.observability.service import get_trace_overlay
from server.wizard.schemas import (
    EdgeType,
    NodeKind,
    Topology,
    TopologyEdge,
    TopologyNode,
    TraceStatus,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _topology() -> Topology:
    return Topology(
        nodes=[
            TopologyNode(component_id="runtime:agentkit-runtime",
                         kind=NodeKind.runtime, label="Runtime",
                         config={"service_name": "agentkit-runtime"}),
            TopologyNode(component_id="agent:target_agent",
                         kind=NodeKind.agent, label="Agent",
                         config={"agent_name": "target_agent"}),
            TopologyNode(component_id="model:doubao-pro-32k",
                         kind=NodeKind.model, label="Model",
                         config={"model": "doubao-pro-32k"}),
            TopologyNode(component_id="skill:search_docs",
                         kind=NodeKind.skill, label="Search",
                         skill_ref="search_docs"),
        ],
        edges=[
            TopologyEdge(edge_id="e1", source="runtime:agentkit-runtime",
                         target="agent:target_agent", type=EdgeType.sync),
            TopologyEdge(edge_id="e2", source="agent:target_agent",
                         target="model:doubao-pro-32k", type=EdgeType.sync),
            TopologyEdge(edge_id="e3", source="agent:target_agent",
                         target="skill:search_docs", type=EdgeType.sync),
        ],
    )


class _MockClient(APMPlusClient):
    """Returns fixture data without any real network call."""

    def __init__(self, payload: dict):
        self._payload = payload
        self.suggest_times: list[int] = []
        # Mark as configured so we don't short-circuit to not_configured
        self._ak = "fake-ak"
        self._sk = "fake-sk"

    def get_trace_detail(self, trace_id: str, suggest_time: int = 0) -> APMPlusResponse:
        self.suggest_times.append(suggest_time)
        return APMPlusResponse(status=TraceStatus.ok, payload=self._payload)


class TestTraceOverlayPipeline:
    def test_success_trace_full_pipeline(self):
        fixture = _load("apmplus_trace_success.json")
        client = _MockClient(fixture)
        overlay = get_trace_overlay(
            runtime_id="rt-1",
            trace_id="trace-success-001",
            design_topology=_topology(),
            client=client,
            poll_interval=0,
            poll_max_attempts=1,
            sleep_fn=lambda x: None,
        )
        assert overlay.status == TraceStatus.ok
        assert overlay.trace_id == "trace-success-001"
        assert client.suggest_times
        # Official GetTraceDetail expects epoch seconds, not milliseconds.
        assert 1_000_000_000 < client.suggest_times[0] < 10_000_000_000

        # node_runtime: 4 mapped nodes
        assert "runtime:agentkit-runtime" in overlay.node_runtime
        assert "agent:target_agent" in overlay.node_runtime
        assert "model:doubao-pro-32k" in overlay.node_runtime
        assert "skill:search_docs" in overlay.node_runtime

        # search_docs called twice (retry)
        assert overlay.node_runtime["skill:search_docs"]["count"] == 2
        assert overlay.node_runtime["model:doubao-pro-32k"]["state"] == "invoked"

        # edge: agent -> skill counted twice
        edge_key = "agent:target_agent->skill:search_docs"
        assert overlay.edge_runtime[edge_key]["count"] == 2

        # summary
        assert overlay.summary.span_nums == 5
        assert overlay.summary.error_span_ids == []

    def test_official_result_trace_envelope(self):
        fixture = _load("apmplus_trace_success.json")
        client = _MockClient({"Result": fixture})
        overlay = get_trace_overlay(
            runtime_id="rt-1",
            trace_id="trace-success-001",
            design_topology=_topology(),
            client=client,
            poll_interval=0,
            poll_max_attempts=1,
            sleep_fn=lambda x: None,
        )
        assert overlay.status == TraceStatus.ok
        assert overlay.summary.span_nums == 5

    def test_error_trace_full_pipeline(self):
        fixture = _load("apmplus_trace_error.json")
        client = _MockClient(fixture)
        overlay = get_trace_overlay(
            runtime_id="rt-1",
            trace_id="trace-error-002",
            design_topology=_topology(),
            client=client,
            poll_interval=0,
            poll_max_attempts=1,
            sleep_fn=lambda x: None,
        )
        assert overlay.status == TraceStatus.ok
        # model node in error
        assert overlay.node_runtime["model:doubao-pro-32k"]["state"] == "error"
        # unmapped spans surfaced
        assert len(overlay.observed_unmapped) == 2

    def test_empty_trace_polls_then_returns_empty(self):
        fixture = _load("apmplus_trace_empty.json")
        client = _MockClient(fixture)
        overlay = get_trace_overlay(
            runtime_id="rt-1",
            trace_id="trace-empty-003",
            design_topology=_topology(),
            client=client,
            poll_interval=0,
            poll_max_attempts=3,
            sleep_fn=lambda x: None,
        )
        assert overlay.status == TraceStatus.empty


class TestNotConfigured:
    def test_explicit_empty_credentials_do_not_use_runtime_iam(self, monkeypatch):
        """Explicit empty credentials keep the client disabled."""
        monkeypatch.setattr(
            apmplus_client_module.Path,
            "read_text",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("IAM should not be read")
            ),
        )
        client = APMPlusClient(ak="", sk="")
        assert client.is_configured() is False

    def test_runtime_iam_credentials_are_used_when_env_missing(self, monkeypatch):
        """AgentKit Runtime can query APMPlus with its short-lived IAM file."""
        for key in (
            "APMPLUS_ACCESS_KEY",
            "APMPLUS_SECRET_KEY",
            "VOLCENGINE_ACCESS_KEY",
            "VOLCENGINE_SECRET_KEY",
            "VOLCENGINE_SESSION_TOKEN",
            "VOLC_SESSIONTOKEN",
        ):
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setattr(
            apmplus_client_module.Path,
            "read_text",
            lambda *args, **kwargs: json.dumps(
                {
                    "access_key_id": "runtime-ak",
                    "secret_access_key": "runtime-sk",
                    "session_token": "runtime-session-token",
                }
            ),
        )
        client = APMPlusClient()
        assert client.is_configured() is True
        assert client._session_token == "runtime-session-token"

    def test_session_token_is_forwarded_to_signer(self, monkeypatch):
        captured: dict[str, str] = {}

        def fake_build(action, body, ak, sk, session_token=""):
            captured["session_token"] = session_token
            return "https://example.invalid", {}, b"{}"

        class FakeClient:
            def __init__(self, **kwargs):
                pass

            def post(self, *args, **kwargs):
                import httpx

                return httpx.Response(200, json={"Result": {}})

            def close(self):
                pass

        monkeypatch.setattr(apmplus_client_module, "_build_signed_request", fake_build)
        monkeypatch.setattr(apmplus_client_module.httpx, "Client", FakeClient)
        response = APMPlusClient(
            ak="runtime-ak", sk="runtime-sk", session_token="runtime-token"
        ).get_trace_detail("trace")
        assert response.ok
        assert captured["session_token"] == "runtime-token"

    def test_not_configured_short_circuits(self):
        """When AK/SK missing, status is not_configured without polling."""
        client = APMPlusClient(ak="", sk="")  # not configured
        overlay = get_trace_overlay(
            runtime_id="rt-1",
            trace_id="t",
            design_topology=_topology(),
            client=client,
            poll_interval=0,
            poll_max_attempts=1,
            sleep_fn=lambda x: None,
        )
        assert overlay.status == TraceStatus.not_configured
