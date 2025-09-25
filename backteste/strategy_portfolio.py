from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from backteste.strategy_evaluator import StrategyScore
from backteste.backtest_engine import BacktestResult

@dataclass
class StrategyAllocation:
    """Representa a alocação de capital para uma estratégia"""
    strategy_id: str
    weight: float  # Peso no portfólio (0-1)
    max_allocation: float  # Máxima alocação permitida
    current_allocation: float  # Alocação atual
    performance_metrics: Dict[str, float]
    last_update: datetime

class StrategyPortfolio:
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.allocations: Dict[str, StrategyAllocation] = {}
        self.historical_performance: List[Dict] = []
        self.min_score_threshold = 0.4  # Score mínimo para manter estratégia
        
    def update_portfolio(self, strategy_scores: List[StrategyScore]):
        """Atualiza o portfólio baseado nas pontuações das estratégias"""
        # Filtra estratégias com pontuação mínima
        valid_strategies = [
            score for score in strategy_scores
            if score.overall_score >= self.min_score_threshold
        ]
        
        if not valid_strategies:
            return
        
        # Calcula novos pesos usando mean-variance optimization
        weights = self._optimize_weights(valid_strategies)
        
        # Atualiza alocações
        new_allocations = {}
        for strategy, weight in weights.items():
            score = next(s for s in valid_strategies if s.strategy_id == strategy)
            
            new_allocations[strategy] = StrategyAllocation(
                strategy_id=strategy,
                weight=weight,
                max_allocation=min(0.25, weight * 1.5),  # Limite máximo de 25% por estratégia
                current_allocation=self.current_capital * weight,
                performance_metrics=score.performance_metrics,
                last_update=datetime.now()
            )
        
        # Remove estratégias que não estão mais no portfólio
        removed_strategies = set(self.allocations.keys()) - set(new_allocations.keys())
        for strategy_id in removed_strategies:
            self._handle_strategy_removal(strategy_id)
        
        self.allocations = new_allocations
        self._record_portfolio_state()
    
    def _optimize_weights(self, strategies: List[StrategyScore]) -> Dict[str, float]:
        """Otimiza pesos do portfólio usando mean-variance optimization"""
        n_strategies = len(strategies)
        if n_strategies == 0:
            return {}
        
        # Extrai retornos e riscos
        returns = np.array([
            s.performance_metrics['risk_adjusted_return']
            for s in strategies
        ])
        
        # Matriz de correlação simplificada (assume correlação média)
        correlation = np.full((n_strategies, n_strategies), 0.2)
        np.fill_diagonal(correlation, 1.0)
        
        # Calcula variâncias
        variances = np.array([
            s.performance_metrics['max_drawdown'] ** 2
            for s in strategies
        ])
        
        # Matriz de covariância
        covariance = np.outer(np.sqrt(variances), np.sqrt(variances)) * correlation
        
        # Otimização simples (equal risk contribution)
        weights = 1.0 / np.sqrt(np.diag(covariance))
        weights = weights / np.sum(weights)
        
        return {
            s.strategy_id: w
            for s, w in zip(strategies, weights)
        }
    
    def _handle_strategy_removal(self, strategy_id: str):
        """Processa remoção de uma estratégia do portfólio"""
        allocation = self.allocations[strategy_id]
        self.current_capital += allocation.current_allocation
        # TODO: Implementar lógica de fechamento de posições
    
    def _record_portfolio_state(self):
        """Registra estado atual do portfólio"""
        total_allocation = sum(a.current_allocation for a in self.allocations.values())
        
        state = {
            'timestamp': datetime.now(),
            'total_capital': self.current_capital,
            'allocated_capital': total_allocation,
            'n_strategies': len(self.allocations),
            'allocations': {
                strategy_id: {
                    'weight': alloc.weight,
                    'allocation': alloc.current_allocation,
                    'metrics': alloc.performance_metrics
                }
                for strategy_id, alloc in self.allocations.items()
            }
        }
        
        self.historical_performance.append(state)
    
    def get_allocation_for_strategy(self, strategy_id: str) -> Optional[StrategyAllocation]:
        """Retorna alocação atual para uma estratégia"""
        return self.allocations.get(strategy_id)
    
    def adjust_allocation(self, strategy_id: str, new_weight: float):
        """Ajusta alocação de uma estratégia específica"""
        if strategy_id not in self.allocations:
            return
        
        # Limita peso máximo
        new_weight = min(new_weight, 0.25)
        
        # Ajusta outros pesos proporcionalmente
        total_other_weight = sum(
            a.weight for sid, a in self.allocations.items()
            if sid != strategy_id
        )
        
        if total_other_weight > 0:
            scale_factor = (1 - new_weight) / total_other_weight
            for sid, alloc in self.allocations.items():
                if sid != strategy_id:
                    alloc.weight *= scale_factor
                    alloc.current_allocation = self.current_capital * alloc.weight
        
        # Atualiza estratégia alvo
        self.allocations[strategy_id].weight = new_weight
        self.allocations[strategy_id].current_allocation = self.current_capital * new_weight
        self._record_portfolio_state()
    
    def get_portfolio_metrics(self) -> Dict:
        """Retorna métricas agregadas do portfólio"""
        if not self.allocations:
            return {}
        
        weighted_metrics = {
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }
        
        for alloc in self.allocations.values():
            for metric in weighted_metrics:
                weighted_metrics[metric] += (
                    alloc.performance_metrics[metric] * alloc.weight
                )
        
        return {
            **weighted_metrics,
            'n_strategies': len(self.allocations),
            'total_allocation': sum(a.current_allocation for a in self.allocations.values()),
            'max_strategy_weight': max(a.weight for a in self.allocations.values())
        }
    
    def get_strategy_ranking(self) -> List[Tuple[str, float]]:
        """Retorna ranking das estratégias por peso no portfólio"""
        return sorted(
            [(sid, alloc.weight) for sid, alloc in self.allocations.items()],
            key=lambda x: x[1],
            reverse=True
        )