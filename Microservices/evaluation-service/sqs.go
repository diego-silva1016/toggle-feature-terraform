package main

import (
	"encoding/json"
	"log/slog"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/service/sqs"
)

type EvaluationEvent struct {
	UserID    string    `json:"user_id"`
	FlagName  string    `json:"flag_name"`
	Result    bool      `json:"result"`
	Timestamp time.Time `json:"timestamp"`
}

func (a *App) sendEvaluationEvent(userID, flagName string, result bool) {
	if a.SqsSvc == nil || a.SqsQueueURL == "" {
		slog.Info("sqs disabled; evaluation event skipped", "user", userID, "flag", flagName, "result", result)
		return
	}

	event := EvaluationEvent{
		UserID:    userID,
		FlagName:  flagName,
		Result:    result,
		Timestamp: time.Now().UTC(),
	}

	body, err := json.Marshal(event)
	if err != nil {
		slog.Error("failed to serialize sqs event", "error", err)
		return
	}

	_, err = a.SqsSvc.SendMessage(&sqs.SendMessageInput{
		MessageBody: aws.String(string(body)),
		QueueUrl:    aws.String(a.SqsQueueURL),
	})

	if err != nil {
		slog.Error("failed to send sqs message", "error", err)
	} else {
		slog.Info("evaluation event sent to sqs", "flag", flagName)
	}
}
