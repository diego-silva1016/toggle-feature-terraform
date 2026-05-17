module evaluation-service

go 1.21

require (
	github.com/aws/aws-sdk-go v1.51.10
	github.com/go-redis/redis/v8 v8.11.5
	github.com/joho/godotenv v1.5.1
	go.opentelemetry.io/instrumentation/database/sql/otelsql v0.1.0
	toggle-feature/otel v0.0.0
)

replace toggle-feature/otel => ./otel

require (
	github.com/cespare/xxhash/v2 v2.2.0 // indirect
	github.com/dgryski/go-rendezvous v0.0.0-20200823014737-9f7001d12a5f // indirect
	github.com/jmespath/go-jmespath v0.4.0 // indirect
	github.com/onsi/ginkgo v1.16.5 // indirect
	github.com/onsi/gomega v1.27.6 // indirect
	golang.org/x/net v0.21.0 // indirect
)