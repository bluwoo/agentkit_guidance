#!/usr/bin/env python3
"""Re-query latest agentkit quotas (cn-beijing) and dump JSON."""
import os, json, datetime
from volcenginesdkcore import Configuration, ApiClient
from volcenginesdkquota.api.quota_api import QUOTAApi
from volcenginesdkquota.models.list_product_quotas_request import ListProductQuotasRequest

REGION = "cn-beijing"
PROVIDER = "agentkit"

config = Configuration()
config.ak = os.environ["VOLCENGINE_ACCESS_KEY"]
config.sk = os.environ["VOLCENGINE_SECRET_KEY"]
config.region = REGION
api = QUOTAApi(ApiClient(config))

# Quota codes to query (from prior evidence + report §2.7)
CODES = ["tool", "skillspace", "runtime", "mcpservice", "a2aspace", "skill"]

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")
out = {"query_time": now, "provider_code": PROVIDER, "region": REGION, "quotas": {}}

for code in CODES:
    try:
        req = ListProductQuotasRequest(provider_code=PROVIDER, quota_code=code)
        resp = api.list_product_quotas(req)
        qs = resp.quotas or []
        entries = []
        for q in qs:
            entries.append({
                "quota_code": q.quota_code,
                "total_quota": q.total_quota,
                "total_usage_value": q.total_usage.value if q.total_usage else None,
                "total_usage_unit": q.total_usage.unit if q.total_usage else None,
                "description": q.description,
                "trn": q.trn,
            })
        out["quotas"][code] = {"count": len(entries), "entries": entries}
        for e in entries:
            print(f"[OK] {code}: quota={e['total_quota']} used={e['total_usage_value']} {e['total_usage_unit']}")
    except Exception as e:
        out["quotas"][code] = {"error": f"{type(e).__name__}: {e}"}
        print(f"[ERR] {code}: {type(e).__name__}: {e}")

print("\n" + json.dumps(out, ensure_ascii=False, indent=2))
