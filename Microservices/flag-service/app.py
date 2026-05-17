import os
import sys
import psycopg2
import requests
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from functools import wraps
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

load_dotenv()

from otel.telemetry import init_telemetry

app = Flask(__name__)
init_telemetry(app, instrument_requests=True)

DATABASE_URL = os.getenv("DATABASE_URL")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")

if not DATABASE_URL or not AUTH_SERVICE_URL:
    log.critical("Erro: DATABASE_URL e AUTH_SERVICE_URL devem ser definidos.")
    sys.exit(1)

try:
    pool = SimpleConnectionPool(1, 5, dsn=DATABASE_URL)
    log.info("Pool de conexÃµes com o PostgreSQL inicializado.")
except psycopg2.OperationalError as e:
    log.critical(f"Erro fatal ao conectar ao PostgreSQL: {e}")
    sys.exit(1)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header obrigatÃ³rio"}), 401

        try:
            validate_url = f"{AUTH_SERVICE_URL}/validate"
            response = requests.get(validate_url, headers={"Authorization": auth_header}, timeout=3)
            
            if response.status_code != 200:
                log.warning(f"Falha na validaÃ§Ã£o da chave (status: {response.status_code})")
                return jsonify({"error": "Chave de API invÃ¡lida"}), 401
        
        except requests.exceptions.Timeout:
            log.error("Timeout ao conectar com o auth-service")
            return jsonify({"error": "ServiÃ§o de autenticaÃ§Ã£o indisponÃ­vel (timeout)"}), 504
        except requests.exceptions.RequestException as e:
            log.error(f"Erro ao conectar com o auth-service: {e}")
            return jsonify({"error": "ServiÃ§o de autenticaÃ§Ã£o indisponÃ­vel"}), 503

        return f(*args, **kwargs)
    return decorated


@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/flags', methods=['POST'])
@require_auth
def create_flag():
    """ Cria uma nova definiÃ§Ã£o de feature flag """
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "'name' Ã© obrigatÃ³rio"}), 400
    
    name = data['name']
    description = data.get('description', '')
    is_enabled = data.get('is_enabled', False)
    
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO flags (name, description, is_enabled, created_at, updated_at) "
            "VALUES (%s, %s, %s, NOW(), NOW()) RETURNING *",
            (name, description, is_enabled)
        )
        new_flag = cur.fetchone()
        conn.commit()
        log.info(f"Flag '{name}' criada com sucesso.")
        return jsonify(new_flag), 201
    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        log.warning(f"Tentativa de criar flag duplicada: '{name}'")
        return jsonify({"error": f"Flag '{name}' jÃ¡ existe"}), 409
    except Exception as e:
        if conn: conn.rollback()
        log.error(f"Erro ao criar flag: {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/flags', methods=['GET'])
@require_auth
def get_flags():
    """ Lista todas as feature flags """
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM flags ORDER BY name")
        flags = cur.fetchall()
        return jsonify(flags)
    except Exception as e:
        log.error(f"Erro ao buscar flags: {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/flags/<string:name>', methods=['GET'])
@require_auth
def get_flag(name):
    """ Busca uma feature flag especÃ­fica pelo nome """
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM flags WHERE name = %s", (name,))
        flag = cur.fetchone()
        if not flag:
            return jsonify({"error": "Flag nÃ£o encontrada"}), 404
        return jsonify(flag)
    except Exception as e:
        log.error(f"Erro ao buscar flag '{name}': {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/flags/<string:name>', methods=['PUT'])
@require_auth
def update_flag(name):
    """ Atualiza uma feature flag (descriÃ§Ã£o ou status 'is_enabled') """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Corpo da requisiÃ§Ã£o obrigatÃ³rio"}), 400

    set_clauses = []
    values = []
    
    if 'description' in data:
        set_clauses.append(sql.SQL("description = %s"))
        values.append(data['description'])
    if 'is_enabled' in data:
        set_clauses.append(sql.SQL("is_enabled = %s"))
        values.append(data['is_enabled'])
    
    if not set_clauses:
        return jsonify({"error": "Pelo menos um campo ('description', 'is_enabled') Ã© obrigatÃ³rio"}), 400
    
    values.append(name)

    query = sql.SQL("UPDATE flags SET {set_clause} WHERE name = %s RETURNING *").format(
        set_clause=sql.SQL(", ").join(set_clauses)
    )
    
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, tuple(values))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Flag nÃ£o encontrada"}), 404
            
        updated_flag = cur.fetchone()
        conn.commit()
        log.info(f"Flag '{name}' atualizada com sucesso.")
        return jsonify(updated_flag), 200
    except Exception as e:
        if conn: conn.rollback()
        log.error(f"Erro ao atualizar flag '{name}': {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/flags/<string:name>', methods=['DELETE'])
@require_auth
def delete_flag(name):
    """ Deleta uma feature flag """
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor()
        cur.execute("DELETE FROM flags WHERE name = %s", (name,))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Flag nÃ£o encontrada"}), 404
            
        conn.commit()
        log.info(f"Flag '{name}' deletada com sucesso.")
        return "", 204
    except Exception as e:
        if conn: conn.rollback()
        log.error(f"Erro ao deletar flag '{name}': {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8002))
    app.run(host='0.0.0.0', port=port, debug=False)  # nosec B104
