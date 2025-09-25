"""
Definições de tipos e enums para o sistema de gerenciamento de GPU.

Este módulo contém todas as definições de tipos, enums e constantes
utilizadas pelo sistema de gerenciamento de GPU.

Classes:
    PerformanceMode: Enum para os modos de gerenciamento de performance
    
Constantes:
    DEFAULT_TARGET_TEMP: Temperatura alvo padrão para o modo AUTO
    MIN_PERFORMANCE: Nível mínimo de performance no modo AUTO
    ADJUSTMENT_INTERVAL: Intervalo de ajuste no modo AUTO
"""

from enum import Enum
from typing import TypedDict, Dict, Optional

class PerformanceMode(Enum):
    """Modos de gerenciamento de performance da GPU."""
    MANUAL = "manual"  # Controle manual de performance
    AUTO = "auto"    # Ajuste automático baseado em uso e temperatura

class GPUStats(TypedDict):
    """Tipo para estatísticas da GPU."""
    gpu: str                    # Nome/Modelo da GPU
    modo: str                   # Modo atual (AUTO/MANUAL)
    compute_capability: str     # Versão da Compute Capability
    cuda_cores: int            # Total de CUDA cores
    cuda_cores_ativos: int     # CUDA cores em uso
    memoria_total_mb: float    # Memória total em MB
    memoria_usada_mb: float    # Memória em uso em MB
    memoria_livre_mb: float    # Memória livre em MB
    temperatura_c: int         # Temperatura em Celsius
    clock_mhz: int            # Clock em MHz
    uso_gpu_percent: float    # Porcentagem de uso da GPU
    uso_memoria_percent: float # Porcentagem de uso da memória
    consumo_energia_w: float  # Consumo em Watts
    nivel_desempenho: int     # Nível atual de desempenho (%)

# Constantes de configuração
DEFAULT_TARGET_TEMP = 75    # Temperatura alvo em Celsius
MIN_PERFORMANCE = 30        # Mínimo de performance em modo AUTO (%)
ADJUSTMENT_INTERVAL = 2.0   # Intervalo de ajuste em segundos