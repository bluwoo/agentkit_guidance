"""test_a2a.py — 验证正式 veadk.a2a.ve_a2a_server.init_app() 暴露标准端点。

测试用例：
1. GET /.well-known/agent-card.json → 200 + 标准 AgentCard 字段
2. POST / JSON-RPC message/send → 200 + {jsonrpc:"2.0", id, result|error}

运行方式：
  python test_a2a.py   # 建议使用项目钉版 venv 的 python 解释器
"""
import os
import sys

os.environ.setdefault("A2A_SERVER_URL", "http://localhost:8000")
os.environ.pop("ENABLE_MEMORY", None)
os.environ.pop("ENABLE_KB", None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from starlette.testclient import TestClient  # noqa: E402
import server as srv  # noqa: E402

client = TestClient(srv.app)

PASS = 0
FAIL = 0


def _check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


# === Test 1: agent-card ===
print("=== Test 1: GET /.well-known/agent-card.json ===")
r = client.get("/.well-known/agent-card.json")
print(f"  status={r.status_code}")
card = r.json() if r.status_code == 200 else {}
print(f"  name={card.get('name')}, version={card.get('version')}, "
      f"protocolVersion={card.get('protocolVersion')}")
_check("agent-card 200", r.status_code == 200, f"got {r.status_code}")
_check("agent-card has name", "name" in card)
_check("agent-card has version", "version" in card)
_check("agent-card has protocolVersion", "protocolVersion" in card)
_check("agent-card has skills", "skills" in card and len(card["skills"]) > 0)

# === Test 2: JSON-RPC message/send ===
print("\n=== Test 2: POST / message/send ===")
rpc = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": "hello"}],
            "messageId": "test-msg-1",
            "sessionId": "test-sess-1",
        }
    },
}
r2 = client.post("/", json=rpc)
print(f"  status={r2.status_code}")
resp = r2.json() if r2.headers.get("content-type", "").startswith("application/json") else {}
print(f"  jsonrpc={resp.get('jsonrpc')}, id={resp.get('id')}, "
      f"has result={'result' in resp}, has error={'error' in resp}")
_check("message/send 200", r2.status_code == 200, f"got {r2.status_code}")
_check("JSON-RPC 2.0 envelope", resp.get("jsonrpc") == "2.0", f"got {resp.get('jsonrpc')}")
_check("id matches", resp.get("id") == 1)
_check("has result or error", "result" in resp or "error" in resp)

print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL}")
if FAIL:
    sys.exit(1)
print("ALL A2A TESTS PASSED")
