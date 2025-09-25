from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from backteste.backtest_engine import BacktestResult, MarketCondition

@dataclass
class StrategyScore:
    """Pontuação de uma estratégia baseada em múltiplas métricas"""
    strategy_id: str
    overall_score: float
    performance_metrics: Dict[str, float]
    market_adaptability: Dict[MarketCondition, float]
    consistency_score: float
    timestamp: datetime

class StrategyEvaluator:
    def __init__(self):
        self.strategy_scores: Dict[str, StrategyScore] = {}
        self.historical_scores: Dict[str, List[StrategyScore]] = {}
        self.performance_weights = {
            'sharpe_ratio': 0.25,
            'max_drawdown': 0.20,
            'win_rate': 0.15,
            'profit_factor': 0.20,
            'risk_adjusted_return': 0.20
        }
    
    def evaluate_strategy(self, backtest_results: List[BacktestResult]) -> StrategyScore:
        """Avalia uma estratégia baseada em seus resultados de backtest"""
        if not backtest_results:
            raise ValueError("Lista de resultados de backtest vazia")
        
        strategy_id = backtest_results[0].strategy_id
        
        # Calcula métricas médias
        avg_metrics = {
            'sharpe_ratio': np.mean([r.sharpe_ratio for r in backtest_results]),
            'max_drawdown': np.mean([r.max_drawdown for r in backtest_results]),
            'win_rate': np.mean([r.win_rate for r in backtest_results]),
            'profit_factor': np.mean([r.profit_factor for r in backtest_results]),
            'risk_adjusted_return': np.mean([r.risk_adjusted_return for r in backtest_results])
        }
        
        # Analisa adaptabilidade a diferentes condições de mercado
        market_adaptability = self._analyze_market_adaptability(backtest_results)
        
        # Calcula consistência
        consistency_score = self._calculate_consistency(backtest_results)
        
        # Calcula pontuação geral
        overall_score = self._calculate_overall_score(avg_metrics, market_adaptability, consistency_score)
        
        # Cria e armazena score
        score = StrategyScore(
            strategy_id=strategy_id,
            overall_score=overall_score,
            performance_metrics=avg_metrics,
            market_adaptability=market_adaptability,
            consistency_score=consistency_score,
            timestamp=datetime.now()
        )
        
        self.strategy_scores[strategy_id] = score
        if strategy_id not in self.historical_scores:
            self.historical_scores[strategy_id] = []
        self.historical_scores[strategy_id].append(score)
        
        return score
    
    def _analyze_market_adaptability(self, backtest_results: List[BacktestResult]) -> Dict[MarketCondition, float]:
        """Analisa como a estratégia se adapta a diferentes condições de mercado"""
        condition_results = {condition: [] for condition in MarketCondition}
        
        for result in backtest_results:
            for condition in result.market_conditions.values():
                if isinstance(condition, MarketCondition):
                    # Usa Sharpe ratio como métrica de performance
                    condition_results[condition].append(result.sharpe_ratio)
        
        # Calcula score médio para cada condição
        return {
            condition: np.mean(scores) if scores else 0.0
            for condition, scores in condition_results.items()
        }
    
    def _calculate_consistency(self, backtest_results: List[BacktestResult]) -> float:
        """Calcula a consistência da estratégia"""
        if len(backtest_results) < 2:
            return 0.0
        
        # Calcula variação das métricas principais
        variations = {
            'sharpe_ratio': np.std([r.sharpe_ratio for r in backtest_results]),
            'win_rate': np.std([r.win_rate for r in backtest_results]),
            'profit_factor': np.std([r.profit_factor for r in backtest_results])
        }
        
        # Normaliza e inverte (menor variação = maior consistência)
        normalized_variations = {
            metric: 1 / (1 + var)
            for metric, var in variations.items()
        }
        
        return np.mean(list(normalized_variations.values()))
    
    def _calculate_overall_score(
        self,
        metrics: Dict[str, float],
        market_adaptability: Dict[MarketCondition, float],
        consistency: float
    ) -> float:
        """Calcula pontuação geral da estratégia"""
        # Performance score
        performance_score = sum(
            metrics[metric] * weight
            for metric, weight in self.performance_weights.items()
        )
        
        # Adaptability score (média dos scores por condição de mercado)
        adaptability_score = np.mean(list(market_adaptability.values()))
        
        # Pesos finais
        weights = {
            'performance': 0.5,
            'adaptability': 0.3,
            'consistency': 0.2
        }
        
        return (
            performance_score * weights['performance'] +
            adaptability_score * weights['adaptability'] +
            consistency * weights['consistency']
        )
    
    def get_top_strategies(self, n: int = 10) -> List[StrategyScore]:
        """Retorna as N melhores estratégias baseado na pontuação geral"""
        sorted_strategies = sorted(
            self.strategy_scores.values(),
            key=lambda x: x.overall_score,
            reverse=True
        )
        return sorted_strategies[:n]
    
    def get_strategy_history(self, strategy_id: str) -> List[StrategyScore]:
        """Retorna histórico de pontuações de uma estratégia"""
        return self.historical_scores.get(strategy_id, [])
    
    def is_strategy_declining(self, strategy_id: str, window: int = 5) -> bool:
        """Verifica se performance da estratégia está declinando"""
        history = self.get_strategy_history(strategy_id)
        if len(history) < window:
            return False
        
        recent_scores = [score.overall_score for score in history[-window:]]
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
        return trend < 0
    
    def should_retire_strategy(self, strategy_id: str) -> bool:
        """Decide se uma estratégia deve ser aposentada"""
        history = self.get_strategy_history(strategy_id)
        if not history:
            return False
        
        current_score = history[-1].overall_score
        
        # Critérios de aposentadoria
        conditions = [
            current_score < 0.3,  # Score muito baixo
            self.is_strategy_declining(strategy_id),  # Tendência de queda
            len(history) >= 3 and all(  # Consistentemente ruim
                score.overall_score < 0.4 for score in history[-3:]
            )
        ]
        
        return any(conditions)