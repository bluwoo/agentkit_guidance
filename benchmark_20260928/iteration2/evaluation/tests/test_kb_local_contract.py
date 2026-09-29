"""
test_kb_local_contract.py — KnowledgeBase(backend="local") 离线能力契约测试。

这些测试**不发任何真实云请求、不读真实密钥**。它们把探针结论固化为可重复断言：
  * 真 SDK 已安装（veadk.knowledgebase.KnowledgeBase 可导入）；
  * 'local' 是受支持后端（构造器签名 Literal 中）；
  * 但本地离线、无凭证时，默认 local 后端在构造期就因缺 Ark 凭证失败；
  * add/search 走 embedding HTTP（用死本地端点确定性复现，不触真实云）。
证据见 ../evidence/kb_local_probe.txt。
"""
from __future__ import annotations
import os, sys
import pytest

# 确保不携带任何真实密钥参与测试
for _k in ("MODEL_EMBEDDING_API_KEY", "MODEL_AGENT_API_KEY", "VOLCENGINE_ACCESS_KEY",
           "VOLCENGINE_SECRET_KEY", "DATABASE_VIKING_API_KEY"):
    os.environ.pop(_k, None)


def test_kb_real_sdk_importable():
    from veadk.knowledgebase import KnowledgeBase
    assert KnowledgeBase is not None


def test_local_is_supported_backend_in_signature():
    import inspect
    from veadk.knowledgebase import KnowledgeBase
    sig = inspect.signature(KnowledgeBase)
    backend_param = sig.parameters["backend"]
    assert "local" in str(backend_param.annotation)


def test_default_local_construction_needs_credentials_offline():
    """无凭证、离线：默认 local 后端在构造期即因缺 Ark 凭证失败（不触网）。"""
    from veadk.knowledgebase import KnowledgeBase
    with pytest.raises(Exception) as ei:
        KnowledgeBase(backend="local", index="contract_probe", top_k=3)
    # 文档化：失败发生在取 Ark token / AK-SK 阶段
    msg = str(ei.value).lower()
    assert ("access key" in msg or "secret key" in msg or "ark" in msg or "iam" in msg
            or "credential" in msg), f"unexpected error: {ei.value!r}"


def test_add_search_requires_embedding_http_offline():
    """注入显式死本地 embedding 端点：add_from_text 必然因连不上 embedding 服务而失败。
    用 127.0.0.1:9 死端口，绝不触真实云。"""
    from veadk.knowledgebase import KnowledgeBase
    from veadk.knowledgebase.backends.in_memory_backend import InMemoryKnowledgeBackend
    be = InMemoryKnowledgeBackend(
        index="contract_dead",
        embedding_config={"name": "doubao-embedding-text-240715",
                          "api_base": "http://127.0.0.1:9/",
                          "api_key": "CONTRACT_DUMMY_NOT_A_REAL_KEY"},
    )
    kb = KnowledgeBase(backend=be, index="contract_dead", top_k=3)
    with pytest.raises(Exception):
        kb.add_from_text("refund within 30 days")
