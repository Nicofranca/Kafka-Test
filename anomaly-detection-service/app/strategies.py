from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
import numpy as np

@dataclass
class ResultadoDeteccao:
    anomalia: bool
    tipo: str
    threshold: float
    severidade: str  # CRITICA | ALTA | MEDIA

class EstrategiaDeteccao(ABC):
    """Interface base para todas as estratégias — Strategy Pattern"""
    @abstractmethod
    def detectar(self, sensor_id: str, valor: float) -> ResultadoDeteccao:
        pass

class ThresholdStrategy(EstrategiaDeteccao):
    """Detecta anomalia quando valor ultrapassa limite fixo"""
    LIMITES = {
        'temperatura': {'min': 0, 'max': 90, 'critico': 100},
        'vibracao': {'min': 0, 'max': 15, 'critico': 25},
        'corrente': {'min': 0, 'max': 120, 'critico': 150},
    }

    def detectar(self, sensor_id: str, valor: float) -> ResultadoDeteccao:
        tipo = self._inferir_tipo(sensor_id)
        limites = self.LIMITES.get(tipo, {'min': -999, 'max': 999, 'critico': 9999})
        
        if valor >= limites['critico']:
            return ResultadoDeteccao(True, 'THRESHOLD_CRITICO', limites['critico'], 'CRITICA')
        
        if valor > limites['max']:
            return ResultadoDeteccao(True, 'THRESHOLD_ALTO', limites['max'], 'ALTA')
        
        return ResultadoDeteccao(False, '', 0, '')

    def _inferir_tipo(self, sensor_id: str) -> str:
        sid = sensor_id.upper()
        if 'TEMP' in sid: return 'temperatura'
        if 'VIB' in sid: return 'vibracao'
        if 'CORR' in sid: return 'corrente'
        return 'desconhecido'

class ZScoreStrategy(EstrategiaDeteccao):
    """Detecta anomalia estatística usando Z-Score"""
    def __init__(self, janela: int = 60, limiar: float = 3.0):
        self.janela = janela
        self.limiar = limiar
        self.historico = {}  # sensorId -> deque de valores

    def detectar(self, sensor_id: str, valor: float) -> ResultadoDeteccao:
        if sensor_id not in self.historico:
            self.historico[sensor_id] = deque(maxlen=self.janela)
        
        hist = self.historico[sensor_id]
        hist.append(valor)

        # Precisa de pelo menos 10 pontos para calcular estatística
        if len(hist) < 10:
            return ResultadoDeteccao(False, '', 0, '')

        media = np.mean(hist)
        desvio = np.std(hist)

        if desvio == 0:
            return ResultadoDeteccao(False, '', 0, '')

        z = abs((valor - media) / desvio)

        if z > self.limiar * 1.5:
            return ResultadoDeteccao(
                True, 'ZSCORE_ANOMALIA', 
                round(media + self.limiar * desvio, 2), 
                'ALTA'
            )
        
        if z > self.limiar:
            return ResultadoDeteccao(
                True, 'ZSCORE_ANOMALIA', 
                round(media + self.limiar * desvio, 2), 
                'MEDIA'
            )
        
        return ResultadoDeteccao(False, '', 0, '')