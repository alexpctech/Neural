"""
Agente especialista em análise fundamentalista que implementa regras baseadas em indicadores financeiros.
"""
from typing import Dict, List, Optional, Any
import torch
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from .expert_base_agent import ExpertBaseAgent

class FundamentalExpertAgent(ExpertBaseAgent):
    def __init__(self, name: str = "FundamentalExpertAgent", gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        
        # Configura regras fundamentalistas
        self.setup_fundamental_rules()
        
        # Adiciona conhecimento específico
        self.add_knowledge('min_pe_ratio', 5)
        self.add_knowledge('max_pe_ratio', 25)
        self.add_knowledge('min_dividend_yield', 0.03)  # 3%
        self.add_knowledge('min_roe', 0.15)  # 15%
        self.add_knowledge('max_debt_to_equity', 2.0)
        self.add_knowledge('min_current_ratio', 1.5)
        self.add_knowledge('min_profit_margin', 0.10)  # 10%
        self.add_knowledge('min_revenue_growth', 0.10)  # 10%
        
    def setup_fundamental_rules(self):
        """Configura regras de análise fundamentalista."""
        # Regras de valuation
        self.add_rule('valuation_pe', self.rule_pe_ratio, weight=1.0)
        self.add_rule('valuation_dividend', self.rule_dividend_yield, weight=0.8)
        
        # Regras de rentabilidade
        self.add_rule('profitability_roe', self.rule_roe, weight=0.9)
        self.add_rule('profitability_margin', self.rule_profit_margin, weight=0.8)
        
        # Regras de saúde financeira
        self.add_rule('health_liquidity', self.rule_liquidity, weight=1.0)
        self.add_rule('health_leverage', self.rule_leverage, weight=0.9)
        
        # Regras de crescimento
        self.add_rule('growth_revenue', self.rule_revenue_growth, weight=0.7)
        self.add_rule('growth_profit', self.rule_profit_growth, weight=0.7)
        
    def rule_pe_ratio(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no P/E (Preço/Lucro)."""
        try:
            pe_ratio = data.get('pe_ratio')
            if pe_ratio is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_pe = knowledge['min_pe_ratio']
            max_pe = knowledge['max_pe_ratio']
            
            if pe_ratio < min_pe:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.9,
                    'metadata': {
                        'pe_ratio': pe_ratio,
                        'reason': 'P/E abaixo do mínimo ideal - possível subvalorização'
                    }
                }
            elif pe_ratio > max_pe:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.9,
                    'metadata': {
                        'pe_ratio': pe_ratio,
                        'reason': 'P/E acima do máximo ideal - possível sobrevalorização'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.7,
                'metadata': {
                    'pe_ratio': pe_ratio,
                    'reason': 'P/E dentro da faixa ideal'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra P/E: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_dividend_yield(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no Dividend Yield."""
        try:
            div_yield = data.get('dividend_yield')
            if div_yield is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_yield = knowledge['min_dividend_yield']
            
            if div_yield > min_yield:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.8,
                    'metadata': {
                        'dividend_yield': div_yield,
                        'reason': 'Dividend Yield atrativo'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.6,
                'metadata': {
                    'dividend_yield': div_yield,
                    'reason': 'Dividend Yield abaixo do mínimo desejado'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Dividend Yield: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_roe(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no ROE (Return on Equity)."""
        try:
            roe = data.get('roe')
            if roe is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_roe = knowledge['min_roe']
            
            if roe > min_roe:
                confidence = min(0.9, 0.6 + (roe - min_roe))
                return {
                    'decision': 'COMPRA',
                    'confidence': confidence,
                    'metadata': {
                        'roe': roe,
                        'reason': 'ROE acima do mínimo desejado'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.5,
                'metadata': {
                    'roe': roe,
                    'reason': 'ROE abaixo do mínimo desejado'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra ROE: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_liquidity(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada em índices de liquidez."""
        try:
            current_ratio = data.get('current_ratio')
            if current_ratio is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_ratio = knowledge['min_current_ratio']
            
            if current_ratio > min_ratio:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.8,
                    'metadata': {
                        'current_ratio': current_ratio,
                        'reason': 'Boa liquidez corrente'
                    }
                }
            elif current_ratio < 1.0:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.9,
                    'metadata': {
                        'current_ratio': current_ratio,
                        'reason': 'Liquidez corrente preocupante'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.6,
                'metadata': {
                    'current_ratio': current_ratio,
                    'reason': 'Liquidez corrente adequada'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Liquidez: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_leverage(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada em alavancagem financeira."""
        try:
            debt_to_equity = data.get('debt_to_equity')
            if debt_to_equity is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            max_ratio = knowledge['max_debt_to_equity']
            
            if debt_to_equity > max_ratio:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.85,
                    'metadata': {
                        'debt_to_equity': debt_to_equity,
                        'reason': 'Alavancagem excessiva'
                    }
                }
            elif debt_to_equity < max_ratio / 2:
                return {
                    'decision': 'COMPRA',
                    'confidence': 0.8,
                    'metadata': {
                        'debt_to_equity': debt_to_equity,
                        'reason': 'Alavancagem conservadora'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.7,
                'metadata': {
                    'debt_to_equity': debt_to_equity,
                    'reason': 'Alavancagem adequada'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Alavancagem: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_profit_margin(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada na margem de lucro."""
        try:
            profit_margin = data.get('profit_margin')
            if profit_margin is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_margin = knowledge['min_profit_margin']
            
            if profit_margin > min_margin:
                confidence = min(0.9, 0.6 + (profit_margin - min_margin))
                return {
                    'decision': 'COMPRA',
                    'confidence': confidence,
                    'metadata': {
                        'profit_margin': profit_margin,
                        'reason': 'Boa margem de lucro'
                    }
                }
            elif profit_margin < 0:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.85,
                    'metadata': {
                        'profit_margin': profit_margin,
                        'reason': 'Empresa com prejuízo'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.6,
                'metadata': {
                    'profit_margin': profit_margin,
                    'reason': 'Margem de lucro adequada'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Margem: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_revenue_growth(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no crescimento de receita."""
        try:
            growth = data.get('revenue_growth')
            if growth is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_growth = knowledge['min_revenue_growth']
            
            if growth > min_growth:
                confidence = min(0.9, 0.6 + (growth - min_growth))
                return {
                    'decision': 'COMPRA',
                    'confidence': confidence,
                    'metadata': {
                        'revenue_growth': growth,
                        'reason': 'Bom crescimento de receita'
                    }
                }
            elif growth < 0:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.8,
                    'metadata': {
                        'revenue_growth': growth,
                        'reason': 'Queda na receita'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.6,
                'metadata': {
                    'revenue_growth': growth,
                    'reason': 'Crescimento modesto'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Crescimento: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def rule_profit_growth(self, data: Dict[str, Any], knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Regra baseada no crescimento do lucro."""
        try:
            growth = data.get('profit_growth')
            if growth is None:
                return {'decision': 'ERRO', 'confidence': 0}
                
            min_growth = knowledge['min_revenue_growth']  # Usa mesmo parâmetro da receita
            
            if growth > min_growth:
                confidence = min(0.9, 0.6 + (growth - min_growth))
                return {
                    'decision': 'COMPRA',
                    'confidence': confidence,
                    'metadata': {
                        'profit_growth': growth,
                        'reason': 'Bom crescimento do lucro'
                    }
                }
            elif growth < 0:
                return {
                    'decision': 'VENDA',
                    'confidence': 0.8,
                    'metadata': {
                        'profit_growth': growth,
                        'reason': 'Queda no lucro'
                    }
                }
            return {
                'decision': 'NEUTRO',
                'confidence': 0.6,
                'metadata': {
                    'profit_growth': growth,
                    'reason': 'Crescimento modesto do lucro'
                }
            }
        except Exception as e:
            logging.error(f"Erro na regra Crescimento Lucro: {str(e)}")
            return {'decision': 'ERRO', 'confidence': 0}
            
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """
        Processa indicadores fundamentalistas em lote na GPU.
        """
        try:
            with torch.no_grad():
                # Exemplo de processamento de múltiplos em lote
                # Calcula P/L, ROE e Margem em paralelo
                pe_ratio = batch[:, 0] / batch[:, 1]  # price / earnings
                roe = batch[:, 1] / batch[:, 2]  # earnings / equity
                margin = batch[:, 1] / batch[:, 3]  # earnings / revenue
                
                return torch.stack([pe_ratio, roe, margin], dim=1)
                
        except Exception as e:
            logging.error(f"Erro no forward pass: {str(e)}")
            return torch.tensor([], device=self.device)