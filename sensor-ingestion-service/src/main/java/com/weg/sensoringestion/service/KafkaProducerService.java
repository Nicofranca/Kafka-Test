package com.weg.sensoringestion.service;

import com.weg.sensoringestion.model.SensorLeituraEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class KafkaProducerService {
    private final KafkaTemplate<String, SensorLeituraEvent> kafkaTemplate;

    @Value("${topics.sensor-leitura}")
    private String topico;

    public void publicarLeitura(SensorLeituraEvent evento) {
    // A chave é o sensorId — garante que leituras do mesmo sensor
    // sempre vão para a mesma partição (preservando ordem)
        kafkaTemplate.send(topico, evento.getSensorId(), evento)
        .whenComplete((result, ex) -> {
            
            if (ex != null) {

                log.error("ERRO ao publicar leitura do sensor {}: {}",

                evento.getSensorId(), ex.getMessage());

            } else {

                log.info("Leitura publicada — sensor: {} | partição: {} | offset: {}",

                evento.getSensorId(),
                result.getRecordMetadata().partition(),
                result.getRecordMetadata().offset());

            }
        });
    }
}
