"""Integration tests: /run_sse streaming behaviour.

Covers:
  * delta events arrive in order, done event carries a non-empty trace_id.
  * error events return a generic message (never leak str(e) to the client).
  * concurrent / sequential /run_sse calls do not crosstalk between sessions.
  * /run_sse is behind KeyAuth when RUNTIME_API_KEY is configured.

The OTel helpers (``start_span`` / ``current_trace_id``) are monkeypatched in
the ``runtime_protocol`` namespace so the trace_id is deterministic and we can
prove it crossed the worker-thread boundary.
"""
from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient

FAKE_TRACE_ID = "<TRACE_ID>"


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class _FakeSpan:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return None

    def set_attribute(self, k, v):
        pass


def _fake_start_span(name, **attrs):
    return _FakeSpan()


def _fake_trace_id():
    return FAKE_TRACE_ID


class FakeBridge:
    """Streams three deltas in a fixed order; records session_ids seen."""

    name = "fake"

    def __init__(self):
        self.calls: list[str] = []

    def new_session(self, session_id: str = "", user_id: str = "") -> str:
        return session_id or f"sess-fake-{uuid.uuid4().hex[:8]}"

    def turn(self, session_id, user_id, message, on_delta=None):
        self.calls.append(session_id)
        chunks = ["alpha-", "beta-", "gamma"]
        if on_delta is not None:
            for c in chunks:
                on_delta(c)
        return {"reply": "alpha-beta-gamma", "session_id": session_id, "trace_id": None}


class FailingBridge:
    """Always raises from turn()."""

    name = "failing"

    def new_session(self, session_id: str = "", user_id: str = "") -> str:
        return session_id or "sess-fail"

    def turn(self, session_id, user_id, message, on_delta=None):
        raise RuntimeError("boom-secret-internal-details")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _make_sse_client(monkeypatch, bridge):
    """Build a TestClient with the given bridge + faked OTel helpers injected."""
    monkeypatch.setenv("WIZARD_MODE", "mock")
    from server.wizard import config
    config._settings = None

    from server.wizard.main import create_app
    app = create_app()

    from server.wizard.shim import hermes_bridge
    hermes_bridge.set_bridge(bridge)

    # Patch OTel helpers in the runtime_protocol namespace so the worker thread
    # resolves the fakes (module-level name lookup, not contextvar-bound).
    import server.wizard.shim.runtime_protocol as rp
    monkeypatch.setattr(rp, "start_span", _fake_start_span)
    monkeypatch.setattr(rp, "current_trace_id", _fake_trace_id)

    return TestClient(app)


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    """Parse an SSE response body into [(event_type, data_dict), ...]."""
    events: list[tuple[str, dict]] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        ev_type = None
        data_line = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                ev_type = line[len("event: "):]
            elif line.startswith("data: "):
                data_line = line[len("data: "):]
        if ev_type and data_line is not None:
            events.append((ev_type, json.loads(data_line)))
    return events


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_sse_delta_order_and_done_trace_id(monkeypatch):
    bridge = FakeBridge()
    client = _make_sse_client(monkeypatch, bridge)

    r = client.post("/run_sse", json={"session_id": "s1", "message": "hello"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(r.text)
    delta_texts = [d["text"] for t, d in events if t == "delta"]
    assert delta_texts == ["alpha-", "beta-", "gamma"], "deltas must arrive in order"

    done_events = [(t, d) for t, d in events if t == "done"]
    assert len(done_events) == 1, "exactly one done event"
    done_data = done_events[0][1]
    assert done_data["trace_id"] == FAKE_TRACE_ID, "trace_id must cross from worker thread"
    assert done_data["session_id"] == "s1"
    assert done_data["reply"] == "alpha-beta-gamma"


def test_sse_error_does_not_leak_exception(monkeypatch):
    bridge = FailingBridge()
    client = _make_sse_client(monkeypatch, bridge)

    r = client.post("/run_sse", json={"session_id": "s2", "message": "hello"})
    assert r.status_code == 200

    events = _parse_sse(r.text)
    error_events = [(t, d) for t, d in events if t == "error"]
    assert len(error_events) == 1
    assert error_events[0][1]["message"] == "stream failed"
    # The raw exception detail must NOT appear anywhere in the response.
    assert "boom-secret" not in r.text
    assert "RuntimeError" not in r.text


def test_sse_concurrent_requests_no_crosstalk(monkeypatch):
    bridge = FakeBridge()
    client = _make_sse_client(monkeypatch, bridge)

    r1 = client.post("/run_sse", json={"session_id": "sA", "message": "hi"})
    r2 = client.post("/run_sse", json={"session_id": "sB", "message": "hi"})

    ev1 = _parse_sse(r1.text)
    ev2 = _parse_sse(r2.text)

    done1 = next(d for t, d in ev1 if t == "done")
    done2 = next(d for t, d in ev2 if t == "done")

    # Each request's done event carries its own session_id.
    assert done1["session_id"] == "sA"
    assert done2["session_id"] == "sB"

    # Each bridge.turn call was routed to its own session.
    assert "sA" in bridge.calls
    assert "sB" in bridge.calls

    # Deltas from r2 must not appear in r1's body (and vice versa).
    delta_texts_1 = [d["text"] for t, d in ev1 if t == "delta"]
    assert delta_texts_1 == ["alpha-", "beta-", "gamma"]


def test_sse_keyauth_rejects_missing_header(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "mock")
    monkeypatch.setenv("RUNTIME_API_KEY", "sekret")
    from server.wizard import config
    config._settings = None
    from server.wizard.main import create_app
    client = TestClient(create_app())

    assert client.post("/run_sse", json={"message": "hi"}).status_code == 401


def test_sse_keyauth_rejects_wrong_header(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "mock")
    monkeypatch.setenv("RUNTIME_API_KEY", "sekret")
    from server.wizard import config
    config._settings = None
    from server.wizard.main import create_app
    client = TestClient(create_app())

    r = client.post("/run_sse", headers={"X-Api-Key": "wrong"}, json={"message": "hi"})
    assert r.status_code == 401


def test_sse_keyauth_accepts_correct_header(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "mock")
    monkeypatch.setenv("RUNTIME_API_KEY", "sekret")
    from server.wizard import config
    config._settings = None
    from server.wizard.main import create_app
    client = TestClient(create_app())

    r = client.post("/run_sse", headers={"X-Api-Key": "sekret"}, json={"message": "hi"})
    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert any(t == "done" for t, _ in events)


def test_sse_uses_unique_mock_session_id_when_absent(monkeypatch):
    """No explicit session_id -> MockHermesBridge generates a unique one."""
    monkeypatch.setenv("WIZARD_MODE", "mock")
    from server.wizard import config
    config._settings = None
    from server.wizard.main import create_app
    client = TestClient(create_app())

    r = client.post("/run_sse", json={"message": "step1"})
    assert r.status_code == 200
    events = _parse_sse(r.text)
    done = next(d for t, d in events if t == "done")
    assert done["session_id"].startswith("sess-mock-")
