"""Component: **agentkit-evaluation** (dataset / evaluator / experiment).

Per the Skill:
  * Three-piece set: Dataset (input/reference_output/actual_output), Evaluator
    (built-in + LLM-as-Judge in 0.0..1.0 + code evaluators), Experiment (A/B across versions).
  * Online eval requires observability on; online eval object currently = A2A-registered agents.
  * Trace flows from observability into the dataset.

We run a local experiment: an exact-match evaluator (code evaluator) + a deterministic
"LLM-as-Judge" stub (keyword overlap score), scoring samples and reporting a mean. Real
platform eval jobs are a CloudBoundary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Sample:
    input: str
    reference_output: str
    actual_output: str = ""


@dataclass
class Dataset:
    name: str
    samples: list[Sample] = field(default_factory=list)


def exact_match(sample: Sample) -> float:
    return 1.0 if sample.actual_output.strip() == sample.reference_output.strip() else 0.0


def llm_judge_stub(sample: Sample) -> float:
    """Deterministic stand-in for LLM-as-Judge: token overlap ratio in [0,1]."""
    ref = set(re.findall(r"\w+", sample.reference_output.lower()))
    act = set(re.findall(r"\w+", sample.actual_output.lower()))
    if not ref:
        return 0.0
    return round(len(ref & act) / len(ref), 3)


@dataclass
class Experiment:
    name: str
    dataset: Dataset
    evaluators: list = field(default_factory=lambda: [exact_match, llm_judge_stub])

    def run(self) -> dict:
        rows = []
        for s in self.dataset.samples:
            scores = {fn.__name__: fn(s) for fn in self.evaluators}
            rows.append({"input": s.input, **scores})
        agg = {}
        for fn in self.evaluators:
            vals = [r[fn.__name__] for r in rows]
            agg[fn.__name__] = round(sum(vals) / len(vals), 3) if vals else 0.0
        return {"experiment": self.name, "rows": rows, "mean_scores": agg}
