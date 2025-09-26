"""
Módulo de Análise Técnica - Sistema Neural Trading
"""

from .indicadores_tecnicos import AnalisisTecnica, IndicadorResult
from .detector_padroes import DetectorPadroes, PadraoDetectado, TipoPadrao
from .backtest_engine import BacktestEngine, HistoricoBacktest, Posicao

__all__ = [
    'AnalisisTecnica', 
    'IndicadorResult',
    'DetectorPadroes', 
    'PadraoDetectado', 
    'TipoPadrao',
    'BacktestEngine', 
    'HistoricoBacktest', 
    'Posicao'
]