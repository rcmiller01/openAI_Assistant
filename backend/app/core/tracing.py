"""OpenTelemetry tracing configuration for observability."""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Configuration
ENABLE_TRACING = os.getenv("ENABLE_TRACING", "false").lower() == "true"
OTEL_EXPORTER_TYPE = os.getenv("OTEL_EXPORTER_TYPE", "console")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "orchestrator")
OTEL_EXPORTER_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_ENDPOINT",
    "http://localhost:4318"
)

# Global tracer instance
_tracer: Optional[Any] = None


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing."""
    global _tracer
    
    if not ENABLE_TRACING:
        logger.info("Tracing disabled (ENABLE_TRACING=false)")
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import (
            FastAPIInstrumentor
        )
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import (
            SQLAlchemyInstrumentor
        )
        
        # Create resource with service name
        resource = Resource.create({
            "service.name": OTEL_SERVICE_NAME,
            "service.version": os.getenv("APP_VERSION", "dev"),
            "deployment.environment": os.getenv("APP_ENV", "development"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Configure exporter
        if OTEL_EXPORTER_TYPE == "otlp":
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter
                )
                exporter = OTLPSpanExporter(
                    endpoint=f"{OTEL_EXPORTER_ENDPOINT}/v1/traces"
                )
                logger.info(
                    f"Using OTLP exporter: {OTEL_EXPORTER_ENDPOINT}"
                )
            except ImportError:
                logger.warning(
                    "OTLP exporter not available, falling back to console"
                )
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()
            logger.info("Using console exporter for traces")
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Auto-instrument libraries
        FastAPIInstrumentor.instrument()
        HTTPXClientInstrumentor.instrument()
        SQLAlchemyInstrumentor.instrument()
        
        # Get tracer
        _tracer = trace.get_tracer(__name__)
        
        logger.info(
            "OpenTelemetry tracing initialized",
            extra={
                "service": OTEL_SERVICE_NAME,
                "exporter": OTEL_EXPORTER_TYPE
            }
        )
        
    except ImportError as e:
        logger.warning(
            f"OpenTelemetry not available: {e}. "
            "Install with: pip install opentelemetry-api "
            "opentelemetry-sdk opentelemetry-instrumentation-fastapi "
            "opentelemetry-instrumentation-httpx "
            "opentelemetry-instrumentation-sqlalchemy"
        )


def get_tracer():
    """Get the global tracer instance."""
    if _tracer is None:
        # Return a no-op tracer if tracing not enabled
        try:
            from opentelemetry import trace
            return trace.get_tracer(__name__)
        except ImportError:
            return None
    return _tracer


@asynccontextmanager
async def trace_operation(name: str, attributes: Optional[dict] = None):
    """
    Context manager for tracing async operations.
    
    Usage:
        async with trace_operation("store_memory", {"text_len": 100}):
            await store_memory(text)
    """
    tracer = get_tracer()
    
    if tracer is None:
        # No tracing, just yield
        yield None
        return
    
    try:
        from opentelemetry import trace
        
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(
                    trace.Status(trace.StatusCode.ERROR, str(e))
                )
                raise
    except ImportError:
        # OpenTelemetry not available
        yield None


def add_span_event(name: str, attributes: Optional[dict] = None) -> None:
    """Add an event to the current span."""
    try:
        from opentelemetry import trace
        
        span = trace.get_current_span()
        if span and span.is_recording():
            span.add_event(name, attributes or {})
    except (ImportError, AttributeError):
        pass


def set_span_attributes(**attributes) -> None:
    """Set attributes on the current span."""
    try:
        from opentelemetry import trace
        
        span = trace.get_current_span()
        if span and span.is_recording():
            for key, value in attributes.items():
                span.set_attribute(key, value)
    except (ImportError, AttributeError):
        pass


def cleanup_tracing() -> None:
    """Cleanup tracing resources."""
    if not ENABLE_TRACING:
        return
    
    try:
        from opentelemetry import trace
        
        provider = trace.get_tracer_provider()
        if hasattr(provider, 'shutdown'):
            provider.shutdown()
        
        logger.info("Tracing cleanup complete")
    except (ImportError, AttributeError):
        pass
