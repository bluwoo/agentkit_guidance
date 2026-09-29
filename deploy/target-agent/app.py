from __future__ import annotations

import os

from agentkit.apps import AgentkitSimpleApp
from openai import OpenAI
from opentelemetry import trace

# APMPlus trace export: fetch app key via Runtime/veFaaS IAM (no long-term AK/SK
# baked in). AgentkitSimpleApp may install the global TracerProvider before this
# module initialises. VeADK deliberately treats such a provider as externally
# managed, so register the APMPlus processor explicitly instead of relying on
# OpentelemetryTracer to replace the provider.
_apmplus_exporter = None
try:
    from opentelemetry.sdk.trace import TracerProvider
    from veadk.tracing.telemetry.exporters.apmplus_exporter import APMPlusExporter
    from veadk.tracing.telemetry.opentelemetry_tracer import OpentelemetryTracer

    if os.environ.get("OTEL_SDK_DISABLED", "").lower() not in ("1", "true", "yes"):
        _apmplus_exporter = APMPlusExporter()
        _provider = trace.get_tracer_provider()
        if isinstance(_provider, TracerProvider):
            _apmplus_exporter.register(_provider)
        else:
            OpentelemetryTracer(exporters=[_apmplus_exporter])
except Exception as _otel_err:
    import logging

    logging.getLogger("target-agent").warning("APMPlus exporter init skipped: %s", _otel_err)

SERVICE_NAME = "support-triage-agent"
MODEL = os.environ["MODEL_NAME"]
API_KEY = os.environ["MODEL_API_KEY"]
BASE_URL = os.environ.get("MODEL_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/")

tracer = trace.get_tracer(SERVICE_NAME)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
app = AgentkitSimpleApp()


@app.entrypoint
async def invoke(payload: dict, headers: dict) -> dict[str, str]:
    user_input = str(payload.get("input") or payload.get("prompt") or "")
    session_id = str(payload.get("session_id") or headers.get("session_id") or "")
    with tracer.start_as_current_span("invoke_agent") as agent_span:
        agent_span.set_attribute("service.name", SERVICE_NAME)
        agent_span.set_attribute("gen_ai.agent.name", SERVICE_NAME)
        agent_span.set_attribute("gen_ai.operation.name", "invoke_agent")
        agent_span.set_attribute("gen_ai.span.kind", "agent")
        with tracer.start_as_current_span("call_llm") as llm_span:
            llm_span.set_attribute("service.name", SERVICE_NAME)
            llm_span.set_attribute("gen_ai.request.model", MODEL)
            llm_span.set_attribute("gen_ai.operation.name", "chat")
            llm_span.set_attribute("gen_ai.span.kind", "llm")
            response = client.chat.completions.create(
                model=MODEL,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "你是客服风险分流Agent。只回答一行：升级人工：是/否；理由：简短理由。退款、投诉、法律、安全与无法确定的请求升级人工。",
                    },
                    {"role": "user", "content": user_input},
                ],
            )
            output = response.choices[0].message.content or ""
    context = trace.get_current_span().get_span_context()
    trace_id = f"{context.trace_id:032x}" if context.is_valid else ""
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if callable(force_flush):
        force_flush(timeout_millis=5000)
    return {"output": output, "reply": output, "trace_id": trace_id, "session_id": session_id}


@app.ping
def ping() -> str:
    return "ok"
