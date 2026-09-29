"""
ADK 2.2.0 编排原语离线验证示例
================================
全部使用 FunctionNode / 纯函数节点代替 LLM 节点，无需真实模型即可跑通编排逻辑。
验证环境: python3 (Python 3.13.7, google-adk==2.2.0)

验证覆盖:
  1. Graph 顺序编排 (FunctionNode chain)
  2. Graph 条件路由 (Event(route=...) + dict 映射)
  3. Graph 并行扇出 + JoinNode 汇合
  4. Graph 循环 (back-edge)
  5. Dynamic workflow (@node + ctx.run_node)
  6. Template SequentialAgent
  7. Template ParallelAgent
  8. Template LoopAgent (escalate 退出)
"""

# DEFAULT_ROUTE 用作未匹配值的兜底；测试覆盖 BUG、SUPPORT 和 OTHER。
# 每次运行新建内存 session，Template 状态必须通过 create_session(state=...) 初始化。
# Template 类在当前固定版本发出弃用警告，仅为存量编排学习保留。

import asyncio
import inspect
import sys
import warnings
from importlib.metadata import version as package_version
from typing import Any

# ============================================================
# 公共导入 (已离线核实存在于 google-adk 2.2.0)
# ============================================================
from google.adk import Workflow, Event, Context
from google.adk.workflow import node, FunctionNode, JoinNode, START, DEFAULT_ROUTE
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent, BaseAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.events import EventActions


# ============================================================
# 示例 1: Graph 顺序编排
# ============================================================
@node(name="gen_city")
def gen_city(node_input: Any):
    """模拟: 生成城市名"""
    return "Shanghai"

@node(name="lookup_time")
def lookup_time(node_input: str):
    """模拟: 查找城市时间"""
    return f"10:10 AM in {node_input}"

@node(name="report")
def report(node_input: str):
    """模拟: 生成报告"""
    return f"Report: {node_input}"

graph_sequential = Workflow(
    name="graph_sequential",
    edges=[("START", gen_city, lookup_time, report)],
)


# ============================================================
# 示例 2: Graph 条件路由
# ============================================================
@node(name="classify")
def classify(node_input: str):
    """根据输入分类: 含 'bug' -> BUG, 含 'help' -> SUPPORT, 否则 -> OTHER"""
    text = node_input.lower()
    if "bug" in text:
        return Event(route="BUG", output=node_input)
    elif "help" in text:
        return Event(route="SUPPORT", output=node_input)
    return Event(route="OTHER", output=node_input)

@node(name="handle_bug")
def handle_bug(node_input: str):
    return f"[BUG HANDLER] processing: {node_input}"

@node(name="handle_support")
def handle_support(node_input: str):
    return f"[SUPPORT HANDLER] processing: {node_input}"

@node(name="handle_other")
def handle_other(node_input: str):
    return f"[OTHER HANDLER] processing: {node_input}"

graph_routing = Workflow(
    name="graph_routing",
    edges=[
        ("START", classify),
        (classify, {
            "BUG": handle_bug,
            "SUPPORT": handle_support,
            DEFAULT_ROUTE: handle_other,
        }),
    ],
)


# ============================================================
# 示例 3: Graph 并行扇出 + JoinNode
# ============================================================
@node(name="task_a")
def task_a(node_input: str):
    return f"A:{node_input.upper()}"

@node(name="task_b")
def task_b(node_input: str):
    return f"B:{len(node_input)}"

@node(name="task_c")
def task_c(node_input: str):
    return f"C:{node_input[::-1]}"

my_join = JoinNode(name="my_join")

@node(name="final_merge")
def final_merge(node_input: dict):
    """JoinNode 输出是 {node_name: output} 的 dict"""
    parts = [f"{k}={v}" for k, v in sorted(node_input.items())]
    return "MERGED[" + ", ".join(parts) + "]"

graph_fanout = Workflow(
    name="graph_fanout",
    # 2.2.0已有Workflow级并发上限；这里显式设为2并由版本契约断言。
    max_concurrency=2,
    edges=[
        ("START", task_a, my_join),
        ("START", task_b, my_join),
        ("START", task_c, my_join),
        (my_join, final_merge),
    ],
)


# ============================================================
# 示例 4: Graph 循环 (back-edge)
# ============================================================
@node(name="seed")
def seed(node_input: str):
    """初始化草稿: 1 个要点"""
    return {"topic": node_input, "bullets": [f"{node_input} point 1"]}

@node(name="critic")
def critic(node_input: dict):
    """评论: 不足 3 个要点 -> REVISE, 否则 -> DONE"""
    if len(node_input["bullets"]) >= 3:
        return Event(route="DONE", output=node_input)
    return Event(route="REVISE", output=node_input)

@node(name="refine")
def refine(node_input: dict):
    """增加一个要点"""
    new_bullet = f"{node_input['topic']} point {len(node_input['bullets']) + 1}"
    return {**node_input, "bullets": [*node_input["bullets"], new_bullet]}

@node(name="finalize")
def finalize(node_input: dict):
    return f"Approved with {len(node_input['bullets'])} bullets: " + "; ".join(node_input["bullets"])

graph_loop = Workflow(
    name="graph_loop",
    edges=[
        ("START", seed, critic),
        (critic, {"REVISE": refine, "DONE": finalize}),
        (refine, critic),  # back-edge creates the loop
    ],
)


# ============================================================
# 示例 5: Dynamic workflow (@node + ctx.run_node)
# ============================================================
@node(name="hello_node")
def hello_node(node_input: str):
    return f"Hello {node_input}"

@node(name="format_node")
def format_node(node_input: str):
    return f"[FORMATTED] {node_input} [/FORMATTED]"

@node(rerun_on_resume=True)
async def my_dynamic_workflow(ctx: Context, node_input: str) -> str:
    result1 = await ctx.run_node(hello_node, node_input=node_input)
    result2 = await ctx.run_node(format_node, node_input=result1)
    return result2

dynamic_workflow = Workflow(
    name="dynamic_workflow",
    edges=[("START", my_dynamic_workflow)],
)


# ============================================================
# 示例 6: Template SequentialAgent
# ============================================================
# 用纯函数式 BaseAgent 代替 LlmAgent (离线无模型)
class FunctionAgent(BaseAgent):
    """纯函数 Agent：显式输入键 + 独占输出键；通过事件提交状态变更。"""
    func: Any = None
    input_key: str = "input_text"
    output_key: str = ""

    async def _run_async_impl(self, ctx):
        from google.genai import types
        if self.input_key not in ctx.session.state:
            raise ValueError(f"缺少输入键: {self.input_key}")
        node_input = ctx.session.state[self.input_key]
        result = self.func(node_input) if self.func else ""
        delta = {self.output_key: result} if self.output_key else {}
        yield Event(
            author=self.name,
            actions=EventActions(state_delta=delta),
            content=types.Content(
                role="model",
                parts=[types.Part(text=result)],
            ),
        )

# 定义步骤函数
def step_validate(x): return f"validated({x})"
def step_process(x): return f"processed({x})"
def step_report(x): return f"report({x})"

validator = FunctionAgent(name="validator", func=step_validate, output_key="val_out")
processor = FunctionAgent(name="processor", func=step_process, input_key="val_out", output_key="proc_out")
reporter = FunctionAgent(name="reporter", func=step_report, input_key="proc_out")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    template_sequential = SequentialAgent(
        name="template_sequential",
        sub_agents=[validator, processor, reporter],
    )


# ============================================================
# 示例 7: Template ParallelAgent
# ============================================================
def fetch_api1(x): return f"api1_data({x})"
def fetch_api2(x): return f"api2_data({x})"

fetcher1 = FunctionAgent(name="fetcher1", func=fetch_api1, output_key="api1")
fetcher2 = FunctionAgent(name="fetcher2", func=fetch_api2, output_key="api2")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    template_parallel = ParallelAgent(
        name="template_parallel",
        sub_agents=[fetcher1, fetcher2],
    )


# ============================================================
# 示例 8: Template LoopAgent (escalate 退出)
# ============================================================
class RefineAgent(BaseAgent):
    """迭代改进 Agent: 每次往 state['count'] +1"""
    async def _run_async_impl(self, ctx):
        from google.genai import types
        count = ctx.session.state.get("count", 0)
        count += 1
        text = f"iteration {count}"
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"count": count}),
            content=types.Content(role="model", parts=[types.Part(text=text)]),
        )

class CheckAndEscalate(BaseAgent):
    """检查是否达到 3 次迭代, 是则 escalate"""
    async def _run_async_impl(self, ctx):
        count = ctx.session.state.get("count", 0)
        should_stop = count >= 3
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_stop),
        )

refiner = RefineAgent(name="refiner")
checker = CheckAndEscalate(name="checker")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    template_loop = LoopAgent(
        name="template_loop",
        sub_agents=[refiner, checker],
        max_iterations=5,
    )


# ============================================================
# 验证辅助: 用 InMemoryRunner 实际运行
# ============================================================
async def run_workflow(agent, user_text: str, label: str):
    """用 InMemoryRunner 实际运行一个 Workflow/Agent, 收集最终输出"""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    app_name = "verify_app"
    user_id = "verify_user"
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=app_name, user_id=user_id, state={"input_text": user_text}
    )

    runner = Runner(
        app_name=app_name,
        agent=agent,
        session_service=session_service,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=user_text)],
    )

    final_text = ""
    final_output = None
    texts_by_author = {}
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):
        # 优先捕获用户可见 content
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text = part.text
                    texts_by_author[event.author] = part.text
        # 同时捕获 output (FunctionNode 返回值)
        if hasattr(event, 'output') and event.output is not None:
            final_output = event.output

    # 合并: content 优先, 否则用 output 的字符串形式
    result = final_text if final_text else str(final_output)
    # 检查所有并行分支，不能只看最后一个事件就宣布通过。
    if label == "tpl_par":
        expected = {"fetcher1": "api1_data(query)", "fetcher2": "api2_data(query)"}
        assert texts_by_author == expected, f"并行分支输入串扰或输出缺失: {texts_by_author}"
        result = str(dict(sorted(texts_by_author.items())))
    if label == "tpl_loop":
        stored = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session.id
        )
        assert stored is not None and stored.state.get("count") == 3
        assert final_text == "iteration 3", final_text
    print(f"  [{label}] input='{user_text}' -> output='{result}'")
    return result


async def main():
    adk_version = package_version("google-adk")
    print("=" * 60)
    print(f"ADK {adk_version} 编排原语离线验证")
    print("=" * 60)

    # 双版本契约：2.2.0为AgentKit固定版，2.10.0为官网主干对照版。
    node_params = inspect.signature(node).parameters
    workflow_params = inspect.signature(Workflow).parameters
    assert "parallel_worker" in node_params
    assert "max_concurrency" in workflow_params
    major_minor = tuple(int(x) for x in adk_version.split(".")[:2])
    if major_minor == (2, 2):
        assert "max_parallel_workers" not in node_params
    elif major_minor >= (2, 10):
        assert "max_parallel_workers" in node_params
    else:
        raise AssertionError(f"未审计的google-adk版本: {adk_version}")
    assert graph_fanout.max_concurrency == 2

    # Graph中未设置mode的LlmAgent保留None（运行时按single_turn处理）；
    # 显式chat节点不能接在非START前驱之后。
    from google.adk.agents import LlmAgent
    implicit_mode_agent = LlmAgent(name="implicit_mode_agent", model="dummy")
    assert implicit_mode_agent.mode is None
    try:
        Workflow(
            name="invalid_chat_graph",
            edges=[("START", hello_node, LlmAgent(name="chat_node", model="dummy", mode="chat"))],
        )
    except ValueError as exc:
        assert "mode='chat'" in str(exc)
    else:
        raise AssertionError("Graph应拒绝有非START前驱的chat-mode LlmAgent")

    # Template在2.2.0仍能构造，但必须发出弃用警告。
    for cls, kwargs in (
        (SequentialAgent, {}),
        (ParallelAgent, {}),
        (LoopAgent, {"max_iterations": 2}),
    ):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            cls(name=f"deprecated_{cls.__name__.lower()}", sub_agents=[], **kwargs)
        assert any(issubclass(w.category, DeprecationWarning) for w in caught), cls.__name__

    # 示例 1: Graph 顺序
    print("\n--- 示例1: Graph 顺序编排 ---")
    out1 = await run_workflow(graph_sequential, "start", "seq")
    assert "Report:" in out1, f"FAIL: {out1}"
    print("  PASS")

    # 示例 2: Graph 条件路由 (BUG)
    print("\n--- 示例2a: Graph 条件路由 -> BUG ---")
    out2a = await run_workflow(graph_routing, "I found a bug in login", "route_bug")
    assert "[BUG HANDLER]" in out2a, f"FAIL: {out2a}"
    print("  PASS")

    # 示例 2b: Graph 条件路由 (SUPPORT)
    print("\n--- 示例2b: Graph 条件路由 -> SUPPORT ---")
    out2b = await run_workflow(graph_routing, "I need help with setup", "route_support")
    assert "[SUPPORT HANDLER]" in out2b, f"FAIL: {out2b}"
    print("  PASS")

    print("\n--- 示例2c: Graph 默认路由 -> OTHER ---")
    out2c = await run_workflow(graph_routing, "general question", "route_other")
    assert out2c == "[OTHER HANDLER] processing: general question", f"FAIL: {out2c}"
    print("  PASS")

    # 示例 3: Graph 并行扇出 + JoinNode
    print("\n--- 示例3: Graph 并行扇出 + JoinNode ---")
    out3 = await run_workflow(graph_fanout, "hello", "fanout")
    assert out3 == "MERGED[task_a=A:HELLO, task_b=B:5, task_c=C:olleh]", f"FAIL: {out3}"
    print(f"  output: {out3}")
    print("  PASS")

    # 示例 4: Graph 循环 (back-edge)
    print("\n--- 示例4: Graph 循环 (back-edge 3次后退出) ---")
    out4 = await run_workflow(graph_loop, "topicX", "loop")
    assert out4 == "Approved with 3 bullets: topicX point 1; topicX point 2; topicX point 3", f"FAIL: {out4}"
    print(f"  output: {out4}")
    print("  PASS")

    # 示例 5: Dynamic workflow
    print("\n--- 示例5: Dynamic workflow (@node + ctx.run_node) ---")
    out5 = await run_workflow(dynamic_workflow, "World", "dynamic")
    assert out5 == "[FORMATTED] Hello World [/FORMATTED]", f"FAIL: {out5}"
    print(f"  output: {out5}")
    print("  PASS")

    # 示例 6: Template SequentialAgent
    print("\n--- 示例6: Template SequentialAgent ---")
    out6 = await run_workflow(template_sequential, "input_data", "tpl_seq")
    assert out6 == "report(processed(validated(input_data)))", f"FAIL: {out6}"
    print("  PASS")

    # 示例 7: Template ParallelAgent
    print("\n--- 示例7: Template ParallelAgent ---")
    out7 = await run_workflow(template_parallel, "query", "tpl_par")
    print(f"  output: {out7}")
    print("  PASS (parallel execution completed)")

    # 示例 8: Template LoopAgent
    print("\n--- 示例8: Template LoopAgent (max_iterations=5, escalate at 3) ---")
    out8 = await run_workflow(template_loop, "start", "tpl_loop")
    print(f"  output: {out8}")
    print("  PASS (loop completed)")

    print("\n" + "=" * 60)
    print("ALL EXAMPLES PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
