"""
Exemplo de estratégia implementada como um agente especializado.
"""

from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from datetime import datetime
import torch

from .agente_padrao import AgentePadrao

class AgenteMediaMovel(AgentePadrao):
    """
    Agente que implementa estratégia de médias móveis.
    Herda de AgentePadrao para combinar funcionalidades.
    """
    
    def __init__(
        self,
        name: str = "AgenteMediaMovel",
        gpu_device: Optional[torch.device] = None
    ):
        """
        Inicializa o agente com configuração específica.
        
        Args:
            name: Nome do agente
            gpu_device: Dispositivo GPU opcional
        """
        config = {
            'timeframes': ['1h', '4h', '1d'],
            'stop_loss': 2.0,
            'take_profit': 4.0,
            'capital_por_operacao': 1.0,
            'parametros': {
                'periodo_media_curta': 9,
                'periodo_media_longa': 21,
                'periodo_rsi': 14,
                'sobrevenda_rsi': 30,
                'sobrecompra_rsi': 70
            }
        }
        super().__init__(name, config, gpu_device)
    
    def _analisar_timeframe(
        self,
        dados: pd.DataFrame,
        timeframe: str
    ) -> Optional[Dict]:
        """
        Analisa um timeframe específico usando médias móveis.
        
        Args:
            dados: DataFrame com dados do timeframe
            timeframe: Timeframe sendo analisado
            
        Returns:
            Dicionário com análise ou None
        """
        try:
            # Calcula indicadores
            media_curta = dados['close'].rolling(
                self.config['parametros']['periodo_media_curta']
            ).mean()
            
            media_longa = dados['close'].rolling(
                self.config['parametros']['periodo_media_longa']
            ).mean()
            
            rsi = self._calcular_rsi(
                dados['close'],
                self.config['parametros']['periodo_rsi']
            )
            
            # Verifica cruzamentos
            cruzamento_alta = (
                media_curta.iloc[-1] > media_longa.iloc[-1] and
                media_curta.iloc[-2] <= media_longa.iloc[-2]
            )
            
            cruzamento_baixa = (
                media_curta.iloc[-1] < media_longa.iloc[-1] and
                media_curta.iloc[-2] >= media_longa.iloc[-2]
            )
            
            # Calcula confiança baseada no RSI
            if cruzamento_alta:
                confianca = max(0, (self.config['parametros']['sobrevenda_rsi'] - rsi.iloc[-1]) / 30)
                tipo_sinal = 'COMPRA'
            elif cruzamento_baixa:
                confianca = max(0, (rsi.iloc[-1] - self.config['parametros']['sobrecompra_rsi']) / 30)
                tipo_sinal = 'VENDA'
            else:
                return None
            
            # Retorna análise
            return {
                'tipo': tipo_sinal,
                'confianca': confianca,
                'indicadores': {
                    'media_curta': media_curta.iloc[-1],
                    'media_longa': media_longa.iloc[-1],
                    'rsi': rsi.iloc[-1]
                },
                'preco': dados['close'].iloc[-1],
                'volume': dados['volume'].iloc[-1],
                'timestamp': dados.index[-1]
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar timeframe {timeframe}: {str(e)}")
            return None
    
    def _combinar_analises(
        self,
        analises: Dict[str, Dict]
    ) -> Optional[Dict]:
        """
        Combina análises de diferentes timeframes.
        
        Args:
            analises: Dicionário com análises por timeframe
            
        Returns:
            Sinal combinado ou None
        """
        if not analises:
            return None
            
        # Pesos por timeframe
        pesos = {
            '1h': 0.2,
            '4h': 0.3,
            '1d': 0.5
        }
        
        # Agrupa sinais por tipo
        sinais_compra = {}
        sinais_venda = {}
        
        for timeframe, analise in analises.items():
            if analise['tipo'] == 'COMPRA':
                sinais_compra[timeframe] = analise
            else:
                sinais_venda[timeframe] = analise
        
        # Verifica conflitos
        if sinais_compra and sinais_venda:
            # Se houver sinais mistos, usa o timeframe maior
            timeframes_compra = set(sinais_compra.keys())
            timeframes_venda = set(sinais_venda.keys())
            
            if '1d' in timeframes_compra:
                sinais = sinais_compra
            elif '1d' in timeframes_venda:
                sinais = sinais_venda
            elif '4h' in timeframes_compra:
                sinais = sinais_compra
            elif '4h' in timeframes_venda:
                sinais = sinais_venda
            else:
                # Em caso de dúvida, não opera
                return None
        else:
            sinais = sinais_compra or sinais_venda
        
        if not sinais:
            return None
        
        # Calcula confiança média ponderada
        confianca_total = 0
        peso_total = 0
        
        for timeframe, analise in sinais.items():
            if timeframe in pesos:
                peso = pesos[timeframe]
                confianca_total += analise['confianca'] * peso
                peso_total += peso
        
        if peso_total == 0:
            return None
            
        confianca_media = confianca_total / peso_total
        
        # Pega primeiro sinal como base
        primeiro_sinal = list(sinais.values())[0]
        
        # Retorna sinal combinado
        return {
            'tipo': primeiro_sinal['tipo'],
            'confianca': confianca_media,
            'parametros': {
                'preco_entrada': primeiro_sinal['preco'],
                'stop_loss': self._calcular_stop_loss(
                    primeiro_sinal['preco'],
                    primeiro_sinal['tipo']
                ),
                'take_profit': self._calcular_take_profit(
                    primeiro_sinal['preco'],
                    primeiro_sinal['tipo']
                )
            }
        }
    
    def _calcular_rsi(
        self,
        precos: pd.Series,
        periodo: int
    ) -> pd.Series:
        """
        Calcula o RSI (Relative Strength Index).
        
        Args:
            precos: Série de preços
            periodo: Período para cálculo
            
        Returns:
            Série com valores do RSI
        """
        delta = precos.diff()
        
        ganhos = delta.copy()
        perdas = delta.copy()
        
        ganhos[ganhos < 0] = 0
        perdas[perdas > 0] = 0
        perdas = abs(perdas)
        
        media_ganhos = ganhos.rolling(window=periodo).mean()
        media_perdas = perdas.rolling(window=periodo).mean()
        
        rs = media_ganhos / media_perdas
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calcular_stop_loss(
        self,
        preco: float,
        tipo_ordem: str
    ) -> float:
        """
        Calcula nível de stop loss.
        
        Args:
            preco: Preço de entrada
            tipo_ordem: Tipo da ordem (COMPRA/VENDA)
            
        Returns:
            Preço do stop loss
        """
        if tipo_ordem == 'COMPRA':
            return preco * (1 - self.stop_loss/100)
        else:
            return preco * (1 + self.stop_loss/100)
    
    def _calcular_take_profit(
        self,
        preco: float,
        tipo_ordem: str
    ) -> float:
        """
        Calcula nível de take profit.
        
        Args:
            preco: Preço de entrada
            tipo_ordem: Tipo da ordem (COMPRA/VENDA)
            
        Returns:
            Preço do take profit
        """
        if tipo_ordem == 'COMPRA':
            return preco * (1 + self.take_profit/100)
        else:
            return preco * (1 - self.take_profit/100)
    
    def handle_feedback(self, message: Dict[str, Any]) -> None:
        """
        Processa feedback sobre sinais anteriores.
        
        Args:
            message: Mensagem com feedback
        """
        if 'resultado' not in message:
            return
            
        # Ajusta parâmetros baseado no feedback
        if message['resultado'] == 'sucesso':
            # Mantém parâmetros atuais
            pass
        elif message['resultado'] == 'falha':
            # Torna mais conservador
            self.config['parametros']['periodo_media_curta'] += 1
            self.config['parametros']['periodo_media_longa'] += 2
            
            # Ajusta níveis de RSI
            self.config['parametros']['sobrevenda_rsi'] = max(
                20,
                self.config['parametros']['sobrevenda_rsi'] - 5
            )
            self.config['parametros']['sobrecompra_rsi'] = min(
                80,
                self.config['parametros']['sobrecompra_rsi'] + 5
            )