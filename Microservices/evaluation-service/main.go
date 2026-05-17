package main

import (
	"context"
	"log"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sqs"
	"github.com/go-redis/redis/v8"
	"github.com/joho/godotenv"
	tfotel "toggle-feature/otel"
)

var ctx = context.Background()

type App struct {
	RedisClient         *redis.Client
	SqsSvc              *sqs.SQS
	SqsQueueURL         string
	HttpClient          *http.Client
	FlagServiceURL      string
	TargetingServiceURL string
}

func main() {
	_ = godotenv.Load()

	serviceName := os.Getenv("OTEL_SERVICE_NAME")
	if serviceName == "" {
		serviceName = "evaluation-service"
	}

	initCtx := context.Background()
	shutdown, err := tfotel.Init(initCtx, serviceName)
	if err != nil {
		log.Fatalf("OpenTelemetry init failed: %v", err)
	}
	defer func() {
		_ = shutdown(context.Background())
	}()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8004"
	}

	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		log.Fatal("REDIS_URL deve ser definida (ex: redis://localhost:6379)")
	}

	flagSvcURL := os.Getenv("FLAG_SERVICE_URL")
	if flagSvcURL == "" {
		log.Fatal("FLAG_SERVICE_URL deve ser definida")
	}

	targetingSvcURL := os.Getenv("TARGETING_SERVICE_URL")
	if targetingSvcURL == "" {
		log.Fatal("TARGETING_SERVICE_URL deve ser definida")
	}

	sqsQueueURL := os.Getenv("AWS_SQS_URL")
	awsRegion := os.Getenv("AWS_REGION")
	if sqsQueueURL == "" {
		slog.Warn("AWS_SQS_URL not set; analytics events will not be sent")
	}
	if awsRegion == "" && sqsQueueURL != "" {
		log.Fatal("AWS_REGION deve ser definida para usar SQS")
	}

	
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		log.Fatalf("NÃ£o foi possÃ­vel parsear a URL do Redis: %v", err)
	}
	rdb := redis.NewClient(opt)
	if _, err := rdb.Ping(ctx).Result(); err != nil {
		log.Fatalf("NÃ£o foi possÃ­vel conectar ao Redis: %v", err)
	}
	slog.Info("connected to Redis")

	var sqsSvc *sqs.SQS
	if sqsQueueURL != "" {
		sess, err := session.NewSession(&aws.Config{Region: aws.String(awsRegion)})
		if err != nil {
			log.Fatalf("NÃ£o foi possÃ­vel criar sessÃ£o AWS: %v", err)
		}
		sqsSvc = sqs.New(sess)
		slog.Info("SQS client initialized")
	}

	httpClient := &http.Client{
		Timeout: 5 * time.Second,
	}

	app := &App{
		RedisClient:         rdb,
		SqsSvc:              sqsSvc,
		SqsQueueURL:         sqsQueueURL,
		HttpClient:          httpClient,
		FlagServiceURL:      flagSvcURL,
		TargetingServiceURL: targetingSvcURL,
	}

	mux := http.NewServeMux()
	mux.Handle("/health", tfotel.WrapHandler("/health", http.HandlerFunc(app.healthHandler)))
	mux.Handle("/evaluate", tfotel.WrapHandler("/evaluate", http.HandlerFunc(app.evaluationHandler)))

	slog.Info("evaluation-service listening", "port", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}
