"""
cold_start 离线集成测试
======================
完全本地、离线、无云凭据。覆盖至少三个 AgentKit 能力：
  - veadk 底座 (Agent 构造 + LlmAgent 继承)
  - adk-workflow (条件路由 Graph)
  - sandbox (真子进程执行 + 同 session FS 复用 / 跨 session 隔离)
  - observability (内存 span recorder：单次 trace vs 聚合分离)
  - evaluation (确定性 ExactMatch)

运行：
  <bench>/.venv/bin/python -m pytest cold_start_agent.py_test?  见 README/run_tests.sh
"""

import os

import pytest

from cold_start_agent import LocalSandbox, OfflineAgentSystem, exact_match


@pytest.fixture(scope="module")
def system():
    return OfflineAgentSystem()


# --- 1) veadk 底座：构造离线成功且继承 LlmAgent ---
def test_veadk_agent_constructs_offline(system):
    from google.adk.agents import LlmAgent
    from veadk import Agent as VeAgent
    assert isinstance(system.agent, VeAgent)
    assert issubclass(VeAgent, LlmAgent)  # veadk.Agent 继承 ADK LlmAgent（Skill 已核）
    assert system.agent.name == "offline_agent"


# --- 2) adk-workflow：CALC 路由进入子进程执行 ---
def test_workflow_calc_runs_subprocess(system):
    res = system.process("t-calc", "please compute", "print(7 * 6)")
    assert "stdout=42" in res["text"], res["text"]
    assert "exit=0" in res["text"]
    # 本 trace 只应包含 classify + run_code 两个 span
    nodes = [s["node"] for s in system.recorder.for_trace(res["trace_id"])]
    assert nodes == ["classify", "run_code"], nodes


# --- 3) adk-workflow：OTHER 路由走 generic，不跑子进程 ---
def test_workflow_other_route(system):
    res = system.process("t-other", "a general question about billing")
    assert res["text"] == "GENERIC: no computation requested", res["text"]
    nodes = [s["node"] for s in system.recorder.for_trace(res["trace_id"])]
    assert nodes == ["classify", "generic"], nodes


# --- 4) sandbox：同 session_id 复用同一工作目录 FS ---
def test_sandbox_same_session_fs_reuse(tmp_path):
    sb = LocalSandbox(root=str(tmp_path))
    sb.exec_python("sessA", "open('marker.txt','w').write('hello-fs')")
    out = sb.exec_python("sessA", "print(open('marker.txt').read())")
    assert out["stdout"] == "hello-fs"
    assert out["exit_code"] == 0


# --- 5) sandbox：跨 session_id 工作目录隔离 ---
def test_sandbox_cross_session_isolation(tmp_path):
    sb = LocalSandbox(root=str(tmp_path))
    sb.exec_python("sessA", "open('only-in-A.txt','w').write('A')")
    sb.exec_python("sessB", "print('b done')")
    # B 的工作目录不应看到 A 写的文件
    b_dir = sb.workspace("sessB")
    assert not os.path.exists(os.path.join(b_dir, "only-in-A.txt"))
    a_dir = sb.workspace("sessA")
    assert os.path.exists(os.path.join(a_dir, "only-in-A.txt"))


# --- 6) observability：单次 trace 与聚合分离 ---
def test_observability_single_trace_vs_aggregate(system):
    r1 = system.process("obs-1", "please compute", "print(1+1)")
    r2 = system.process("obs-2", "random question")
    t1 = system.recorder.for_trace(r1["trace_id"])
    t2 = system.recorder.for_trace(r2["trace_id"])
    # 单次 trace：只含本 trace 的 span，互不串
    assert all(s["trace_id"] == r1["trace_id"] for s in t1)
    assert all(s["trace_id"] == r2["trace_id"] for s in t2)
    assert set(s["node"] for s in t1) == {"classify", "run_code"}
    assert set(s["node"] for s in t2) == {"classify", "generic"}
    # 聚合：跨所有 trace 的总计数，独立于单次 trace
    agg = system.recorder.aggregate()
    assert agg["total"] >= len(system.recorder.spans)  # 即全部 span
    assert agg["error"] == 0


# --- 7) evaluation：确定性 ExactMatch ---
def test_evaluation_exact_match(system):
    assert exact_match("42", "42") == 1.0
    assert exact_match("42", "24") == 0.0
    report = system.evaluate([("stdout=42", "stdout=42"), ("a", "b"), ("  x ", "x")])
    assert report["n"] == 3
    assert report["passed"] == 2   # 精确相等 + 去空白后相等
    assert report["failed"] == 1
