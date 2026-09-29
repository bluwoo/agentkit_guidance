"""memory (3-layer local), knowledge retrieval, observability recorder, evaluation."""
import asyncio

from harness.c06_memory import LocalThreeLayerMemory
from harness.c12_knowledge import LocalKnowledgeBase
from harness.c13_observability import TraceRecorder
from harness.c14_evaluation import Dataset, Sample, Experiment


def test_memory_three_layer_persists():
    m = LocalThreeLayerMemory.build()
    m.append_session("u", "s1", "my preference is concise answers")
    asyncio.run(m.save_session_to_long_term_memory("s1", "u"))
    assert "my preference is concise answers" in m.recall("u")
    # real veadk LTM(backend=local) was constructed
    assert m.real_ltm is not None


def test_knowledge_retrieves():
    kb = LocalKnowledgeBase.build()
    kb.add_document("refund", "refund within 30 days")
    kb.add_document("shipping", "dispatch within 2 days")
    hits = kb.retrieve("what is the refund policy")
    assert hits and hits[0]["id"] == "refund"


def test_observability_single_trace_vs_aggregate():
    t = TraceRecorder()
    tid = t.new_trace()
    t.record("invoke_agent", tid, {"gen_ai.operation.name": "invoke_agent"}, duration_ms=30)
    t.record("call_llm", tid, {"gen_ai.operation.name": "chat", "gen_ai.span.kind": "llm"},
             duration_ms=20, status="OK")
    summ = t.trace_summary(tid)
    assert summ["span_count"] == 2
    assert summ["total_duration_ms"] == 50          # span start->end diff, not percentile
    agg = t.aggregate_window()
    assert agg["spans"] == 2 and agg["p95_ms"] >= 20


def test_evaluation_experiment():
    ds = Dataset(name="smoke", samples=[
        Sample(input="refund?", reference_output="30 days", actual_output="30 days"),
        Sample(input="ship?", reference_output="2 days", actual_output="never"),
    ])
    exp = Experiment(name="v1", dataset=ds).run()
    assert exp["mean_scores"]["exact_match"] == 0.5
    assert 0.0 <= exp["mean_scores"]["llm_judge_stub"] <= 1.0
