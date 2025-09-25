from typing import Dict, List, Optional, Type
from datetime import datetime, timedelta
import logging
from backteste.backtest_engine import BacktestEngine, BacktestResult
from backteste.strategy_evaluator import StrategyEvaluator
from backteste.strategy_portfolio import StrategyPortfolio

class AdaptiveLearningSystem:
    def __init__(self, initial_capital: float = 1000000.0):
        self.backtest_engine = BacktestEngine()
        self.evaluator = StrategyEvaluator()
        self.portfolio = StrategyPortfolio(initial_capital)
        self.strategies: Dict[str, object] = {}
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura logger para o sistema"""
        logger = logging.getLogger('AdaptiveLearningSystem')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('logs/adaptive_learning.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def add_strategy(self, strategy_id: str, strategy_class: Type, **params):
        """Adiciona uma nova estratégia ao sistema"""
        try:
            strategy = strategy_class(**params)
            self.strategies[strategy_id] = strategy
            self.logger.info(f"Estratégia adicionada: {strategy_id}")
        except Exception as e:
            self.logger.error(f"Erro ao adicionar estratégia {strategy_id}: {str(e)}")
            raise
    
    def evaluate_strategy(self, strategy_id: str, symbol: str, periods: List[tuple]) -> bool:
        """Avalia uma estratégia em múltiplos períodos"""
        if strategy_id not in self.strategies:
            self.logger.error(f"Estratégia não encontrada: {strategy_id}")
            return False
        
        try:
            # Executa backtests
            results = []
            for start_date, end_date in periods:
                result = self.backtest_engine.run_backtest(
                    self.strategies[strategy_id],
                    symbol,
                    start_date,
                    end_date
                )
                results.append(result)
            
            # Avalia resultados
            score = self.evaluator.evaluate_strategy(results)
            
            # Decide se mantém a estratégia
            should_keep = score.overall_score >= 0.4
            
            self.logger.info(
                f"Avaliação da estratégia {strategy_id}:\n"
                f"Score geral: {score.overall_score:.2f}\n"
                f"Decisão: {'manter' if should_keep else 'descartar'}"
            )
            
            return should_keep
        
        except Exception as e:
            self.logger.error(f"Erro ao avaliar estratégia {strategy_id}: {str(e)}")
            return False
    
    def update_portfolio(self):
        """Atualiza o portfólio com as melhores estratégias"""
        try:
            # Obtém scores de todas as estratégias
            scores = [
                score for score in self.evaluator.strategy_scores.values()
                if score.overall_score >= 0.4
            ]
            
            # Atualiza alocações
            self.portfolio.update_portfolio(scores)
            
            metrics = self.portfolio.get_portfolio_metrics()
            self.logger.info(
                f"Portfólio atualizado:\n"
                f"Número de estratégias: {metrics['n_strategies']}\n"
                f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n"
                f"Max Drawdown: {metrics['max_drawdown']:.2f}\n"
                f"Win Rate: {metrics['win_rate']:.2f}"
            )
        
        except Exception as e:
            self.logger.error(f"Erro ao atualizar portfólio: {str(e)}")
    
    def get_strategy_recommendation(self, symbol: str) -> Dict:
        """Gera recomendação combinada das estratégias ativas"""
        recommendations = {}
        total_weight = 0
        
        try:
            for strategy_id, strategy in self.strategies.items():
                allocation = self.portfolio.get_allocation_for_strategy(strategy_id)
                if allocation:
                    signal = strategy.generate_signal(symbol)
                    if signal != 0:  # Se houver sinal
                        recommendations[strategy_id] = {
                            'signal': signal,
                            'weight': allocation.weight,
                            'confidence': strategy.get_confidence()
                        }
                        total_weight += allocation.weight
            
            if not recommendations:
                return {'action': 'HOLD', 'confidence': 0.0}
            
            # Calcula sinal ponderado
            weighted_signal = sum(
                rec['signal'] * rec['weight'] * rec['confidence']
                for rec in recommendations.values()
            ) / total_weight
            
            # Determina ação final
            if weighted_signal > 0.2:
                action = 'BUY'
            elif weighted_signal < -0.2:
                action = 'SELL'
            else:
                action = 'HOLD'
            
            return {
                'action': action,
                'confidence': abs(weighted_signal),
                'contributing_strategies': recommendations
            }
        
        except Exception as e:
            self.logger.error(f"Erro ao gerar recomendação: {str(e)}")
            return {'action': 'HOLD', 'confidence': 0.0}
    
    def retire_strategy(self, strategy_id: str):
        """Aposenta uma estratégia que não está mais performando bem"""
        try:
            if strategy_id in self.strategies:
                self.logger.info(f"Aposentando estratégia: {strategy_id}")
                
                # Remove do portfólio primeiro
                if strategy_id in self.portfolio.allocations:
                    self.portfolio.adjust_allocation(strategy_id, 0.0)
                
                # Remove da lista de estratégias
                del self.strategies[strategy_id]
                
                # Atualiza portfólio
                self.update_portfolio()
        
        except Exception as e:
            self.logger.error(f"Erro ao aposentar estratégia {strategy_id}: {str(e)}")
    
    def adapt_strategy_parameters(self, strategy_id: str):
        """Adapta parâmetros da estratégia baseado em performance histórica"""
        if strategy_id not in self.strategies:
            return
        
        try:
            strategy = self.strategies[strategy_id]
            if hasattr(strategy, 'optimize_parameters'):
                history = self.evaluator.get_strategy_history(strategy_id)
                if history:
                    # Passa últimos N resultados para otimização
                    strategy.optimize_parameters(history[-10:])
                    self.logger.info(f"Parâmetros adaptados para estratégia: {strategy_id}")
        
        except Exception as e:
            self.logger.error(
                f"Erro ao adaptar parâmetros da estratégia {strategy_id}: {str(e)}"
            )
    
    def run_maintenance(self):
        """Executa manutenção periódica do sistema"""
        try:
            self.logger.info("Iniciando manutenção do sistema")
            
            # Verifica estratégias em declínio
            for strategy_id in list(self.strategies.keys()):
                if self.evaluator.should_retire_strategy(strategy_id):
                    self.retire_strategy(strategy_id)
                else:
                    self.adapt_strategy_parameters(strategy_id)
            
            # Atualiza portfólio
            self.update_portfolio()
            
            self.logger.info("Manutenção do sistema concluída")
        
        except Exception as e:
            self.logger.error(f"Erro durante manutenção do sistema: {str(e)}")
    
    def get_system_status(self) -> Dict:
        """Retorna status atual do sistema"""
        return {
            'active_strategies': len(self.strategies),
            'portfolio_metrics': self.portfolio.get_portfolio_metrics(),
            'top_strategies': [
                {
                    'id': sid,
                    'weight': weight,
                    'allocation': self.portfolio.allocations[sid].current_allocation
                }
                for sid, weight in self.portfolio.get_strategy_ranking()[:5]
            ]
        }