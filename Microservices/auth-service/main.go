package main

import (
	"database/sql"
	"log"
	"net/http"
	"os"

	_ "github.com/jackc/pgx/v4/stdlib"
	"github.com/joho/godotenv"
)

type App struct {
	DB         *sql.DB
	MasterKey  string
}

func main() {
	_ = godotenv.Load()

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
	mux.HandleFunc("/health", app.healthHandler)

	mux.HandleFunc("/validate", app.validateKeyHandler)

	mux.Handle("/admin/keys", app.masterKeyAuthMiddleware(http.HandlerFunc(app.createKeyHandler)))

	log.Printf("ServiÃ§o de AutenticaÃ§Ã£o (Go) rodando na porta %s", port)
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

	log.Println("Conectado ao PostgreSQL com sucesso!")
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
		log.Println("Schema do auth-service verificado com sucesso.")
	}
	return err
}
