"""
Módulo que define a interface base para todas as estratégias de trading.

Este módulo fornece:
1. Interface base que todas as estratégias devem implementar
2. Estruturas de dados para sinais de trading
3. Enums para tipos de ordens e direções
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

class TipoOrdem(Enum):
    """Tipos de ordens disponíveis"""
    MERCADO = "mercado"
    LIMITE = "limite"
    STOP = "stop"
    STOP_LIMITE = "stop_limite"

class Direcao(Enum):
    """Direções possíveis para ordens"""
    COMPRA = "compra"
    VENDA = "venda"

@dataclass
class ConfiguracaoEstrategia:
    """
    Configuração base para estratégias.
    
    Atributos:
        nome: Nome da estratégia
        versao: Versão da estratégia
        timeframes: Lista de timeframes para análise
        parametros: Dicionário de parâmetros específicos
        stop_loss: Valor do stop loss em %
        take_profit: Valor do take profit em %
        capital_por_operacao: % do capital para cada operação
    """
    nome: str
    versao: str
    timeframes: List[str]
    parametros: Dict
    stop_loss: float
    take_profit: float
    capital_por_operacao: float

@dataclass
class SinalTrading:
    """
    Sinal de trading gerado pela estratégia.
    
    Atributos:
        ativo: Símbolo do ativo
        direcao: Direção da operação (compra/venda)
        tipo_ordem: Tipo de ordem a ser enviada
        preco_entrada: Preço de entrada desejado
        stop_loss: Preço do stop loss
        take_profit: Preço do take profit
        timeframe: Timeframe que gerou o sinal
        data_hora: Momento da geração do sinal
        confianca: Nível de confiança do sinal (0-1)
        metadados: Informações adicionais do sinal
    """
    ativo: str
    direcao: Direcao
    tipo_ordem: TipoOrdem
    preco_entrada: float
    stop_loss: float
    take_profit: float
    timeframe: str
    data_hora: datetime
    confianca: float
    metadados: Dict

class EstrategiaBase(ABC):
    """
    Classe base abstrata que define a interface que todas as 
    estratégias devem implementar.
    """
    
    def __init__(self, config: ConfiguracaoEstrategia):
        """
        Inicializa a estratégia com sua configuração.
        
        Args:
            config: Objeto de configuração da estratégia
        """
        self.config = config
        self.nome = config.nome
        self.versao = config.versao
        self.timeframes = config.timeframes
        self.parametros = config.parametros
        self._validar_configuracao()
    
    def _validar_configuracao(self):
        """Valida a configuração da estratégia"""
        if not self.config.nome:
            raise ValueError("Nome da estratégia é obrigatório")
        if not self.config.timeframes:
            raise ValueError("Pelo menos um timeframe deve ser especificado")
        if not 0 < self.config.stop_loss <= 100:
            raise ValueError("Stop loss deve estar entre 0 e 100%")
        if not 0 < self.config.take_profit <= 100:
            raise ValueError("Take profit deve estar entre 0 e 100%")
        if not 0 < self.config.capital_por_operacao <= 100:
            raise ValueError("Capital por operação deve estar entre 0 e 100%")
    
    @abstractmethod
    def analisar_mercado(
        self,
        dados: Dict[str, pd.DataFrame],
        ativo: str
    ) -> Optional[SinalTrading]:
        """
        Analisa o mercado e gera sinais de trading.
        
        Args:
            dados: Dicionário com DataFrames de dados por timeframe
            ativo: Símbolo do ativo sendo analisado
            
        Returns:
            Sinal de trading se houver oportunidade, None caso contrário
        """
        pass
    
    @abstractmethod
    def atualizar_parametros(self, resultados_backtest: Dict):
        """
        Atualiza parâmetros da estratégia baseado em resultados.
        
        Args:
            resultados_backtest: Resultados do backtest
        """
        pass
    
    @abstractmethod
    def calcular_confianca(
        self,
        dados: Dict[str, pd.DataFrame],
        ativo: str,
        direcao: Direcao
    ) -> float:
        """
        Calcula nível de confiança para uma direção.
        
        Args:
            dados: Dicionário com DataFrames de dados por timeframe
            ativo: Símbolo do ativo
            direcao: Direção a ser avaliada
            
        Returns:
            Nível de confiança entre 0 e 1
        """
        pass
    
    def validar_sinal(
        self,
        sinal: SinalTrading,
        dados: Dict[str, pd.DataFrame]
    ) -> bool:
        """
        Valida um sinal de trading antes de enviá-lo.
        
        Args:
            sinal: Sinal a ser validado
            dados: Dados de mercado atuais
            
        Returns:
            True se o sinal é válido, False caso contrário
        """
        # Valida preços
        if sinal.preco_entrada <= 0:
            return False
        if sinal.stop_loss <= 0:
            return False
        if sinal.take_profit <= 0:
            return False
        
        # Valida direção do stop e take
        if sinal.direcao == Direcao.COMPRA:
            if sinal.stop_loss >= sinal.preco_entrada:
                return False
            if sinal.take_profit <= sinal.preco_entrada:
                return False
        else:
            if sinal.stop_loss <= sinal.preco_entrada:
                return False
            if sinal.take_profit >= sinal.preco_entrada:
                return False
        
        # Valida confiança
        if not 0 <= sinal.confianca <= 1:
            return False
        
        return True
    
    def calcular_tamanho_posicao(
        self,
        capital: float,
        preco: float,
        risco_operacao: float = None
    ) -> float:
        """
        Calcula o tamanho da posição baseado no capital.
        
        Args:
            capital: Capital total disponível
            preco: Preço do ativo
            risco_operacao: % do capital a arriscar (opcional)
            
        Returns:
            Quantidade de unidades para a operação
        """
        if risco_operacao is None:
            risco_operacao = self.config.capital_por_operacao
        
        valor_operacao = capital * (risco_operacao / 100)
        return valor_operacao / preco