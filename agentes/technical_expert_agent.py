"""
Agente especialista em análise técnica que implementa regras de trading baseadas em indicadores.
"""
from typing import Dict, List, Optional, Any
import torch
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import talib
from .expert_base_agent import ExpertBaseAgent

class TechnicalExpertAgent(ExpertBaseAgent):
    def __init__(self, name: str = "TechnicalExpertAgent", gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        
        # Configura regras de análise técnica
        self.setup_technical_rules()
        
        # Adiciona conhecimento específico
        self.add_knowledge('rsi_oversold', 30)
        self.add_knowledge('rsi_overbought', 70)
        self.add_knowledge('macd_threshold', 0)
        self.add_knowledge('volume_ratio_threshold', 1.5)
        
    def setup_technical_rules(self):
        """Configura regras de análise técnica."""
        # Regras de tendência
        self.add_rule('trend_sma', self.rule_sma_crossover, weight=1.0)
        self.add_rule('trend_macd', self.rule_macd_signal, weight=1.0)
        
        # Regras de momentum
        self.add_rule('momentum_rsi', self.rule_rsi, weight=0.8)
        self.add_rule('momentum_stoch', self.rule_stochastic, weight=0.8)
        
        # Regras de volume
        self.add_rule('volume_price', self.rule_volume_price_correlation, weight=0.7)
        self.add_rule('volume_trend', self.rule_volume_trend, weight=0.7)
        
        # Regras de volatilidade
        self.add_rule('volatility_bb', self.rule_bollinger_bands, weight=0.9)
        self.add_rule('volatility_atr', self.rule_atr, weight=0.6)
        
    def rule_sma_crossover(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra de cruzamento de médias móveis."""
        try:
            close = data['close']
            sma_20 = talib.SMA(close, timeperiod=20)
            sma_50 = talib.SMA(close, timeperiod=50)
            
            # Verifica cruzamento
            if sma_20[-1] > sma_50[-1] and sma_20[-2] <= sma_50[-2]:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.8,
                    'metadata': {
                        'sma_20': sma_20[-1],
                        'sma_50': sma_50[-1],
                        'reason': 'Cruzamento de alta das médias móveis'
                    }
                }
            elif sma_20[-1] < sma_50[-1] and sma_20[-2] >= sma_50[-2]:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.8,
                    'metadata': {
                        'sma_20': sma_20[-1],
                        'sma_50': sma_50[-1],
                        'reason': 'Cruzamento de baixa das médias móveis'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'sma_20': sma_20[-1],
                    'sma_50': sma_50[-1],
                    'reason': 'Sem cruzamento significativo'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra SMA: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_macd_signal(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no MACD."""
        try:
            close = data['close']
            macd, signal, hist = talib.MACD(close)
            
            threshold = knowledge['macd_threshold']
            
            # Verifica sinais do MACD
            if hist[-1] > threshold and hist[-2] <= threshold:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.85,
                    'metadata': {
                        'macd': macd[-1],
                        'signal': signal[-1],
                        'histogram': hist[-1],
                        'reason': 'Cruzamento de alta do MACD'
                    }
                }
            elif hist[-1] < -threshold and hist[-2] >= -threshold:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.85,
                    'metadata': {
                        'macd': macd[-1],
                        'signal': signal[-1],
                        'histogram': hist[-1],
                        'reason': 'Cruzamento de baixa do MACD'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'macd': macd[-1],
                    'signal': signal[-1],
                    'histogram': hist[-1],
                    'reason': 'Sem sinal significativo do MACD'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra MACD: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_rsi(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no RSI."""
        try:
            close = data['close']
            rsi = talib.RSI(close)
            
            oversold = knowledge['rsi_oversold']
            overbought = knowledge['rsi_overbought']
            
            if rsi[-1] < oversold:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.9,
                    'metadata': {
                        'rsi': rsi[-1],
                        'reason': 'RSI em condição de sobrevendido'
                    }
                }
            elif rsi[-1] > overbought:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.9,
                    'metadata': {
                        'rsi': rsi[-1],
                        'reason': 'RSI em condição de sobrecomprado'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'rsi': rsi[-1],
                    'reason': 'RSI em região neutra'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra RSI: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_stochastic(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no Estocástico."""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            slowk, slowd = talib.STOCH(high, low, close)
            
            if slowk[-1] < 20 and slowd[-1] < 20:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.85,
                    'metadata': {
                        'k': slowk[-1],
                        'd': slowd[-1],
                        'reason': 'Estocástico em região de sobrevendido'
                    }
                }
            elif slowk[-1] > 80 and slowd[-1] > 80:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.85,
                    'metadata': {
                        'k': slowk[-1],
                        'd': slowd[-1],
                        'reason': 'Estocástico em região de sobrecomprado'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'k': slowk[-1],
                    'd': slowd[-1],
                    'reason': 'Estocástico em região neutra'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Estocástico: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_bollinger_bands(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada nas Bandas de Bollinger."""
        try:
            close = data['close']
            upper, middle, lower = talib.BBANDS(close)
            
            # Calcula a largura das bandas
            bandwidth = (upper[-1] - lower[-1]) / middle[-1]
            
            if close[-1] <= lower[-1]:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.9,
                    'metadata': {
                        'price': close[-1],
                        'lower_band': lower[-1],
                        'bandwidth': bandwidth,
                        'reason': 'Preço tocou/cruzou banda inferior'
                    }
                }
            elif close[-1] >= upper[-1]:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.9,
                    'metadata': {
                        'price': close[-1],
                        'upper_band': upper[-1],
                        'bandwidth': bandwidth,
                        'reason': 'Preço tocou/cruzou banda superior'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'price': close[-1],
                    'middle_band': middle[-1],
                    'bandwidth': bandwidth,
                    'reason': 'Preço dentro das bandas'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Bollinger: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_volume_price_correlation(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada na correlação preço-volume."""
        try:
            close = data['close']
            volume = data['volume']
            
            # Calcula correlação entre preço e volume
            price_change = np.diff(close)
            volume_change = np.diff(volume)
            correlation = np.corrcoef(price_change[-20:], volume_change[-20:])[0,1]
            
            if correlation > 0.7:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.8,
                    'metadata': {
                        'correlation': correlation,
                        'reason': 'Alta correlação positiva preço-volume'
                    }
                }
            elif correlation < -0.7:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.8,
                    'metadata': {
                        'correlation': correlation,
                        'reason': 'Alta correlação negativa preço-volume'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'correlation': correlation,
                    'reason': 'Baixa correlação preço-volume'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Volume-Preço: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_volume_trend(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada na tendência do volume."""
        try:
            volume = data['volume']
            close = data['close']
            
            # Calcula média móvel do volume
            vol_sma = talib.SMA(volume, timeperiod=20)
            vol_ratio = volume[-1] / vol_sma[-1]
            
            price_change = (close[-1] - close[-2]) / close[-2]
            
            if vol_ratio > knowledge['volume_ratio_threshold'] and price_change > 0:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.85,
                    'metadata': {
                        'volume_ratio': vol_ratio,
                        'price_change': price_change,
                        'reason': 'Alto volume com preço subindo'
                    }
                }
            elif vol_ratio > knowledge['volume_ratio_threshold'] and price_change < 0:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.85,
                    'metadata': {
                        'volume_ratio': vol_ratio,
                        'price_change': price_change,
                        'reason': 'Alto volume com preço caindo'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'volume_ratio': vol_ratio,
                    'price_change': price_change,
                    'reason': 'Volume dentro da média'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Tendência Volume: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_atr(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no ATR (Average True Range)."""
        try:
            high = data['high']
            low = data['low']
            close = data['close']
            
            atr = talib.ATR(high, low, close)
            atr_ma = talib.SMA(atr, timeperiod=20)
            
            # Calcula razão ATR atual / média
            atr_ratio = atr[-1] / atr_ma[-1]
            
            if atr_ratio > 1.5:
                return {
                    'decision': 'NEUTRO',
                    'confidence': 0.7,
                    'metadata': {
                        'atr_ratio': atr_ratio,
                        'reason': 'Alta volatilidade - aguardar estabilização'
                    }
                }
            else:
                return {
                    'decision': 'NEUTRO',
                    'confidence': 0.5,
                    'metadata': {
                        'atr_ratio': atr_ratio,
                        'reason': 'Volatilidade normal'
                    }
                }
        except Exception as e:
            logging.error(f"Erro na regra ATR: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """
        Processa dados técnicos em lote na GPU.
        """
        try:
            with torch.no_grad():
                # Exemplo de processamento em lote de indicadores
                # Neste caso, calculamos RSI e MACD em paralelo
                rsi = torch.nn.functional.conv1d(
                    batch.unsqueeze(1),
                    torch.ones(14, 1, 1, device=self.device) / 14,
                    padding=13
                ).squeeze(1)
                
                exp1 = torch.nn.functional.conv1d(
                    batch.unsqueeze(1),
                    torch.ones(12, 1, 1, device=self.device) / 12,
                    padding=11
                ).squeeze(1)
                
                exp2 = torch.nn.functional.conv1d(
                    batch.unsqueeze(1),
                    torch.ones(26, 1, 1, device=self.device) / 26,
                    padding=25
                ).squeeze(1)
                
                macd = exp1 - exp2
                
                return torch.stack([rsi, macd], dim=1)
                
        except Exception as e:
            logging.error(f"Erro no forward pass: {str(e)}")
            return torch.tensor([], device=self.device)