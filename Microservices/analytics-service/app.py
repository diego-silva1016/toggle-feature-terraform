import os
import sys
import threading
import json
import uuid
import time
import logging
from urllib.parse import urlparse
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from flask import Flask, jsonify
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")

SQS_QUEUE_URL = os.getenv("AWS_SQS_URL")
DYNAMODB_TABLE_NAME = os.getenv("AWS_DYNAMODB_TABLE")
SQS_ENDPOINT_URL = os.getenv("AWS_SQS_ENDPOINT")
DYNAMODB_ENDPOINT_URL = os.getenv("AWS_DYNAMODB_ENDPOINT")

if not all([AWS_REGION, SQS_QUEUE_URL, DYNAMODB_TABLE_NAME]):
    log.critical("Erro: AWS_REGION, AWS_SQS_URL, e AWS_DYNAMODB_TABLE devem ser definidos.")
    sys.exit(1)

try:
    session = boto3.Session(
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )
    sqs_client = session.client("sqs", endpoint_url=SQS_ENDPOINT_URL)
    dynamodb_client = session.client("dynamodb", endpoint_url=DYNAMODB_ENDPOINT_URL)
    log.info(f"Clientes Boto3 inicializados na regiÃ£o {AWS_REGION}")
    if SQS_ENDPOINT_URL:
        log.info(f"SQS endpoint local configurado: {SQS_ENDPOINT_URL}")
    if DYNAMODB_ENDPOINT_URL:
        log.info(f"DynamoDB endpoint local configurado: {DYNAMODB_ENDPOINT_URL}")
except NoCredentialsError:
    log.critical("Credenciais da AWS nÃ£o encontradas. Verifique seu ambiente.")
    sys.exit(1)
except Exception as e:
    log.critical(f"Erro ao inicializar o Boto3: {e}")
    sys.exit(1)


def ensure_sqs_queue_exists(queue_url):
    """Garante que a fila exista no broker local e retorna a QueueUrl efetiva."""
    queue_name = urlparse(queue_url).path.rsplit('/', 1)[-1].strip()
    if not queue_name:
        log.critical(f"URL da fila SQS invÃ¡lida: {queue_url}")
        sys.exit(1)

    try:
        sqs_client.create_queue(QueueName=queue_name)
        resolved_queue_url = sqs_client.get_queue_url(QueueName=queue_name)["QueueUrl"]
        log.info(f"Fila SQS pronta para uso: {resolved_queue_url}")
        return resolved_queue_url
    except ClientError as e:
        log.critical(f"NÃ£o foi possÃ­vel garantir a fila SQS '{queue_name}': {e}")
        sys.exit(1)


SQS_QUEUE_URL = ensure_sqs_queue_exists(SQS_QUEUE_URL)



def process_message(message):
    """ Processa uma Ãºnica mensagem SQS e a insere no DynamoDB """
    try:
        log.info(f"Processando mensagem ID: {message['MessageId']}")
        body = json.loads(message['Body'])
        
        event_id = str(uuid.uuid4())
        
        item = {
            'event_id': {'S': event_id},
            'user_id': {'S': body['user_id']},
            'flag_name': {'S': body['flag_name']},
            'result': {'BOOL': body['result']},
            'timestamp': {'S': body['timestamp']}
        }
        
        dynamodb_client.put_item(
            TableName=DYNAMODB_TABLE_NAME,
            Item=item
        )
        
        log.info(f"Evento {event_id} (Flag: {body['flag_name']}) salvo no DynamoDB.")
        
        sqs_client.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=message['ReceiptHandle']
        )
        
    except json.JSONDecodeError:
        log.error(f"Erro ao decodificar JSON da mensagem ID: {message['MessageId']}")
    except ClientError as e:
        log.error(f"Erro do Boto3 (DynamoDB ou SQS) ao processar {message['MessageId']}: {e}")
    except Exception as e:
        log.error(f"Erro inesperado ao processar {message['MessageId']}: {e}")

def sqs_worker_loop():
    """ Loop principal do worker que ouve a fila SQS """
    log.info("Iniciando o worker SQS...")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
            
            messages = response.get('Messages', [])
            if not messages:
                continue
                
            log.info(f"Recebidas {len(messages)} mensagens.")
            
            for message in messages:
                process_message(message)
                
        except ClientError as e:
            log.error(f"Erro do Boto3 no loop principal do SQS: {e}")
            time.sleep(10)
        except Exception as e:
            log.error(f"Erro inesperado no loop principal do SQS: {e}")
            time.sleep(10)


app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})


def start_worker():
    """ Inicia o worker SQS em uma thread separada """
    worker_thread = threading.Thread(target=sqs_worker_loop, daemon=True)
    worker_thread.start()

start_worker()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8005))
    app.run(host='0.0.0.0', port=port, debug=False)  # nosec B104
