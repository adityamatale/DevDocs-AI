from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from llama_index.observability.otel import LlamaIndexOpenTelemetry
from app.config import settings
    

# LLamaindex instrumentation
"""
This tells LlamaIndex:
    "Start emitting your internal operations as OpenTelemetry spans."
"""

instrumentor = LlamaIndexOpenTelemetry(
    service_name_or_resource = settings.OTEL_SERVICE_NAME,
    span_exporter = OTLPSpanExporter(settings.OTLP_EXPORTER_PATH),
    debug = True,
)

instrumentor.start_registering()


if __name__ == "__main__":
    pass