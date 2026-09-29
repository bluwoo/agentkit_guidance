# AgentKit Wizard — Observability Layer

后端 Step4「测试验证 + 观测 trace 取数」与自进化闭环的纯 Python 模块。
全部逻辑基于 fixture 测试，不打真实云。

## 模块结构

```
server/wizard/observability/
  apmplus_client.py    # APMPlus 查询客户端（GetTraceDetail / ListSpan / ListSession）
  mapper.py            # 核心：raw spans + Topology → TraceOverlay
  service.py           # 高层服务：get_trace_overlay / get_aggregate_panel / get_logs

server/wizard/security/
  scan.py              # 安全扫描：prompt injection / 凭证泄漏 / 后门

server/wizard/evolution/
  proposals.py         # 提案队列 + 状态机 + 回归钩子
```

## 环境变量

| 变量 | 用途 |
|---|---|
| `APMPLUS_ACCESS_KEY`  | 火山引擎 AK（V4 HMAC-SHA256 签名） |
| `APMPLUS_SECRET_KEY`  | 火山引擎 SK |

未配置时客户端不抛异常，返回 `TraceStatus.not_configured`。
**AK/SK 绝不写入代码、日志或错误体。**

## 公开 API（后端 import 清单）

### apmplus_client.py
```python
from server.wizard.observability.apmplus_client import APMPlusClient, APMPlusResponse

client = APMPlusClient(transport=None, ak=None, sk=None, timeout=10.0)
client.is_configured()                                    # -> bool
client.get_trace_detail(trace_id: str, suggest_time=0)     # -> APMPlusResponse
client.list_span(start_time, end_time, filters=None, limit=100)  # -> APMPlusResponse
client.list_session(start_time_ms, end_time_ms, page_size=50)    # -> APMPlusResponse
```

### mapper.py（铁律核心）
```python
from server.wizard.observability.mapper import (
    build_trace_overlay,   # (trace_id, raw_spans, topology, status, error, logs) -> TraceOverlay
    aggregate_metrics,     # (spans, time_window, window_seconds) -> AggregateMetricsPanel
    normalize_span,        # (raw_span_dict) -> ObservedSpan
    is_span_error,         # (raw_span_dict) -> bool
)
```

### service.py
```python
from server.wizard.observability.service import (
    get_trace_overlay,       # (runtime_id, trace_id, design_topology, client=None, ...) -> TraceOverlay
    get_aggregate_panel,     # (runtime_id, time_window, service=None, client=None) -> AggregateMetricsPanel
    get_logs,                # (runtime_id, trace_id, service, raw_logs) -> list[LogLine]
)
```

### security/scan.py
```python
from server.wizard.security.scan import scan_proposal, scan_proposal_text

scan_proposal(diff="...", rationale="...")  # -> {"passed": bool, "hits": [...]}
```

### evolution/proposals.py
```python
from server.wizard.evolution.proposals import (
    ProposalEngine, ProposalStore, RegressionRunner, StubRegressionRunner
)

engine = ProposalEngine(store=ProposalStore("./wizard_data/proposals.json"),
                        regression_runner=StubRegressionRunner())
engine.register_proposal(kind, target, diff, rationale, locked_eval_ids=None)  # -> Proposal
engine.list_proposals()            # -> list[Proposal]
engine.scan_proposal(id)           # draft -> scanned/rejected
engine.mark_pending(id)            # scanned -> pending
engine.approve(id)                 # pending -> approved (idempotent)
engine.reject(id, reason="")       # any -> rejected (idempotent)
engine.mark_staged(id)             # approved -> staged
engine.mark_regressing(id)         # staged -> regressing -> live/rejected
engine.mark_live(id)               # regressing -> live (idempotent)
engine.reject_regression(id, reason="")  # regressing -> rejected
```

## 状态机

```
draft → scanned → pending → approved → staged → regressing → live
           ↘ rejected (terminal, archived)
      pending → rejected
      regressing → rejected
```

## 如何被后端 import

FastAPI shim 在路由层直接 import：
```python
from server.wizard.observability.service import get_trace_overlay
from server.wizard.observability.apmplus_client import APMPlusClient

@app.get("/api/wizard/observability/trace")
async def trace(runtime_id: str, trace_id: str, topology: Topology):
    return get_trace_overlay(runtime_id, trace_id, topology, client=APMPlusClient())
```

## 铁律

1. 单次 trace 的 duration = `DurationMicroseconds / 1000`，**不是** Histogram P50/P95
2. 单次 trace 的错误 = `Status=ERROR` 或 `ErrorInfoList` 非空，**不是** error_type 聚合计数
3. 调用次数 = 单次 trace 内 span 出现次数（含重试），**不是** `_count` Counter
4. P50/P95/QPS 只出现在 `AggregateMetricsPanel`，**绝不**回写到 TraceOverlay
5. 映射不上的 span → `observed_unmapped`，**不硬塞、不丢弃**
