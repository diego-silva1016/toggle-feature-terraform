package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sqs"
	"github.com/go-redis/redis/v8"
	"github.com/joho/godotenv"
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
		log.Println("AtenÃ§Ã£o: AWS_SQS_URL nÃ£o definida. Eventos nÃ£o serÃ£o enviados.")
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
	log.Println("Conectado ao Redis com sucesso!")

	var sqsSvc *sqs.SQS
	if sqsQueueURL != "" {
		sess, err := session.NewSession(&aws.Config{Region: aws.String(awsRegion)})
		if err != nil {
			log.Fatalf("NÃ£o foi possÃ­vel criar sessÃ£o AWS: %v", err)
		}
		sqsSvc = sqs.New(sess)
		log.Println("Cliente SQS inicializado com sucesso.")
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
	mux.HandleFunc("/health", app.healthHandler)
	mux.HandleFunc("/evaluate", app.evaluationHandler)

	log.Printf("ServiÃ§o de AvaliaÃ§Ã£o (Go) rodando na porta %s", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}
