"""agentkit-sdk contract + runtime descriptor."""
import asyncio

import pytest

from harness.c02_sdk_app import AgentkitSimpleApp, HTTPError
from harness.contract import InvokeRequest
from harness.c03_runtime import RuntimeDescriptor, RUNTIME_APIS, REGION


def test_ping_returns_pong():
    app = AgentkitSimpleApp()
    assert app.ping_now() == "pong!"


def test_missing_user_id_session_id_rejected_400():
    app = AgentkitSimpleApp()

    @app.entrypoint
    async def run(payload, headers):
        return "should not reach"

    with pytest.raises(HTTPError) as ei:
        asyncio.run(app.invoke(InvokeRequest(prompt="hi", user_id=None, session_id="s")))
    assert ei.value.status == 400


def test_entrypoint_invoked_with_identity():
    app = AgentkitSimpleApp()

    @app.entrypoint
    async def run(payload, headers):
        assert headers["user_id"] == "u1" and headers["session_id"] == "s1"
        return "ok"

    res = asyncio.run(app.invoke(InvokeRequest(prompt="hi", user_id="u1", session_id="s1")))
    assert res.text == "ok"


def test_runtime_descriptor_and_apis():
    d = RuntimeDescriptor(name="r", image="img:1")
    assert d.region == REGION == "cn-beijing"
    assert "CreateRuntime" in RUNTIME_APIS and "InvokeTool" not in RUNTIME_APIS
    assert "/invoke" in d.invoke_curl()
