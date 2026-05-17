import os
import sys
import psycopg2
import requests
import json
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, Json
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
    log.info("Pool de conexÃµes com o PostgreSQL (targeting) inicializado.")
except psycopg2.OperationalError as e:
    log.critical(f"Erro fatal ao conectar ao PostgreSQL: {e}")
    sys.exit(1)

def require_auth(f):
    """ Middleware para validar a chave de API contra o auth-service """
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

@app.route('/rules', methods=['POST'])
@require_auth
def create_rule():
    """ Cria uma nova regra de segmentaÃ§Ã£o para uma flag """
    data = request.get_json()
    if not data or 'flag_name' not in data or 'rules' not in data:
        return jsonify({"error": "'flag_name' e 'rules' (JSON) sÃ£o obrigatÃ³rios"}), 400
    
    flag_name = data['flag_name']
    rules_obj = data['rules']
    is_enabled = data.get('is_enabled', True)
    
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO targeting_rules (flag_name, is_enabled, rules, created_at, updated_at) "
            "VALUES (%s, %s, %s, NOW(), NOW()) RETURNING *",
            (flag_name, is_enabled, Json(rules_obj))
        )
        new_rule = cur.fetchone()
        conn.commit()
        log.info(f"Regra para '{flag_name}' criada com sucesso.")
        return jsonify(new_rule), 201
    except psycopg2.IntegrityError:
        if conn: conn.rollback()
        log.warning(f"Tentativa de criar regra duplicada: '{flag_name}'")
        return jsonify({"error": f"Regra para a flag '{flag_name}' jÃ¡ existe"}), 409
    except Exception as e:
        if conn: conn.rollback()
        log.error(f"Erro ao criar regra: {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/rules/<string:flag_name>', methods=['GET'])
@require_auth
def get_rule(flag_name):
    """ Busca uma regra de segmentaÃ§Ã£o pelo nome da flag """
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM targeting_rules WHERE flag_name = %s", (flag_name,))
        rule = cur.fetchone()
        if not rule:
            return jsonify({"error": "Regra nÃ£o encontrada"}), 404
        return jsonify(rule)
    except Exception as e:
        log.error(f"Erro ao buscar regra '{flag_name}': {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/rules/<string:flag_name>', methods=['PUT'])
@require_auth
def update_rule(flag_name):
    """ Atualiza a regra de segmentaÃ§Ã£o de uma flag """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Corpo da requisiÃ§Ã£o obrigatÃ³rio"}), 400

    set_clauses = []
    values = []
    
    if 'rules' in data:
        set_clauses.append(sql.SQL("rules = %s"))
        values.append(Json(data['rules']))
    if 'is_enabled' in data:
        set_clauses.append(sql.SQL("is_enabled = %s"))
        values.append(data['is_enabled'])
    
    if not set_clauses:
        return jsonify({"error": "Pelo menos um campo ('rules', 'is_enabled') Ã© obrigatÃ³rio"}), 400
    
    values.append(flag_name)

    query = sql.SQL("UPDATE targeting_rules SET {set_clause} WHERE flag_name = %s RETURNING *").format(
        set_clause=sql.SQL(", ").join(set_clauses)
    )
    
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, tuple(values))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Regra nÃ£o encontrada"}), 404
            
        updated_rule = cur.fetchone()
        conn.commit()
        log.info(f"Regra para '{flag_name}' atualizada com sucesso.")
        return jsonify(updated_rule), 200
    except Exception as e:
        if conn: conn.rollback()
        log.error(f"Erro ao atualizar regra '{flag_name}': {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

@app.route('/rules/<string:flag_name>', methods=['DELETE'])
@require_auth
def delete_rule(flag_name):
    """ Deleta a regra de segmentaÃ§Ã£o de uma flag """
    conn = None
    cur = None
    try:
        conn = pool.getconn()
        cur = conn.cursor()
        cur.execute("DELETE FROM targeting_rules WHERE flag_name = %s", (flag_name,))
        
        if cur.rowcount == 0:
            return jsonify({"error": "Regra nÃ£o encontrada"}), 404
            
        conn.commit()
        log.info(f"Regra para '{flag_name}' deletada com sucesso.")
        return "", 204
    except Exception as e:
        if conn: conn.rollback()
        log.error(f"Erro ao deletar regra '{flag_name}': {e}")
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: pool.putconn(conn)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8003))
    app.run(host='0.0.0.0', port=port, debug=False)  # nosec B104
