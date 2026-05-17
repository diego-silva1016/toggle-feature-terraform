package otel

import (
	"context"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"time"

	"go.opentelemetry.io/contrib/bridges/otelslog"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
	"go.opentelemetry.io/otel/log/global"
	"go.opentelemetry.io/otel/propagation"
	sdklog "go.opentelemetry.io/otel/sdk/log"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	semconv "go.opentelemetry.io/otel/semconv/v1.27.0"
)

// Init configures OTLP metrics and logs export. Returns shutdown when OTEL_EXPORTER_OTLP_ENDPOINT is set.
func Init(ctx context.Context, serviceName string) (func(context.Context) error, error) {
	if os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT") == "" {
		return func(context.Context) error { return nil }, nil
	}

	res, err := resource.Merge(
		resource.Default(),
		resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName(serviceName),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("resource: %w", err)
	}

	metricExporter, err := otlpmetricgrpc.New(ctx)
	if err != nil {
		return nil, fmt.Errorf("metric exporter: %w", err)
	}

	meterProvider := sdkmetric.NewMeterProvider(
		sdkmetric.WithResource(res),
		sdkmetric.WithReader(
			sdkmetric.NewPeriodicReader(
				metricExporter,
				sdkmetric.WithInterval(15*time.Second),
			),
		),
	)
	otel.SetMeterProvider(meterProvider)

	logExporter, err := otlploggrpc.New(ctx)
	if err != nil {
		_ = meterProvider.Shutdown(ctx)
		return nil, fmt.Errorf("log exporter: %w", err)
	}

	loggerProvider := sdklog.NewLoggerProvider(
		sdklog.WithResource(res),
		sdklog.WithProcessor(sdklog.NewBatchProcessor(logExporter)),
	)
	global.SetLoggerProvider(loggerProvider)

	logger := otelslog.NewLogger(serviceName, otelslog.WithLoggerProvider(loggerProvider))
	slog.SetDefault(slog.New(logger))

	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	shutdown := func(ctx context.Context) error {
		var errs []error
		if err := meterProvider.Shutdown(ctx); err != nil {
			errs = append(errs, err)
		}
		if err := loggerProvider.Shutdown(ctx); err != nil {
			errs = append(errs, err)
		}
		if len(errs) > 0 {
			return fmt.Errorf("shutdown: %v", errs)
		}
		return nil
	}

	return shutdown, nil
}

// WrapHandler instruments an HTTP handler for request metrics.
func WrapHandler(pattern string, handler http.Handler) http.Handler {
	if os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT") == "" {
		return handler
	}
	return otelhttp.NewHandler(handler, pattern)
}

// WrapHandlerFunc instruments a HandlerFunc.
func WrapHandlerFunc(pattern string, handler http.HandlerFunc) http.HandlerFunc {
	wrapped := WrapHandler(pattern, handler)
	return func(w http.ResponseWriter, r *http.Request) {
		wrapped.ServeHTTP(w, r)
	}
}
