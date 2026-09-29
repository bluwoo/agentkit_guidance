#!/usr/bin/env python3
"""run_local_eval.py — 本地评测 reference 端到端跑通（离线、确定性）。"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "reference")))
from reference_eval import (Dataset, Sample, ExactMatchEvaluator,
                            TokenOverlapEvaluator, Experiment)


def dummy_run(q: str) -> str:
    table = {
        "refund?": "refund within 30 days",
        "ship?": "dispatch within 2 days",
        "kb?": "see employee handbook",
    }
    return table.get(q, "unknown")


def main() -> int:
    ds = Dataset([
        Sample(id="s1", input="refund?", reference_output="refund within 30 days"),
        Sample(id="s2", input="ship?", reference_output="2 days"),
        Sample(id="s3", input="kb?", reference_output="nine steps"),  # 故意错，验证 0 分
    ])
    rep = Experiment(name="iter2-local", dataset=ds,
                     evaluators=[ExactMatchEvaluator(), TokenOverlapEvaluator()],
                     run_fn=dummy_run).run()
    out = os.path.abspath(os.path.join(HERE, "..", "evidence", "local_eval_report.json"))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print("\n[written]", out)
    assert rep["is_official_sdk"] is False
    assert rep["n_samples"] == 3
    print("[ok] local reference eval ran end-to-end.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
