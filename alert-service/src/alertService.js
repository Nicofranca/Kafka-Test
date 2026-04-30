const { Kafka, logLevel } = require('kafkajs');
const winston = require('winston');
// ── Logger ───────────────────────────────────────────────────────
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.printf(({ timestamp, level, message }) =>
            `[${timestamp}] ${level.toUpperCase()}: ${message}`
        )
    ),
    transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'alertas.log' })
    ]
});
// ── Kafka ────────────────────────────────────────────────────────
const kafka = new Kafka({
    clientId: 'alert-service',
    brokers: ['localhost:9094'],
    retry: { retries: 5 }
});
const consumer = kafka.consumer({ groupId: 'alert-service-group' });
// ── Lógica de alerta por severidade ──────────────────────────────
function processarAlerta(evento) {
    const emoji = { CRITICA: '🚨', ALTA: '⚠️', MEDIA: '📊' }[evento.severidade] || '❓';
    const msg = `${emoji} ALERTA ${evento.severidade} | Sensor: ${evento.sensorId} | ` +
        `Estação: ${evento.estacao} | Valor: ${evento.valorDetectado} | ` +
        `Tipo: ${evento.tipoAnomalia} | Threshold: ${evento.threshold}`;
    if (evento.severidade === 'CRITICA') {
        logger.error(msg);
        // TODO: enviar e-mail, SMS, acionar CLP de parada
    } else if (evento.severidade === 'ALTA') {
        logger.warn(msg);
        // TODO: notificar supervisor via push notification
    } else {
        logger.info(msg);
    }
}
// ── Main ─────────────────────────────────────────────────────────
async function iniciar() {
    await consumer.connect();
    logger.info('Alert Service conectado ao Kafka');
    await consumer.subscribe({
        topic: 'producao.anomalia.detectada',
        fromBeginning: false
    });
    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            try {
                const evento = JSON.parse(message.value.toString());
                processarAlerta(evento);
            } catch (err) {
                logger.error(`Erro ao processar mensagem: ${err.message}`);
            }
        }
    });
}
iniciar().catch(err => {
    logger.error(`Falha fatal: ${err.message}`);
    process.exit(1);
});