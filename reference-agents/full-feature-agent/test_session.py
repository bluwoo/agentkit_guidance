"""test_session.py — 验证 full-feature-agent 的持久化会话隔离与 header 校验。

测试用例：
1. 同 user + 同 session：第二轮能回忆第一轮写入的内容
2. 同 user + 新 session：不共享短期上下文
3. 异 user 隔离：userA 写入，userB 同 session_id 读不到
4. 缺 user_id header → 400
5. 缺 session_id header → 400

运行方式：
  python test_session.py   # 建议使用项目钉版 venv 的 python 解释器
"""
import asyncio
import os
import sys
import tempfile

# ========== 测试环境配置（必须在 import agent 之前设置） ==========
_tmpdir = tempfile.mkdtemp(prefix="agentkit_session_test_")
_test_db = os.path.join(_tmpdir, "sessions.db")
# 4 slashes = absolute path: sqlite+aiosqlite:////abs/path
os.environ["SESSION_DB_URL"] = f"sqlite+aiosqlite:///{_test_db}"
# 避免 skills / 云配置干扰
os.environ.pop("SKILL_SPACE_ID", None)
os.environ.pop("ENABLE_MEMORY", None)
os.environ.pop("ENABLE_KB", None)
os.environ.pop("TOOL_LLM_SHIELD_APP_ID", None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ========== 导入 agent 模块 ==========
import agent as agent_module  # noqa: E402

from veadk.memory.short_term_memory import DatabaseSessionService  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402

# ========== 验证持久化 backend ==========
_svc = agent_module.runner.short_term_memory.session_service
assert isinstance(_svc, DatabaseSessionService), (
    f"FAIL: session_service is {type(_svc).__name__}, expected DatabaseSessionService"
)
print(f"[SETUP] session_service = {type(_svc).__name__}, db = {_test_db}")


# ========== Monkeypatch runner.run：避免真实 LLM 调用，
# 但通过真实 DatabaseSessionService.append_event 持久化事件，
# 从而验证持久化 backend 的会话隔离与跨请求保留。 ==========
from google.adk.events import Event as _TestEvent  # noqa: E402
from google.genai import types as _TestTypes  # noqa: E402


async def _fake_run(messages, user_id, session_id, **kwargs):
    stm = agent_module.runner.short_term_memory
    ss = stm.session_service
    app_name = agent_module.runner.app_name

    session = await ss.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await ss.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    prompt = str(messages)

    # 把用户消息作为 Event 追加并持久化到 DB
    user_event = _TestEvent(
        invocation_id="test-inv",
        author="user",
        content=_TestTypes.Content(role="user", parts=[_TestTypes.Part(text=prompt)]),
    )
    await ss.append_event(session, user_event)

    # 回忆问题 → 从 session.events 搜索之前的"记住XXX"消息
    if "我刚才说记住什么" in prompt:
        for ev in session.events:
            if ev.content and ev.content.parts:
                for part in ev.content.parts:
                    if part.text and "记住" in part.text and "我刚才说" not in part.text:
                        return f"你刚才说过：{part.text}"
        return "我不记得你让我记住过什么。"

    return "好的"


agent_module.runner.run = _fake_run

# ========== 用 Starlette TestClient 发请求 ==========
from starlette.testclient import TestClient  # noqa: E402

client = TestClient(agent_module.app)

PASS = 0
FAIL = 0


def _check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


# ========== Test 1: 同 user + 同 session 第二轮回忆 ==========
print("\n=== Test 1: 同 user + 同 session 第二轮回忆 ===")
r1 = client.post(
    "/invoke",
    json={"prompt": "记住我最喜欢的颜色是蓝色"},
    headers={"user_id": "alice", "session_id": "sess-1"},
)
print(f"  round1 status={r1.status_code}, body={r1.text[:120]}")

r2 = client.post(
    "/invoke",
    json={"prompt": "我刚才说记住什么"},
    headers={"user_id": "alice", "session_id": "sess-1"},
)
print(f"  round2 status={r2.status_code}, body={r2.text[:200]}")
_check(
    "同session第二轮能回忆蓝色偏好",
    r2.status_code == 200 and "蓝色" in r2.text,
    f"got: {r2.text[:200]}",
)


# ========== Test 2: 同 user 新 session 不混上下文 ==========
print("\n=== Test 2: 同 user 新 session 不混短期上下文 ===")
r3 = client.post(
    "/invoke",
    json={"prompt": "我刚才说记住什么"},
    headers={"user_id": "alice", "session_id": "sess-2"},  # 新 session
)
print(f"  status={r3.status_code}, body={r3.text[:200]}")
_check(
    "新session读不到sess-1的内容",
    r3.status_code == 200 and "蓝色" not in r3.text,
    f"leaked color pref into new session! body={r3.text[:200]}",
)


# ========== Test 3: 异 user 隔离 ==========
print("\n=== Test 3: 异 user 隔离 ===")
r4 = client.post(
    "/invoke",
    json={"prompt": "我刚才说记住什么"},
    headers={"user_id": "bob", "session_id": "sess-1"},  # 同 session_id 但不同 user
)
print(f"  status={r4.status_code}, body={r4.text[:200]}")
_check(
    "异user同session_id读不到alice的内容",
    r4.status_code == 200 and "蓝色" not in r4.text,
    f"leaked alice data to bob! body={r4.text[:200]}",
)


# ========== Test 4: 缺 user_id header → 400 ==========
print("\n=== Test 4: 缺 user_id header → 400 ===")
r5 = client.post(
    "/invoke",
    json={"prompt": "hello"},
    headers={"session_id": "sess-x"},  # 无 user_id
)
print(f"  status={r5.status_code}, body={r5.text[:200]}")
_check(
    "缺user_id返回400",
    r5.status_code == 400,
    f"expected 400, got {r5.status_code}: {r5.text[:200]}",
)


# ========== Test 5: 缺 session_id header → 400 ==========
print("\n=== Test 5: 缺 session_id header → 400 ===")
r6 = client.post(
    "/invoke",
    json={"prompt": "hello"},
    headers={"user_id": "alice"},  # 无 session_id
)
print(f"  status={r6.status_code}, body={r6.text[:200]}")
_check(
    "缺session_id返回400",
    r6.status_code == 400,
    f"expected 400, got {r6.status_code}: {r6.text[:200]}",
)


# ========== 汇总 ==========
print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL}")
if FAIL > 0:
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
