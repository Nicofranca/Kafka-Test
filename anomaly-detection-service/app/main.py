import faust
from dataclasses import dataclass
from datetime import datetime, timezone
from strategies import ThresholdStrategy, ZScoreStrategy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Modelos de eventos ──────────────────────────────────────────
class SensorLeituraEvent(faust.Record, serializer='json'):
    sensorId: str
    estacao: str
    tipoMedicao: str
    valor: float
    unidade: str
    timestamp: str = ''

class AnomaliaDetectadaEvent(faust.Record, serializer='json'):
    sensorId: str
    estacao: str
    tipoAnomalia: str
    valorDetectado: float
    threshold: float
    severidade: str
    timestamp: str

# ── Aplicação Faust ─────────────────────────────────────────────
app = faust.App(
    'anomaly-detection',
    broker='kafka://localhost:9094',
    value_serializer='json',
)

topico_leituras = app.topic('producao.sensor.leitura', value_type=SensorLeituraEvent)
topico_anomalias = app.topic('producao.anomalia.detectada', value_type=AnomaliaDetectadaEvent)

# ── Estratégias plugáveis (Strategy Pattern) ────────────────────
estrategia_threshold = ThresholdStrategy()
estrategia_zscore = ZScoreStrategy(janela=60, limiar=3.0)

# ── Agent: processa cada leitura ────────────────────────────────
@app.agent(topico_leituras)
async def processar_leitura(stream):
    async for evento in stream:
        try:
            # Executa ambas as estratégias
            resultado_t = estrategia_threshold.detectar(evento.sensorId, evento.valor)
            resultado_z = estrategia_zscore.detectar(evento.sensorId, evento.valor)

            # Usa o resultado mais grave (Prioriza Threshold se ambos detectarem)
            resultado = resultado_t if resultado_t.anomalia else resultado_z

            if resultado.anomalia:
                anomalia = AnomaliaDetectadaEvent(
                    sensorId=evento.sensorId,
                    estacao=evento.estacao,
                    tipoAnomalia=resultado.tipo,
                    valorDetectado=evento.valor,
                    threshold=resultado.threshold,
                    severidade=resultado.severidade,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                
                await topico_anomalias.send(key=evento.sensorId, value=anomalia)
                logger.warning(f"ANOMALIA [{resultado.severidade}] sensor={evento.sensorId} valor={evento.valor}")
            else:
                logger.debug(f"OK sensor={evento.sensorId} valor={evento.valor}")
                
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}")

if __name__ == '__main__':
    app.main()