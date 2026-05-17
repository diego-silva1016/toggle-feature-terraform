package main

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
)

type EvaluationResponse struct {
	FlagName string `json:"flag_name"`
	UserID   string `json:"user_id"`
	Result   bool   `json:"result"`
}

func (a *App) healthHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	tracer := otel.Tracer("evaluation-service")
	_, span := tracer.Start(ctx, "handler.health")
	defer span.End()

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (a *App) evaluationHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	tracer := otel.Tracer("evaluation-service")
	ctx, span := tracer.Start(ctx, "handler.evaluation")
	defer span.End()

	w.Header().Set("Content-Type", "application/json")

	userID := r.URL.Query().Get("user_id")
	flagName := r.URL.Query().Get("flag_name")

	span.SetAttributes(
		attribute.String("user.id", userID),
		attribute.String("flag.name", flagName),
	)

	if userID == "" || flagName == "" {
		span.SetStatus(codes.Error, "missing required parameters")
		http.Error(w, `{"error": "user_id e flag_name sÃ£o obrigatÃ³rios"}`, http.StatusBadRequest)
		return
	}

	result, err := a.getDecision(ctx, userID, flagName)
	if err != nil {
		if _, ok := err.(*NotFoundError); ok {
			result = false
		} else {
			span.SetStatus(codes.Error, "flag evaluation failed")
			span.RecordError(err)
			slog.Error("flag evaluation failed", "flag", flagName, "error", err)
			http.Error(w, `{"error": "Erro interno ao avaliar a flag"}`, http.StatusBadGateway)
			return
		}
	}

	span.SetStatus(codes.Ok)
	span.SetAttributes(attribute.Bool("flag.result", result))
	go a.sendEvaluationEvent(userID, flagName, result)

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(EvaluationResponse{
		FlagName: flagName,
		UserID:   userID,
		Result:   result,
	})
}
