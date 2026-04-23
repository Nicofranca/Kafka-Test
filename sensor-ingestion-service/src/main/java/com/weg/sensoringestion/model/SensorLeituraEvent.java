package com.weg.sensoringestion.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.Instant;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class SensorLeituraEvent {
    private String sensorId;
    private String estacao;
    private String tipoMedicao; // temperatura | vibracao | corrente
    private double valor;
    private String unidade;
    private Instant timestamp;
}
