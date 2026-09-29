"""
离线最小集成场景 (cold start)
=============================
完全本地、离线、无云凭据。把至少三个 AgentKit 能力缝进一个可运行系统：

1. veadk 底座            : veadk.Agent 构造（继承 google.adk.agents.LlmAgent），不发起模型调用。
2. adk-workflow 编排     : google.adk.Workflow 条件路由（Event(route=...) + dict 边），纯 @node 函数节点。
3. sandbox 子进程执行    : LocalSandbox 用真子进程 (sys.executable -I) 执行代码；
                           同 session_id 复用同一工作目录 FS，跨 session_id 隔离
                           （对应 sandbox Skill §1/§8 的离线语义；不用云 TOOL_CODE_SANDBOX_URL）。
4. observability 内存追踪: InMemorySpanRecorder 内存 span 记录；单次 trace 与聚合计数分离
                           （对应 observability Skill 离线表“内存 span recorder / 单次 trace vs 聚合分离”）。
5. evaluation 离线评测   : 确定性 ExactMatch 打分（evaluation Skill 离线表的本地指标，不调 LLM judge）。

安全：模块导入即剥离火山/ARK/AK/SK/API_KEY/DATABASE/TOOL_CODE 相关环境变量；
不读 shell profile，不创建云资源。所有写入仅落在本目录。
"""

import asyncio
import os
import subprocess
import sys
import time
import uuid

# --- 强制离线：导入阶段就剥离任何可能触发云凭据读取的环境变量 ---
for _k in list(os.environ):
    if any(t in _k.upper() for t in (
        "VOLCENGINE", "ARK_", "_AK", "_SK", "SECRET", "ACCESS_KEY",
        "API_KEY", "DATABASE_", "TOOL_CODE",
    )):
        os.environ.pop(_k, None)

from google.adk import Event, Workflow  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.workflow import DEFAULT_ROUTE, node  # noqa: E402
from google.genai import types  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACES = os.path.join(_HERE, "workspaces")
os.makedirs(WORKSPACES, exist_ok=True)


# ---------------------------------------------------------------------------
# 4) observability 离线：内存 span recorder
# ---------------------------------------------------------------------------
class InMemorySpanRecorder:
    """内存 span recorder。单次 trace 只看本 trace 的 span；聚合是独立统计，不回写单次 trace。"""

    def __init__(self):
        self.spans = []

    def record(self, trace_id, node, status, detail=""):
        self.spans.append({
            "trace_id": trace_id,
            "node": node,
            "status": status,          # OK / ERROR
            "detail": detail,
            "ts": time.time(),
        })

    def for_trace(self, trace_id):
        """单次 trace：仅返回本 trace 的 span。"""
        return [s for s in self.spans if s["trace_id"] == trace_id]

    def aggregate(self):
        """聚合观测：跨所有 trace 的计数，与单次 trace 分离。"""
        return {
            "total": len(self.spans),
            "ok": sum(1 for s in self.spans if s["status"] == "OK"),
            "error": sum(1 for s in self.spans if s["status"] == "ERROR"),
        }


# ---------------------------------------------------------------------------
# 3) sandbox 离线语义：真子进程 + 同 session FS 复用 / 跨 session 隔离
# ---------------------------------------------------------------------------
class LocalSandbox:
    def __init__(self, root=WORKSPACES):
        self.root = root

    def workspace(self, session_id):
        d = os.path.join(self.root, session_id)
        os.makedirs(d, exist_ok=True)
        return d

    def exec_python(self, session_id, code, timeout=30):
        """在子进程里执行 Python 代码，cwd=该 session 的工作目录（同 session 复用）。"""
        cwd = self.workspace(session_id)
        proc = subprocess.run(
            [sys.executable, "-I", "-c", code],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return {
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "exit_code": proc.returncode,
            "cwd": cwd,
        }


# ---------------------------------------------------------------------------
# 5) evaluation 离线：确定性 ExactMatch
# ---------------------------------------------------------------------------
def exact_match(pred, expected):
    return 1.0 if str(pred).strip() == str(expected).strip() else 0.0


class OfflineAgentSystem:
    """把上述能力缝在一起的最小系统。"""

    def __init__(self):
        # --- 1) veadk 底座：仅构造，不发模型调用 ---
        from veadk import Agent as VeAgent
        self.agent = VeAgent(
            name="offline_agent",
            model_name="offline-stub",
            # 显式传本地占位 key：优先级最高，避免 model_post_init 调 get_ark_token()。
            # 这不是真实云凭据，也不触发任何网络调用（已实测）。
            model_api_key="local-offline-placeholder-not-a-secret",
            instruction="offline integration demo (no model call).",
        )

        self.sandbox = LocalSandbox()
        self.recorder = InMemorySpanRecorder()
        self._active = {}          # 本进程调用的 trace_id（单次运行内有效）
        self.ticket_wf = self._build_ticket_workflow()

    # --- 2) adk-workflow：条件路由 Graph ---
    def _build_ticket_workflow(self):
        sysref = self

        @node(name="classify")
        async def classify(ctx, node_input):
            text = str(ctx.session.state.get("text", ""))
            low = text.lower()
            route = "CALC" if ("calc" in low or "compute" in low) else "OTHER"
            sysref.recorder.record(sysref._active["trace_id"], "classify", "OK", route)
            return Event(route=route, output=text)

        @node(name="run_code")
        async def run_code(ctx, node_input):
            sid = ctx.session.state.get("session_id", "default")
            code = ctx.session.state.get("code", "print('no code')")
            res = sysref.sandbox.exec_python(sid, code)
            status = "OK" if res["exit_code"] == 0 else "ERROR"
            sysref.recorder.record(sysref._active["trace_id"], "run_code", status, res["stdout"])
            return f"RESULT stdout={res['stdout']} exit={res['exit_code']}"

        @node(name="generic")
        async def generic(ctx, node_input):
            sysref.recorder.record(sysref._active["trace_id"], "generic", "OK")
            return "GENERIC: no computation requested"

        return Workflow(
            name="offline_ticket",
            edges=[
                ("START", classify),
                (classify, {"CALC": run_code, DEFAULT_ROUTE: generic}),
            ],
        )

    async def _run_workflow(self, wf, session_id, text, code):
        self._active = {"trace_id": "tr-" + uuid.uuid4().hex[:8]}
        app_name = "offline_app"
        user_id = "offline_user"
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name=app_name, user_id=user_id,
            state={"text": text, "code": code, "session_id": session_id},
        )
        runner = Runner(app_name=app_name, agent=wf, session_service=session_service)
        content = types.Content(role="user", parts=[types.Part(text=text)])

        final_text = ""
        final_output = None
        async for ev in runner.run_async(
            user_id=user_id, session_id=session.id, new_message=content,
        ):
            if ev.content and ev.content.parts:
                for p in ev.content.parts:
                    if p.text:
                        final_text = p.text
            if getattr(ev, "output", None) is not None:
                final_output = ev.output
        # 节点返回值进 event.output；用户可见文本优先，否则回退 output
        result = final_text if final_text else (str(final_output) if final_output is not None else "")
        return {
            "text": result,
            "output": final_output,
            "trace_id": self._active["trace_id"],
        }

    def process(self, session_id, text, code=""):
        """同步封装：处理一张工单（跑条件路由 Graph，必要时子进程执行代码）。"""
        return asyncio.run(self._run_workflow(self.ticket_wf, session_id, text, code))

    def evaluate(self, cases):
        """cases: list of (prediction, expected)；返回 ExactMatch 统计。"""
        scores = [exact_match(p, e) for p, e in cases]
        return {
            "n": len(cases),
            "passed": sum(1 for s in scores if s == 1.0),
            "failed": sum(1 for s in scores if s == 0.0),
            "scores": scores,
        }


if __name__ == "__main__":
    system = OfflineAgentSystem()
    r1 = system.process("demo-sess", "please compute", "print(21*2)")
    print("CALC ->", r1["text"], "| trace", r1["trace_id"])
    r2 = system.process("demo-sess", "just a question")
    print("OTHER->", r2["text"], "| trace", r2["trace_id"])
    print("spans for last trace:", system.recorder.for_trace(r2["trace_id"]))
    print("aggregate:", system.recorder.aggregate())
    print("eval:", system.evaluate([("RESULT stdout=42", "RESULT stdout=42"), ("a", "b")]))
