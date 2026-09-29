"""The minimal integrated Harness: one request through all 14 components.

Pipeline (each stage maps to a formal component):
  identity -> guardrails(input) -> knowledge-base -> veadk/sdk agent run ->
  session-memory -> guardrails(output) -> observability -> evaluation.
"""
from __future__ import annotations

from .contract import InvokeRequest, InvokeResult, CloudBoundary
from .c01_veadk import ScriptedRunner, veadk_status
from .c02_sdk_app import AgentkitSimpleApp, HTTPError
from .c03_runtime import RuntimeDescriptor
from .c06_memory import LocalThreeLayerMemory
from .c09_sandbox import LocalSandbox
from .c10_guardrails import LocalShield
from .c11_identity import IdentityManager, Principal, AuthError
from .c12_knowledge import LocalKnowledgeBase
from .c13_observability import TraceRecorder


class MinimalHarness:
    def __init__(self) -> None:
        self.runtime = RuntimeDescriptor(name="harness-demo", image="local/harness:0.1")
        self.identity = IdentityManager()
        self.shield = LocalShield()
        self.kb = LocalKnowledgeBase.build(top_k=2)
        self.memory = LocalThreeLayerMemory.build()
        self.sandbox = LocalSandbox()
        self.tracer = TraceRecorder()
        self.runner = ScriptedRunner(reply="The agent answered based on retrieved context.")
        self.app = AgentkitSimpleApp()

        # seed identity + knowledge
        self.identity.grant("support", "chat")
        self.kb.add_document("doc1", "refund policy: items can be returned within 30 days.")
        self.kb.add_document("doc2", "shipping: orders dispatch within 2 business days.")

    async def handle(self, req: InvokeRequest) -> InvokeResult:
        trace_id = self.tracer.new_trace()
        # 1) identity (inbound authN; user_id header is not trusted identity)
        try:
            subject = self.identity.authenticate(req.authorization)
        except AuthError as e:
            self.tracer.record("auth", trace_id, {"gen_ai.operation.name": "auth",
                                                  "gen_ai.user.id": req.user_id or "anon"},
                               status="ERROR")
            raise
        # 2) guardrails input side
        blocked = self.shield.check_input(req.prompt)
        self.tracer.record("guardrail.in", trace_id,
                           {"gen_ai.operation.name": "guardrail", "gen_ai.user.id": subject.user},
                           duration_ms=1)
        if blocked:
            self.tracer.record("invoke_agent", trace_id,
                               {"gen_ai.operation.name": "invoke_agent", "gen_ai.session.id": req.session_id},
                               status="ERROR", duration_ms=1)
            return InvokeResult(text=blocked, user_id=subject.user, session_id=req.session_id,
                                trace_id=trace_id, blocks=["prompt_injection"], ok=False)
        # 3) knowledge base retrieval
        hits = self.kb.retrieve(req.prompt)
        self.tracer.record("load_knowledgebase", trace_id,
                           {"gen_ai.operation.name": "tool", "gen_ai.tool.name": "LoadKnowledgebaseTool"},
                           duration_ms=2)
        # 4) agent run (veadk Runner contract; model call is CloudBoundary)
        answer = await self.runner.run(messages=req.prompt, user_id=req.user_id,
                                       session_id=req.session_id)
        answer = f"{answer} (kb_hits={[h['id'] for h in hits]})"
        self.tracer.record("call_llm", trace_id,
                           {"gen_ai.operation.name": "chat", "gen_ai.span.kind": "llm"},
                           duration_ms=40)
        # 5) memory: record + persist to long-term
        self.memory.append_session(req.user_id, req.session_id, req.prompt)
        await self.memory.save_session_to_long_term_memory(req.session_id, req.user_id)
        # 6) guardrails output side
        answer = self.shield.check_output(answer)
        self.tracer.record("invoke_agent", trace_id,
                           {"gen_ai.operation.name": "invoke_agent", "gen_ai.session.id": req.session_id},
                           duration_ms=45)
        return InvokeResult(text=answer, user_id=subject.user, session_id=req.session_id,
                            trace_id=trace_id)

    def cloud_boundary_report(self) -> dict:
        return {
            "runtime.deploy_invoke": "needs AK/SK + CR image",
            "veadk.runner.run_model_call": "needs ARK model key",
            "guardrails.real_llm_shield": "needs TOOL_LLM_SHIELD_APP_ID",
            "mcp.live_endpoint": "needs MCP_ENDPOINT + MCP_AUTH_KEY",
            "a2a.registry_register": "needs A2A space + AK/SK",
            "sandbox.live": "needs AGENTKIT_TOOL_ID",
            "memory.mem0_viking": "needs mem0/viking connection",
            "knowledge.viking": "needs DATABASE_VIKING_COLLECTION",
            "observability.apmplus_query": "needs APMPlus signed OpenAPI",
            "eval.platform": "needs online eval platform",
            "veadk_status": veadk_status(),
        }
