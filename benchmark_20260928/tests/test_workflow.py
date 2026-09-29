"""Real google.adk==2.2.0 orchestration (no model, no cloud)."""
import asyncio

from harness import c04_workflow as wf


def run(coro):
    return asyncio.run(coro)


def test_routing_graph_bug():
    out = run(wf.run_workflow(wf.routing_graph, "I found a bug in login"))
    assert "[BUG HANDLER]" in out


def test_routing_graph_support():
    out = run(wf.run_workflow(wf.routing_graph, "I need help with setup"))
    assert "[SUPPORT HANDLER]" in out


def test_routing_graph_other_default():
    out = run(wf.run_workflow(wf.routing_graph, "just a general question"))
    assert "[OTHER HANDLER]" in out


def test_fanout_join():
    out = run(wf.run_workflow(wf.fanout_graph, "hello"))
    assert out.startswith("MERGED[") and "A:HELLO" in out and "B:5" in out


def test_dynamic():
    out = run(wf.run_workflow(wf.dynamic_graph, "World"))
    assert out == "[FORMATTED] Hello World [/FORMATTED]"
