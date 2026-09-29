"""OpenTelemetry wiring for the Wizard shim.

Responsibilities (design 01-architecture.md §4.7):
  * Create a root span per inbound request: ``invocation`` with
    ``service.name=wizard`` and ``gen_ai.operation.name`` attributes.
  * Continue an inbound W3C ``traceparent`` header when present (so a trace
    started by the frontend or an upstream Runtime is joined, not orphaned).
  * Provide a ``Tracer`` and helper span context managers used around the
    HermesBridge turn (``invoke_agent {wizard}``) and around LLM / tool
    callbacks (``call_llm`` / ``execute_tool <name>``) with ``gen_ai.*`` attrs.
  * Stamp every span with ``wizard_version`` / ``hermes_version``.
  * Export to OTLP when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set; otherwise fall
    back to a no-op/console provider so the service still starts.
  * ``inject_traceparent_headers`` propagates the current trace context onto
    outbound tool / proxy request headers.

Hermes itself emits no OTel spans; the shim injects them via the bridge's
callback hooks (see hermes_bridge.py).
"""
from __future__ import annotations

import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.trace import SpanContext

logger = logging.getLogger(__name__)

_TRACER_NAME = "wizard.shim"
_provider_initialized = False


def build_resource(settings) -> Resource:
    return Resource.create(
        {
            "service.name": settings.service_name,
            "wizard_version": settings.wizard_version,
            "hermes_version": settings.hermes_version,
        }
    )


def init_tracer_provider(settings) -> TracerProvider:
    """Idempotently build and install the global TracerProvider."""
    global _provider_initialized
    provider = TracerProvider(
        resource=build_resource(settings),
        sampler=TraceIdRatioBased(1.0),
    )

    endpoint = (settings.otel_exporter_otlp_endpoint or "").strip()
    if endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
            )
            logger.info("OTel OTLP exporter -> %s", endpoint)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("OTLP exporter unavailable (%s); falling back to console", e)
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # No collector configured: still export to console so local smoke runs
        # show spans, but never attempt network egress.
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT unset; using console span exporter")

    trace.set_tracer_provider(provider)
    _provider_initialized = True
    return provider


def get_tracer() -> trace.Tracer:
    return trace.get_tracer(_TRACER_NAME)


def current_trace_id() -> str | None:
    """Hex trace id of the currently-active span, or None if not recording."""
    span = trace.get_current_span()
    ctx: SpanContext | None = span.get_span_context() if span else None
    if ctx and ctx.is_valid and ctx.trace_flags.sampled:
        return format(ctx.trace_id, "032x")
    return None


def inject_traceparent_headers(headers: dict | None = None) -> dict:
    """Return a copy of ``headers`` with the W3C ``traceparent`` injected.

    Used on outbound tool / runtime-proxy calls so the downstream Runtime joins
    the same trace. Safe to call when no span is active (returns headers).
    """
    out: dict = dict(headers or {})
    inject(out)
    return out


class _NullSpan:
    """Context-manager stand-in when tracing is effectively a no-op."""

    def __enter__(self) -> _NullSpan:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, *a: Any, **k: Any) -> None:
        pass


def start_span(name: str, **attrs: Any):
    """Start a span with the standard wizard/version attributes stamped.

    Returns a context manager-like object exposing ``set_attribute`` /
    ``set_status``. Never raises: if the global tracer is the no-op tracer the
    returned object is a cheap null span.
    """
    span = get_tracer().start_as_current_span(name)
    # start_as_current_span returns a context manager; enter lazily by wrapping.
    return _AttrSpan(span, attrs)


class _AttrSpan:
    """Wraps a ``start_as_current_span`` CM and applies default attrs on enter."""

    def __init__(self, cm, attrs: dict) -> None:
        self._cm = cm
        self._attrs = attrs or {}
        self._span: Any = None

    def __enter__(self):
        self._span = self._cm.__enter__()
        for k, v in self._attrs.items():
            try:
                self._span.set_attribute(k, v)
            except Exception:  # pragma: no cover
                pass
        return self._span

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


def make_otel_asgi_middleware(settings):
    """Build a Starlette @app.middleware("http") callable.

    Continues an inbound ``traceparent`` and opens the root ``invocation`` span
    for every HTTP request. The business handlers then nest their own spans via
    ``start_span``.
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    version_attrs = {
        "wizard_version": settings.wizard_version,
        "hermes_version": settings.hermes_version,
    }

    class OtelMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # 1. Extract inbound W3C TraceContext (traceparent header).
            carrier = dict(request.headers)
            ctx = extract(carrier)
            token = attach(ctx)
            try:
                with get_tracer().start_as_current_span("invocation") as root:
                    root.set_attribute("service.name", settings.service_name)
                    root.set_attribute("gen_ai.operation.name", "invoke_agent")
                    root.set_attribute("gen_ai.span.kind", "workflow")
                    root.set_attribute("http.route", request.url.path)
                    for k, v in version_attrs.items():
                        root.set_attribute(k, v)
                    response = await call_next(request)
                    # Echo trace id back so the frontend can pull Step4 overlay.
                    tid = current_trace_id()
                    if tid:
                        response.headers["trace-id"] = tid
                    return response
            finally:
                detach(token)

    return OtelMiddleware


__all__ = [
    "current_trace_id",
    "get_tracer",
    "init_tracer_provider",
    "inject_traceparent_headers",
    "make_otel_asgi_middleware",
    "start_span",
]
