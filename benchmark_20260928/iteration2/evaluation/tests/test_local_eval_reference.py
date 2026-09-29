"""本地评测 reference 的确定性测试（contract test，非官方 SDK）。"""
from __future__ import annotations
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "reference")))
import pytest
from reference_eval import (Dataset, Sample, ExactMatchEvaluator,
                            TokenOverlapEvaluator, Experiment)


def _ds():
    return Dataset([Sample(id="a", input="q1", reference_output="hello"),
                    Sample(id="b", input="q2", reference_output="world")])


def test_dataset_rejects_empty_and_dup_ids():
    with pytest.raises(ValueError):
        Dataset([])
    with pytest.raises(ValueError):
        Dataset([Sample(id="x", input="q", reference_output="e"),
                 Sample(id="x", input="q", reference_output="e")])


def test_exact_match_deterministic():
    ev = ExactMatchEvaluator()
    s = Sample(id="", input="q", reference_output="hello")
    assert ev(sample=s, actual_output="hello")["score"] == 1.0
    assert ev(sample=s, actual_output=" hello ")["score"] == 1.0   # strip
    assert ev(sample=s, actual_output="nope")["score"] == 0.0


def test_token_overlap_in_range():
    ev = TokenOverlapEvaluator()
    s = Sample(id="", input="q", reference_output="refund within 30 days")
    r = ev(sample=s, actual_output="refund within 30 days please")
    assert 0.0 <= r["score"] <= 1.0
    assert r["score"] == 1.0  # ref 词全命中


def test_experiment_aggregates():
    exp = Experiment(name="t", dataset=_ds(), evaluators=[ExactMatchEvaluator()],
                     run_fn=lambda q: {"q1": "hello", "q2": "WRONG"}[q])
    rep = exp.run()
    assert rep["n_samples"] == 2
    assert rep["aggregate"]["per_evaluator_mean"]["exact_match"] == 0.5
    assert rep["aggregate"]["overall_mean"] == 0.5
    assert rep["is_official_sdk"] is False


def test_experiment_requires_evaluator():
    with pytest.raises(ValueError):
        Experiment(name="x", dataset=_ds(), evaluators=[], run_fn=lambda q: q)
