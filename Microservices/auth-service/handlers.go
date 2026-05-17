package main

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"strings"
)

type CreateKeyRequest struct {
	Name string `json:"name"`
}

type CreateKeyResponse struct {
	Name    string `json:"name"`
	Key     string `json:"key"`
	Message string `json:"message"`
}

func (a *App) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

func (a *App) validateKeyHandler(w http.ResponseWriter, r *http.Request) {
	authHeader := r.Header.Get("Authorization")
	keyString := strings.TrimPrefix(authHeader, "Bearer ")

	if keyString == "" {
		http.Error(w, "Authorization header nÃ£o encontrado", http.StatusUnauthorized)
		return
	}

	keyHash := hashAPIKey(keyString)

	var id int
	err := a.DB.QueryRow("SELECT id FROM api_keys WHERE key_hash = $1 AND is_active = true", keyHash).Scan(&id)
	if err != nil {
		slog.Warn("api key validation failed", "hash_prefix", keyHash[:6], "error", err)
		http.Error(w, "Chave de API invÃ¡lida ou inativa", http.StatusUnauthorized)
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Chave vÃ¡lida"})
}

func (a *App) createKeyHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "MÃ©todo nÃ£o permitido", http.StatusMethodNotAllowed)
		return
	}

	var req CreateKeyRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Corpo da requisiÃ§Ã£o invÃ¡lido", http.StatusBadRequest)
		return
	}

	if req.Name == "" {
		http.Error(w, "O campo 'name' Ã© obrigatÃ³rio", http.StatusBadRequest)
		return
	}

	newKey, err := generateAPIKey()
	if err != nil {
		http.Error(w, "Erro ao gerar a chave", http.StatusInternalServerError)
		return
	}
	newKeyHash := hashAPIKey(newKey)

	var newID int
	err = a.DB.QueryRow(
		"INSERT INTO api_keys (name, key_hash) VALUES ($1, $2) RETURNING id",
		req.Name, newKeyHash,
	).Scan(&newID)

	if err != nil {
		slog.Error("failed to save api key", "error", err)
		http.Error(w, "Erro ao salvar a chave", http.StatusInternalServerError)
		return
	}

	slog.Info("api key created", "id", newID, "name", req.Name)
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(CreateKeyResponse{
		Name:    req.Name,
		Key:     newKey,
		Message: "Guarde esta chave com seguranÃ§a! VocÃª nÃ£o poderÃ¡ vÃª-la novamente.",
	})
}


func (a *App) masterKeyAuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		keyString := strings.TrimPrefix(authHeader, "Bearer ")

		if keyString != a.MasterKey {
			http.Error(w, "Acesso nÃ£o autorizado", http.StatusForbidden)
			return
		}
		next.ServeHTTP(w, r)
	})
}
