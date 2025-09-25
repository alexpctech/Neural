import random
from typing import Dict, List
from datetime import datetime


class AgenteTecnicoV4:
    """Agente técnico mínimo extraído do monólito para modularização."""

    def __init__(self):
        self.indicadores = ['RSI', 'MACD', 'BB']

    def analisar_indicadores_completos(self, dados_mercado: Dict) -> Dict:
        resultados = {}
        for simbolo, dados in dados_mercado.items():
            rsi = self._calcular_rsi(dados)
            macd = self._calcular_macd(dados)
            resultados[simbolo] = {
                'RSI': rsi,
                'MACD': macd,
                'score_tecnico': (rsi['valor'] / 100) + (macd['histogram'] * 0.1),
                'timestamp': datetime.now().isoformat()
            }
        return resultados

    def _calcular_rsi(self, dados: Dict, periodo: int = 14) -> Dict:
        valor = random.uniform(20, 80)
        return {'valor': valor, 'sinal': 'SOBRECOMPRADO' if valor > 70 else 'SOBREVENDIDO' if valor < 30 else 'NEUTRO'}

    def _calcular_macd(self, dados: Dict) -> Dict:
        macd_line = random.uniform(-2, 2)
        signal_line = random.uniform(-2, 2)
        histogram = macd_line - signal_line
        return {'macd_line': macd_line, 'signal_line': signal_line, 'histogram': histogram}
