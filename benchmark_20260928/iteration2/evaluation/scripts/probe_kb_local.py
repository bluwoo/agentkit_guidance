#!/usr/bin/env python3
"""
probe_kb_local.py — 探测真 SDK `KnowledgeBase(backend="local")` 的 search 能否离线执行。

安全约束（本探针绝不违反）：
  * 不读取、不打印任何真实密钥/环境变量值；
  * 不向真实云端端点（ark.cn-beijing.volces.com / vikingdb 等）发请求；
  * 为确定性地证明"add/search 依赖 embedding 网络调用"，我们把 embedding 的 api_base
    显式指向一个死本地端口 http://127.0.0.1:9/ ，让 embedding 调用立刻 ConnectionRefused，
    而不是打到真实云。
"""
from __future__ import annotations

import inspect
import json
import os
import platform
import sys
import traceback
from datetime import datetime, timezone

# 确保不携带任何真实模型密钥参与探测
for k in ("MODEL_EMBEDDING_API_KEY", "MODEL_AGENT_API_KEY", "VOLCENGINE_ACCESS_KEY",
          "VOLCENGINE_SECRET_KEY", "DATABASE_VIKING_API_KEY"):
    os.environ.pop(k, None)

report: dict = {"when_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version.split()[0],
                "executable": sys.executable,
                "platform": platform.platform(),
                "checks": []}


def rec(check, **kw):
    report["checks"].append({"check": check, **kw})


print("== import veadk.knowledgebase ==")
try:
    from veadk.knowledgebase import KnowledgeBase
    import veadk
    rec("import_knowledgebase", ok=True, file=KnowledgeBase.__module__)
    print("OK KnowledgeBase from", KnowledgeBase.__module__)
except Exception as e:
    rec("import_knowledgebase", ok=False, error=f"{type(e).__name__}: {e}")
    print("FAILED:", repr(e))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0)

# --- 1) 签名/支持后端 -------------------------------------------------------
print("\n== KnowledgeBase signature & supported backends ==")
try:
    sig = inspect.signature(KnowledgeBase)
    print("KnowledgeBase signature:", sig)
    rec("kb_signature", ok=True, signature=str(sig))
except Exception as e:
    rec("kb_signature", ok=False, error=repr(e))

# --- 2) 离线构造（无密钥、默认云 embedding 配置） ---------------------------
print("\n== construct KnowledgeBase(backend='local') with NO secrets ==")
kb = None
try:
    kb = KnowledgeBase(backend="local", index="probe_local", top_k=3)
    be = getattr(kb, "_backend", None)
    embed = getattr(be, "_embed_model", None) if be else None
    print("constructed OK; backend:", type(be).__name__)
    print("embed_model:", type(embed).__name__ if embed else None)
    embed_info = {}
    if embed is not None:
        for attr in ("api_base", "model_name", "model", "api_key"):
            v = getattr(embed, attr, None)
            if attr == "api_key":
                v = "<set:%s>" % bool(v) if v else "<empty>"
            embed_info[attr] = v
    print("embedder introspection (no secret printed):", embed_info)
    rec("construct_local_offline", ok=True, backend=type(be).__name__, embed_model=type(embed).__name__,
        embedder=embed_info)
except Exception as e:
    rec("construct_local_offline", ok=False, error=f"{type(e).__name__}: {e}", tb=traceback.format_exc())
    print("CONSTRUCT FAILED:", repr(e))

# --- 3) search 的真实依赖：用死本地端点确定性证明需要网络 embedding ----------
print("\n== guarded add_from_text/search attempt (dead local embed endpoint, NO real cloud) ==")
try:
    # 重新构造一个把 embedding 指向死本地地址的实例，证明 add/search 必然走 HTTP embedding
    from veadk.knowledgebase.backends.in_memory_backend import InMemoryKnowledgeBackend
    be_dead = InMemoryKnowledgeBackend(
        index="probe_dead",
        embedding_config={
            "name": "doubao-embedding-text-240715",
            "api_base": "http://127.0.0.1:9/",   # 死端口：立刻拒绝，绝不触真实云
            "api_key": "PROBE_DUMMY_NOT_A_REAL_KEY",
        },
    )
    kb2 = KnowledgeBase(backend=be_dead, index="probe_dead", top_k=3)
    add_exc = None
    try:
        kb2.add_from_text("refund within 30 days")
    except Exception as e:
        add_exc = f"{type(e).__name__}: {e}"
    search_exc = None
    if add_exc is None:
        try:
            kb2.search("refund policy")
        except Exception as e:
            search_exc = f"{type(e).__name__}: {e}"
    print("add_from_text ->", add_exc)
    print("search      ->", search_exc)
    if add_exc or search_exc:
        rec("add_search_needs_network", ok=False,
            conclusion="add_from_text/search 实际调用 embedding HTTP；离线/无可用 embedding 服务时失败。",
            add_error=add_exc, search_error=search_exc)
    else:
        rec("add_search_needs_network", ok=True,
            conclusion="在死本地端点上竟然成功——需复核。")
except Exception as e:
    rec("add_search_needs_network", ok=False, setup_error=f"{type(e).__name__}: {e}",
        tb=traceback.format_exc())
    print("SETUP FAILED:", repr(e))

# --- verdict ----------------------------------------------------------------
print("\n== VERDICT ==")
constructed = any(c.get("check") == "construct_local_offline" and c.get("ok") for c in report["checks"])
need_net = any(c.get("check") == "add_search_needs_network" and not c.get("ok") for c in report["checks"])
if constructed and need_net:
    verdict = ("CONCLUSION: KnowledgeBase(backend='local') 对象可离线构造（惰性），但 add_from_text/search "
               "依赖 Ark 云 embedding HTTP 调用；在无密钥/离线环境无法真实召回。"
               "=> 不能把它当作纯离线可执行的真 SDK 冒烟；属'构造可、检索需云'的边界。")
else:
    verdict = "结论见 checks。"
print(verdict)
report["verdict"] = verdict
print("\n== JSON ==")
print(json.dumps(report, ensure_ascii=False, indent=2))
