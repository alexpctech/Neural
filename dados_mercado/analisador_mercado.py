"""
Módulo de análise de mercado para identificação de níveis importantes,
extremos e condições seguras para operação.

Este módulo fornece ferramentas para:
1. Identificar topos e fundos
2. Avaliar força de níveis
3. Detectar zonas seguras para operação
4. Gerenciar stops protetivos
5. Analisar perfil de volume
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import numpy as np
import pandas as pd

class TipoExtremo(Enum):
    """Tipos de pontos extremos do mercado"""
    TOPO = "topo"
    FUNDO = "fundo"
    NENHUM = "nenhum"

@dataclass
class PontoExtremo:
    """
    Representa um ponto extremo do mercado (topo ou fundo)
    
    Atributos:
        preco: Preço do extremo
        data_hora: Momento em que o extremo foi formado
        tipo: Tipo do extremo (TOPO ou FUNDO)
        forca: Força do nível (0-1)
        confirmacoes: Número de confirmações do nível
        perfil_volume: Perfil de volume no extremo
        nivel_stop: Nível de stop protetor
    """
    preco: float
    data_hora: datetime
    tipo: TipoExtremo
    forca: float  # 0-1
    confirmacoes: int
    perfil_volume: float
    nivel_stop: float

class AnalisadorMercado:
    """
    Analisador de estrutura de mercado para identificação de níveis
    importantes e condições seguras para operação.
    """
    
    def __init__(
        self,
        periodos_analise: int = 20,
        peso_volume: float = 0.3,
        peso_momentum: float = 0.3,
        peso_padrao: float = 0.4
    ):
        """
        Inicializa o analisador de mercado.
        
        Args:
            periodos_analise: Número de períodos para análise
            peso_volume: Peso do volume na análise (0-1)
            peso_momentum: Peso do momentum na análise (0-1)
            peso_padrao: Peso do padrão de preço na análise (0-1)
        """
        self.periodos_analise = periodos_analise
        self.peso_volume = peso_volume
        self.peso_momentum = peso_momentum
        self.peso_padrao = peso_padrao
        self.pontos_extremos: Dict[str, List[PontoExtremo]] = {}
        self.estrutura_atual: Dict[str, Dict] = {}
    
    def analisar_estrutura_preco(
        self,
        ativo: str,
        dados: pd.DataFrame,
        forca_minima: float = 0.6
    ) -> Dict:
        """
        Analisa a estrutura de preços para identificar extremos.
        
        Args:
            ativo: Símbolo do ativo
            dados: DataFrame com OHLCV
            forca_minima: Força mínima para considerar um extremo (0-1)
            
        Returns:
            Dicionário com estrutura atual do mercado
        """
        # Inicializa estrutura para o ativo
        if ativo not in self.pontos_extremos:
            self.pontos_extremos[ativo] = []
        
        # Calcula indicadores
        maximas = dados['high'].rolling(self.periodos_analise).max()
        minimas = dados['low'].rolling(self.periodos_analise).min()
        volume = dados['volume'].rolling(self.periodos_analise).mean()
        
        # Identifica potenciais extremos
        extremos_potenciais = []
        for i in range(self.periodos_analise, len(dados)):
            janela = dados.iloc[i-self.periodos_analise:i+1]
            
            # Verifica topo
            if self._eh_topo_potencial(janela):
                forca = self._calcular_forca_extremo(janela, True)
                if forca >= forca_minima:
                    extremo = PontoExtremo(
                        preco=janela['high'].max(),
                        data_hora=janela.index[-1],
                        tipo=TipoExtremo.TOPO,
                        forca=forca,
                        confirmacoes=self._contar_confirmacoes(janela, True),
                        perfil_volume=self._calcular_perfil_volume(janela),
                        nivel_stop=self._calcular_nivel_stop(janela, True)
                    )
                    extremos_potenciais.append(extremo)
            
            # Verifica fundo
            elif self._eh_fundo_potencial(janela):
                forca = self._calcular_forca_extremo(janela, False)
                if forca >= forca_minima:
                    extremo = PontoExtremo(
                        preco=janela['low'].min(),
                        data_hora=janela.index[-1],
                        tipo=TipoExtremo.FUNDO,
                        forca=forca,
                        confirmacoes=self._contar_confirmacoes(janela, False),
                        perfil_volume=self._calcular_perfil_volume(janela),
                        nivel_stop=self._calcular_nivel_stop(janela, False)
                    )
                    extremos_potenciais.append(extremo)
        
        # Atualiza lista de extremos
        self.pontos_extremos[ativo].extend(extremos_potenciais)
        
        # Remove extremos antigos ou invalidados
        self._limpar_extremos(ativo, dados)
        
        # Atualiza estrutura atual
        preco_atual = dados['close'].iloc[-1]
        self.estrutura_atual[ativo] = {
            'preco_atual': preco_atual,
            'topo_proximo': self._encontrar_extremo_proximo(ativo, preco_atual, TipoExtremo.TOPO),
            'fundo_proximo': self._encontrar_extremo_proximo(ativo, preco_atual, TipoExtremo.FUNDO),
            'proximo_extremo': self._esta_proximo_extremo(ativo, preco_atual),
            'zonas_entrada': self._calcular_zonas_entrada_segura(ativo, preco_atual)
        }
        
        return self.estrutura_atual[ativo]
    
    def _eh_topo_potencial(self, janela: pd.DataFrame) -> bool:
        """
        Verifica se uma janela contém um potencial topo.
        
        Args:
            janela: DataFrame com dados da janela de análise
            
        Returns:
            True se for um potencial topo, False caso contrário
        """
        ponto_medio = len(janela) // 2
        janela_esquerda = janela.iloc[:ponto_medio]
        janela_direita = janela.iloc[ponto_medio:]
        
        pico = janela['high'].max()
        
        # Verifica padrão de topo
        maior_que_antes = pico > janela_esquerda['high'].max()
        maior_que_depois = pico > janela_direita['high'].max()
        
        # Verifica momentum
        momentum = self._calcular_momentum(janela)
        
        return maior_que_antes and maior_que_depois and momentum < 0
    
    def _eh_fundo_potencial(self, janela: pd.DataFrame) -> bool:
        """
        Verifica se uma janela contém um potencial fundo.
        
        Args:
            janela: DataFrame com dados da janela de análise
            
        Returns:
            True se for um potencial fundo, False caso contrário
        """
        ponto_medio = len(janela) // 2
        janela_esquerda = janela.iloc[:ponto_medio]
        janela_direita = janela.iloc[ponto_medio:]
        
        fundo = janela['low'].min()
        
        # Verifica padrão de fundo
        menor_que_antes = fundo < janela_esquerda['low'].min()
        menor_que_depois = fundo < janela_direita['low'].min()
        
        # Verifica momentum
        momentum = self._calcular_momentum(janela)
        
        return menor_que_antes and menor_que_depois and momentum > 0
    
    def _calcular_momentum(self, janela: pd.DataFrame) -> float:
        """
        Calcula o momentum da janela.
        
        Args:
            janela: DataFrame com dados da janela de análise
            
        Returns:
            Valor do momentum normalizado
        """
        retornos = janela['close'].pct_change()
        return retornos.mean() / retornos.std() if retornos.std() != 0 else 0
    
    def _calcular_forca_extremo(self, janela: pd.DataFrame, eh_topo: bool) -> float:
        """
        Calcula força de um extremo baseado em múltiplos fatores.
        
        Args:
            janela: DataFrame com dados da janela de análise
            eh_topo: True se for topo, False se for fundo
            
        Returns:
            Força do extremo (0-1)
        """
        # Score de volume
        score_volume = janela['volume'].iloc[-1] / janela['volume'].mean()
        score_volume = min(score_volume / 2, 1)  # Normaliza, max 2x média
        
        # Score de momentum
        momentum = abs(self._calcular_momentum(janela))
        score_momentum = min(momentum, 1)
        
        # Score de padrão de preço
        if eh_topo:
            score_padrao = self._calcular_forca_padrao_topo(janela)
        else:
            score_padrao = self._calcular_forca_padrao_fundo(janela)
        
        # Combina scores com pesos
        return (
            score_volume * self.peso_volume +
            score_momentum * self.peso_momentum +
            score_padrao * self.peso_padrao
        )
    
    def _calcular_forca_padrao_topo(self, janela: pd.DataFrame) -> float:
        """
        Calcula força do padrão de topo.
        
        Args:
            janela: DataFrame com dados da janela de análise
            
        Returns:
            Força do padrão (0-1)
        """
        maxima = janela['high'].max()
        fechamento = janela['close'].iloc[-1]
        tamanho_corpo = abs(janela['open'] - janela['close']).mean()
        
        # Verifica rejeição de preços mais altos
        rejeicao = (maxima - fechamento) / tamanho_corpo
        score_rejeicao = min(rejeicao / 2, 1)
        
        # Verifica volume decrescente
        tendencia_volume = np.corrcoef(range(len(janela)), janela['volume'])[0,1]
        score_volume = 1 - max(tendencia_volume, 0)  # Volume decrescente é bom para topos
        
        return (score_rejeicao * 0.7 + score_volume * 0.3)
    
    def _calcular_forca_padrao_fundo(self, janela: pd.DataFrame) -> float:
        """
        Calcula força do padrão de fundo.
        
        Args:
            janela: DataFrame com dados da janela de análise
            
        Returns:
            Força do padrão (0-1)
        """
        minima = janela['low'].min()
        fechamento = janela['close'].iloc[-1]
        tamanho_corpo = abs(janela['open'] - janela['close']).mean()
        
        # Verifica rejeição de preços mais baixos
        rejeicao = (fechamento - minima) / tamanho_corpo
        score_rejeicao = min(rejeicao / 2, 1)
        
        # Verifica volume crescente
        tendencia_volume = np.corrcoef(range(len(janela)), janela['volume'])[0,1]
        score_volume = max(tendencia_volume, 0)  # Volume crescente é bom para fundos
        
        return (score_rejeicao * 0.7 + score_volume * 0.3)
    
    def _calcular_perfil_volume(self, janela: pd.DataFrame) -> float:
        """
        Calcula perfil de volume do extremo.
        
        Args:
            janela: DataFrame com dados da janela de análise
            
        Returns:
            Relação do volume atual com a média
        """
        media_movel_volume = janela['volume'].rolling(5).mean()
        return media_movel_volume.iloc[-1] / media_movel_volume.mean()
    
    def _calcular_nivel_stop(self, janela: pd.DataFrame, eh_topo: bool) -> float:
        """
        Calcula nível de stop protetor.
        
        Args:
            janela: DataFrame com dados da janela de análise
            eh_topo: True se for topo, False se for fundo
            
        Returns:
            Nível de preço para stop
        """
        atr = self._calcular_atr(janela)
        
        if eh_topo:
            # Para topos, stop acima do topo
            return janela['high'].max() + (atr * 1.5)
        else:
            # Para fundos, stop abaixo do fundo
            return janela['low'].min() - (atr * 1.5)
    
    def _calcular_atr(self, janela: pd.DataFrame, periodo: int = 14) -> float:
        """
        Calcula Average True Range.
        
        Args:
            janela: DataFrame com dados da janela de análise
            periodo: Período para cálculo do ATR
            
        Returns:
            Valor do ATR
        """
        maximas = janela['high']
        minimas = janela['low']
        fechamentos = janela['close']
        
        tr1 = maximas - minimas
        tr2 = abs(maximas - fechamentos.shift(1))
        tr3 = abs(minimas - fechamentos.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(periodo).mean().iloc[-1]
    
    def eh_seguro_operar(
        self,
        ativo: str,
        preco_atual: float,
        direcao: str,
        exigir_stop: bool = True
    ) -> Tuple[bool, str, Optional[float]]:
        """
        Verifica se é seguro operar na direção especificada.
        
        Args:
            ativo: Símbolo do ativo
            preco_atual: Preço atual
            direcao: 'compra' ou 'venda'
            exigir_stop: Se True, só permite operação com stop protegido
            
        Returns:
            (é_seguro, razão, stop_sugerido)
        """
        if ativo not in self.estrutura_atual:
            return False, "Estrutura de mercado não analisada", None
        
        estrutura = self.estrutura_atual[ativo]
        
        # Verifica proximidade com extremos
        if estrutura['proximo_extremo']:
            return False, "Preço muito próximo de extremo", None
        
        # Verifica zonas seguras
        zonas_seguras = estrutura['zonas_entrada']
        if direcao.lower() == 'compra':
            zonas = zonas_seguras['zonas_compra']
            extremo_proximo = estrutura['fundo_proximo']
        else:
            zonas = zonas_seguras['zonas_venda']
            extremo_proximo = estrutura['topo_proximo']
        
        # Verifica se preço está em zona segura
        em_zona_segura = any(
            minimo <= preco_atual <= maximo
            for minimo, maximo in zonas
        )
        
        if not em_zona_segura:
            return False, "Preço fora da zona segura de operação", None
        
        # Se precisar de stop, verifica se há stop protegido disponível
        if exigir_stop and extremo_proximo:
            nivel_stop = extremo_proximo.nivel_stop
            if direcao.lower() == 'compra' and nivel_stop >= preco_atual:
                return False, "Stop acima do preço de compra", None
            elif direcao.lower() == 'venda' and nivel_stop <= preco_atual:
                return False, "Stop abaixo do preço de venda", None
            return True, "Operação segura com stop protegido", nivel_stop
        
        return True, "Operação em zona segura", None