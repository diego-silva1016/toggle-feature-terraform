"""OpenTelemetry setup for Flask microservices (metrics + logs via OTLP)."""

from __future__ import annotations

import os


def _configure_providers() -> None:
    from opentelemetry import metrics, trace
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    service_name = os.getenv("OTEL_SERVICE_NAME", "unknown-service")
    resource = Resource.create({"service.name": service_name})

    # Traces setup
    trace_exporter = OTLPSpanExporter()
    trace.set_tracer_provider(
        TracerProvider(resource=resource)
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(trace_exporter)
    )

    # Metrics setup
    metric_exporter = OTLPMetricExporter()
    reader = PeriodicExportingMetricReader(metric_exporter)
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[reader])
    )

    # Logs setup
    log_exporter = OTLPLogExporter()
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(log_exporter)
    )
    set_logger_provider(logger_provider)


def init_telemetry(app=None, *, instrument_requests: bool = False) -> None:
    """Configure OTLP exporters and auto-instrumentation."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return

    _configure_providers()

    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    from opentelemetry.instrumentation.boto3 import Boto3Instrumentor

    LoggingInstrumentor().instrument(set_logging_format=True)

    # Database instrumentation
    Psycopg2Instrumentor().instrument()

    # AWS boto3 instrumentation
    Boto3Instrumentor().instrument()

    if instrument_requests:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()

    if app is not None:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument_app(app)
