package main

import (
	"context"
	"database/sql"
	"log"
	"log/slog"
	"net/http"
	"os"

	_ "github.com/jackc/pgx/v4/stdlib"
	"github.com/joho/godotenv"
	tfotel "toggle-feature/otel"
)

type App struct {
	DB         *sql.DB
	MasterKey  string
}

func main() {
	_ = godotenv.Load()

	serviceName := os.Getenv("OTEL_SERVICE_NAME")
	if serviceName == "" {
		serviceName = "auth-service"
	}

	ctx := context.Background()
	shutdown, err := tfotel.Init(ctx, serviceName)
	if err != nil {
		log.Fatalf("OpenTelemetry init failed: %v", err)
	}
	defer func() {
		_ = shutdown(context.Background())
	}()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8001"
	}

	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		log.Fatal("DATABASE_URL deve ser definida")
	}

	masterKey := os.Getenv("MASTER_KEY")
	if masterKey == "" {
		log.Fatal("MASTER_KEY deve ser definida")
	}

	db, err := connectDB(databaseURL)
	if err != nil {
		log.Fatalf("NÃ£o foi possÃ­vel conectar ao banco de dados: %v", err)
	}
	defer db.Close()
	if err := ensureSchema(db); err != nil {
		log.Fatalf("NÃ£o foi possÃ­vel preparar o schema do banco: %v", err)
	}

	app := &App{
		DB:         db,
		MasterKey:  masterKey,
	}

	mux := http.NewServeMux()
	mux.Handle("/health", tfotel.WrapHandler("/health", http.HandlerFunc(app.healthHandler)))
	mux.Handle("/validate", tfotel.WrapHandler("/validate", http.HandlerFunc(app.validateKeyHandler)))
	mux.Handle(
		"/admin/keys",
		tfotel.WrapHandler(
			"/admin/keys",
			app.masterKeyAuthMiddleware(http.HandlerFunc(app.createKeyHandler)),
		),
	)

	slog.Info("auth-service listening", "port", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatal(err)
	}
}

func connectDB(databaseURL string) (*sql.DB, error) {
	db, err := sql.Open("pgx", databaseURL)
	if err != nil {
		return nil, err
	}

	if err = db.Ping(); err != nil {
		return nil, err
	}

	slog.Info("connected to PostgreSQL")
	return db, nil
}

func ensureSchema(db *sql.DB) error {
	_, err := db.Exec(`
		CREATE TABLE IF NOT EXISTS api_keys (
			id SERIAL PRIMARY KEY,
			name VARCHAR(100) NOT NULL,
			key_hash VARCHAR(64) NOT NULL UNIQUE,
			is_active BOOLEAN DEFAULT true,
			created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
		)
	`)
	if err == nil {
		slog.Info("auth-service schema verified")
	}
	return err
}
