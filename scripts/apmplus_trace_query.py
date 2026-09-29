import os, sys, time, json
from volcenginesdkcore import Configuration, ApiClient
import volcenginesdkapmplusserver as a

ak = os.environ.get("VOLCENGINE_ACCESS_KEY")
sk = os.environ.get("VOLCENGINE_SECRET_KEY")
region = os.environ.get("VOLCENGINE_REGION", "cn-beijing")

trace_id = sys.argv[1]
# suggest_time: unix seconds, ~now (trace happened within last few min)
suggest_time = int(time.time())

cfg = Configuration()
cfg.ak = ak
cfg.sk = sk
cfg.region = region
# apmplus server endpoint
cfg.host = "open.volcengineapi.com"
api = a.APMPLUSSERVERApi(ApiClient(cfg))

req = a.GetTraceDetailRequest(suggest_time=suggest_time, trace_id=trace_id)
try:
    resp = api.get_trace_detail(req)
except Exception as e:
    print("API_ERROR:", repr(e)[:800])
    sys.exit(2)

d = resp.to_dict()
open("/tmp/dbw_trace_resp.json","w").write(json.dumps(d, ensure_ascii=False, indent=2))
spans = d.get("span_list") or d.get("SpanList") or []
print("=== trace_id:", trace_id, "===")
print("top keys:", list(d.keys()))
print("span count:", len(spans) if isinstance(spans,list) else "n/a")
def walk(span, depth=0):
    name = span.get("span_name") or span.get("spanName") or span.get("operation_name") or span.get("operationName") or "?"
    svc = span.get("service_name") or span.get("serviceName") or ""
    print("  "*depth + f"- {name}  [{svc}]")
    for c in (span.get("child_spans") or span.get("childSpans") or []):
        walk(c, depth+1)
if isinstance(spans, list):
    for s in spans:
        walk(s)
else:
    print(json.dumps(d, ensure_ascii=False)[:1500])
