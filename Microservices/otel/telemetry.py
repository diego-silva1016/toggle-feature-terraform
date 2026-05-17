"""OpenTelemetry setup for Flask microservices (metrics + logs via OTLP)."""

from __future__ import annotations

import os


def _configure_providers() -> None:
    from opentelemetry import metrics
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource

    service_name = os.getenv("OTEL_SERVICE_NAME", "unknown-service")
    resource = Resource.create({"service.name": service_name})

    metric_exporter = OTLPMetricExporter()
    reader = PeriodicExportingMetricReader(metric_exporter)
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[reader])
    )

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

    LoggingInstrumentor().instrument(set_logging_format=True)

    if instrument_requests:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()

    if app is not None:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument_app(app)
