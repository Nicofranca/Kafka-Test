import json
import logging
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer, KafkaException
from .strategies import ThresholdStrategy, ZScoreStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do Kafka
KAFKA_CONF = {'bootstrap.servers': 'localhost:9094'}
TOPICO_LEITURA = 'producao.sensor.leitura'
TOPICO_ANOMALIA = 'producao.anomalia.detectada'

# Inicializa as estratégias
estrategia_threshold = ThresholdStrategy()
estrategia_zscore = ZScoreStrategy(janela=60, limiar=3.0)

def processar_mensagem():
    # Configuração do Consumidor
    consumer = Consumer({
        **KAFKA_CONF,
        'group.id': 'anomaly-detector-group',
        'auto.offset.reset': 'earliest'
    })
    
    # Configuração do Produtor
    producer = Producer(KAFKA_CONF)
    
    consumer.subscribe([TOPICO_LEITURA])
    logger.info(f"Monitorando tópico {TOPICO_LEITURA}...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                logger.error(f"Erro no Kafka: {msg.error()}")
                continue

            # 1. Parse do JSON recebido do Spring Boot
            dados = json.loads(msg.value().decode('utf-8'))
            sensor_id = dados.get('sensorId')
            valor = dados.get('valor')

            # 2. Executa as estratégias
            res_t = estrategia_threshold.detectar(sensor_id, valor)
            res_z = estrategia_zscore.detectar(sensor_id, valor)
            resultado = res_t if res_t.anomalia else res_z

            # 3. Se for anomalia, envia para o novo tópico
            if resultado.anomalia:
                anomalia_event = {
                    "sensorId": sensor_id,
                    "estacao": dados.get('estacao'),
                    "tipoAnomalia": resultado.tipo,
                    "valorDetectado": valor,
                    "threshold": resultado.threshold,
                    "severidade": resultado.severidade,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                producer.produce(
                    TOPICO_ANOMALIA, 
                    key=sensor_id, 
                    value=json.dumps(anomalia_event).encode('utf-8')
                )
                producer.flush()
                logger.warning(f"🔥 ANOMALIA DETECTADA: {sensor_id} - {resultado.tipo}")
            else:
                logger.info(f"✅ Leitura OK: {sensor_id} = {valor}")

    except KeyboardInterrupt:
        logger.info("Encerrando...")
    finally:
        consumer.close()

if __name__ == '__main__':
    processar_mensagem()