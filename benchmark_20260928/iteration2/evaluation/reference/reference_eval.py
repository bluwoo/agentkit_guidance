"""
reference_eval.py — 本地评测 reference / contract test（纯标准库、确定性、离线）。

【定位说明】
钉版 venv 里**确实装了官方 eval SDK**：
  - google.adk.evaluation（AgentEvaluator / EvalSet / EvalMetrics / PrebuiltMetrics ...）
  - veadk.evaluation（EvalSetRecorder / BaseEvaluator / adk_evaluator / deepeval_evaluator ...）
但它们的指标全部是 **LLM/Vertex/Ark 后台**（LlmAsAJudge、PrebuiltMetrics 全是 response_match /
rubric / hallucination / tool_trajectory / user_simulator；BaseEvaluator.generate_outputs 要跑 agent）。
在不联网、不持密钥的本地环境里**不可执行**。证据见 ../evidence/eval_sdk_probe.txt。

因此本模块是 **项目本地 reference implementation / contract test**，不是官方 SDK：
用纯标准库钉住"Dataset -> 确定性 Evaluator -> Experiment 汇总"的最小可执行形状，
作为日后把被测对象接到官方 AgentEvaluator 时的对照。报告里 is_official_sdk=False。

云端边界（本模块绝不触碰）：
  - google.adk.evaluation.AgentEvaluator（Vertex/AIplatform）；
  - veadk.evaluation 的 LLM-as-Judge / deepeval_evaluator；
  - EvalSetRecorder 上报、TEA / default project / 任意 project_name 的结果回流。
"""
from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class Sample:
    input: str
    reference_output: str
    id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class Dataset:
    """评测集 = 输入 + 预期输出。样本 id 唯一、非空。"""

    def __init__(self, samples: Sequence[Sample]) -> None:
        if not samples:
            raise ValueError("Dataset 不能为空。")
        ids = [s.id for s in samples]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Sample.id 必须唯一，重复：{ids}")
        self._samples = list(samples)

    def __len__(self) -> int:
        return len(self._samples)

    def __iter__(self):
        return iter(self._samples)

    def __getitem__(self, i: int) -> Sample:
        return self._samples[i]

    @classmethod
    def from_jsonl(cls, path: str) -> "Dataset":
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                o = json.loads(line)
                out.append(Sample(id=str(o.get("id", n)), input=o["input"],
                                   reference_output=o["reference_output"],
                                   metadata=o.get("metadata", {})))
        return cls(out)


class Evaluator:
    name = "base"

    def score_one(self, *, sample: Sample, actual_output: str) -> dict[str, Any]:
        raise NotImplementedError

    def __call__(self, *, sample: Sample, actual_output: str) -> dict[str, Any]:
        r = self.score_one(sample=sample, actual_output=actual_output)
        if not (0.0 <= float(r["score"]) <= 1.0):
            raise ValueError(f"{self.name}: score 必须在 [0,1]，实际 {r['score']}")
        r["evaluator"] = self.name
        return r


class ExactMatchEvaluator(Evaluator):
    """确定性代码评估器：去空白后完全相等 -> 1.0 否则 0.0。"""
    name = "exact_match"

    def score_one(self, *, sample: Sample, actual_output: str) -> dict[str, Any]:
        ok = actual_output.strip() == sample.reference_output.strip()
        return {"score": 1.0 if ok else 0.0, "reason": "equal" if ok else "mismatch"}


class TokenOverlapEvaluator(Evaluator):
    """确定性'伪 LLM-judge'：参考词被命中的比例 ∈ [0,1]。离线、可重复。"""
    name = "token_overlap_stub"

    def score_one(self, *, sample: Sample, actual_output: str) -> dict[str, Any]:
        import re
        ref = set(re.findall(r"\w+", sample.reference_output.lower()))
        act = set(re.findall(r"\w+", actual_output.lower()))
        score = round(len(ref & act) / len(ref), 3) if ref else 0.0
        return {"score": score, "reason": "token_overlap"}


class Experiment:
    """对 Dataset 跑 run_fn（被测逻辑），用 evaluators 打分并汇总。"""

    def __init__(self, *, name: str, dataset: Dataset,
                 evaluators: Sequence[Evaluator], run_fn: Callable[[str], str]) -> None:
        if not evaluators:
            raise ValueError("Experiment 至少需要 1 个 evaluator。")
        self.name = name
        self.dataset = dataset
        self.evaluators = list(evaluators)
        self.run_fn = run_fn

    def run(self) -> dict[str, Any]:
        t0 = time.perf_counter()
        rows = []
        for s in self.dataset:
            actual = self.run_fn(s.input)
            scores = {}
            for ev in self.evaluators:
                r = ev(sample=s, actual_output=actual)
                scores[ev.name] = r["score"]
            rows.append({"id": s.id, "input": s.input, "expected": s.reference_output,
                         "actual": actual, "scores": scores,
                         "mean": round(statistics.fmean(scores.values()), 4)})
        elapsed = time.perf_counter() - t0
        per = {}
        for ev in self.evaluators:
            per[ev.name] = round(statistics.fmean(r["scores"][ev.name] for r in rows), 4)
        overall = round(statistics.fmean(r["mean"] for r in rows), 4)
        return {
            "experiment": self.name,
            "is_official_sdk": False,
            "note": "本地 reference/contract test；官方 google.adk/veadk eval 为云/LLM 后台，未调用。",
            "n_samples": len(rows),
            "elapsed_sec": round(elapsed, 6),
            "aggregate": {"overall_mean": overall, "per_evaluator_mean": per,
                          "pass_count_mean_ge_0_5": sum(1 for r in rows if r["mean"] >= 0.5)},
            "rows": rows,
        }
