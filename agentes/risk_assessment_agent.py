"""
Agente responsável por análise de risco e avaliação de carteira.
Utiliza métricas como VaR, Sharpe Ratio e drawdown máximo.
"""
from typing import Dict, List, Optional, Any
import torch
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from .abstract_agent import AbstractAgent

class RiskAssessmentAgent(AbstractAgent):
    def __init__(self, name: str = "RiskAssessmentAgent", gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        self.risk_free_rate = 0.02  # Taxa livre de risco (2% a.a.)
        self.var_confidence = 0.95  # Nível de confiança para VaR
        self.portfolio = {}  # Pesos dos ativos no portfólio
        
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza análise de risco do portfólio/ativo.
        """
        try:
            returns = data.get('returns')
            if returns is None:
                raise ValueError("Dados de retornos não fornecidos")
                
            # Calcula métricas de risco
            volatility = self._calculate_volatility(returns)
            var = self._calculate_var(returns)
            beta = self._calculate_beta(returns, data.get('benchmark_returns'))
            sharpe = self._calculate_sharpe(returns)
            max_drawdown = self._calculate_max_drawdown(returns)
            
            analysis = {
                'signal_type': 'RISK_ASSESSMENT',
                'confidence': self.var_confidence,
                'parameters': {
                    'volatility': volatility,
                    'value_at_risk': var,
                    'beta': beta,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': max_drawdown
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'portfolio': self.portfolio.copy()
                }
            }
            
            self.last_analysis = analysis
            return analysis
            
        except Exception as e:
            logging.error(f"Erro na análise de risco: {str(e)}")
            return {
                'signal_type': 'ERROR',
                'confidence': 0,
                'parameters': {},
                'metadata': {'error': str(e)}
            }
            
    def prepare_batch(self, data: List[Dict]) -> torch.Tensor:
        """
        Prepara batch de dados para análise em GPU.
        """
        try:
            returns_data = []
            for item in data:
                if 'returns' in item:
                    returns_series = pd.Series(item['returns'])
                    # Calcula métricas em batch
                    metrics = torch.tensor([
                        returns_series.std() * np.sqrt(252),  # Volatilidade anualizada
                        returns_series.quantile(1 - self.var_confidence),  # VaR
                        (1 + returns_series).cumprod().max() - 1,  # Retorno máximo
                        (1 + returns_series).cumprod().min() - 1   # Retorno mínimo
                    ], device=self.device)
                    returns_data.append(metrics)
                    
            if returns_data:
                return torch.stack(returns_data)
            return torch.tensor([], device=self.device)
            
        except Exception as e:
            logging.error(f"Erro ao preparar batch: {str(e)}")
            return torch.tensor([], device=self.device)
            
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """
        Processa métricas de risco em lote na GPU.
        """
        try:
            with torch.no_grad():
                # Calcula métricas adicionais
                sharpe = (batch[:, 0] - self.risk_free_rate) / batch[:, 1]  # (retorno - rf) / vol
                sortino = torch.where(
                    batch[:, 1] < 0,
                    (batch[:, 0] - self.risk_free_rate) / batch[:, 1].abs(),
                    torch.zeros_like(batch[:, 0])
                )
                drawdown = batch[:, 2] - batch[:, 3]  # max - min
                
                return torch.stack([sharpe, sortino, drawdown], dim=1)
                
        except Exception as e:
            logging.error(f"Erro no forward pass: {str(e)}")
            return torch.tensor([], device=self.device)
            
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calcula volatilidade anualizada."""
        return returns.std() * np.sqrt(252)
        
    def _calculate_var(self, returns: pd.Series) -> float:
        """Calcula Value at Risk."""
        return returns.quantile(1 - self.var_confidence)
        
    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calcula beta em relação ao benchmark."""
        if benchmark_returns is None:
            return 1.0
        cov = returns.cov(benchmark_returns)
        var = benchmark_returns.var()
        return cov / var if var != 0 else 1.0
        
    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """Calcula Sharpe Ratio anualizado."""
        excess_returns = returns - (self.risk_free_rate / 252)  # Converte taxa anual para diária
        if len(excess_returns) > 0:
            return np.sqrt(252) * excess_returns.mean() / returns.std()
        return 0.0
        
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calcula máximo drawdown."""
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdowns = cumulative / rolling_max - 1.0
        return drawdowns.min()
        
    def update_portfolio(self, weights: Dict[str, float]) -> None:
        """Atualiza os pesos do portfólio."""
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.0001:  # Tolera pequena diferença de arredondamento
            # Normaliza os pesos
            self.portfolio = {
                ticker: weight/total_weight 
                for ticker, weight in weights.items()
            }
        else:
            self.portfolio = weights.copy()
            
    def get_portfolio_risk(self, returns_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """
        Calcula métricas de risco para o portfólio completo.
        """
        try:
            if not self.portfolio or not returns_data:
                return {}
                
            # Calcula retorno do portfólio
            portfolio_returns = pd.Series(0, index=next(iter(returns_data.values())).index)
            for ticker, weight in self.portfolio.items():
                if ticker in returns_data:
                    portfolio_returns += returns_data[ticker] * weight
                    
            # Calcula métricas
            risk_metrics = {
                'volatility': self._calculate_volatility(portfolio_returns),
                'var': self._calculate_var(portfolio_returns),
                'sharpe': self._calculate_sharpe(portfolio_returns),
                'max_drawdown': self._calculate_max_drawdown(portfolio_returns)
            }
            
            return risk_metrics
            
        except Exception as e:
            logging.error(f"Erro ao calcular risco do portfólio: {str(e)}")
            return {}