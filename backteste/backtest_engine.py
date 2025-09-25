import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

@dataclass
class BacktestResult:
    """Resultados do backteste de uma estratégia"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    returns: List[float]
    trades: List[Dict]
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    risk_adjusted_return: float
    market_conditions: Dict

class MarketCondition(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    LOW_VOLATILITY = "low_volatility"

class BacktestEngine:
    def __init__(self):
        self.historical_data = {}
        self.results_cache = {}
        self.market_conditions = {}
    
    def detect_market_condition(self, data: pd.DataFrame, window: int = 20) -> MarketCondition:
        """Detecta condição atual do mercado baseado em indicadores"""
        returns = data['close'].pct_change()
        volatility = returns.rolling(window).std()
        trend = data['close'].rolling(window).mean()
        
        current_volatility = volatility.iloc[-1]
        avg_volatility = volatility.mean()
        price_trend = (trend.iloc[-1] - trend.iloc[-window]) / trend.iloc[-window]
        
        if current_volatility > avg_volatility * 1.5:
            return MarketCondition.VOLATILE
        elif current_volatility < avg_volatility * 0.5:
            return MarketCondition.LOW_VOLATILITY
        elif price_trend > 0.05:
            return MarketCondition.BULL
        elif price_trend < -0.05:
            return MarketCondition.BEAR
        else:
            return MarketCondition.SIDEWAYS
    
    def run_backtest(
        self,
        strategy,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0
    ) -> BacktestResult:
        """Executa backtesting de uma estratégia"""
        # Carrega dados históricos
        data = self.load_historical_data(symbol, start_date, end_date)
        
        # Detecta condições de mercado durante o período
        market_conditions = {
            'start': self.detect_market_condition(data.head(20)),
            'middle': self.detect_market_condition(data.iloc[len(data)//2-10:len(data)//2+10]),
            'end': self.detect_market_condition(data.tail(20))
        }
        
        # Executa a estratégia
        positions = []
        trades = []
        capital = initial_capital
        current_position = None
        
        for i in range(len(data)):
            current_bar = data.iloc[i]
            signal = strategy.generate_signal(data.iloc[:i+1])
            
            if signal != 0 and current_position is None:
                # Abre posição
                current_position = {
                    'type': 'long' if signal > 0 else 'short',
                    'entry_price': current_bar['close'],
                    'entry_time': current_bar.name,
                    'size': capital * 0.02 / current_bar['close']  # 2% do capital por trade
                }
                positions.append(current_position)
            
            elif signal == 0 and current_position is not None:
                # Fecha posição
                exit_price = current_bar['close']
                pnl = (exit_price - current_position['entry_price']) * current_position['size']
                if current_position['type'] == 'short':
                    pnl *= -1
                
                trades.append({
                    'entry_time': current_position['entry_time'],
                    'exit_time': current_bar.name,
                    'entry_price': current_position['entry_price'],
                    'exit_price': exit_price,
                    'type': current_position['type'],
                    'pnl': pnl
                })
                
                capital += pnl
                current_position = None
        
        # Calcula métricas
        returns = [trade['pnl'] / initial_capital for trade in trades]
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        total_trades = len(trades)
        
        result = BacktestResult(
            strategy_id=strategy.id,
            start_date=start_date,
            end_date=end_date,
            returns=returns,
            trades=trades,
            sharpe_ratio=self.calculate_sharpe_ratio(returns),
            max_drawdown=self.calculate_max_drawdown(returns),
            win_rate=winning_trades / total_trades if total_trades > 0 else 0,
            profit_factor=self.calculate_profit_factor(trades),
            risk_adjusted_return=self.calculate_risk_adjusted_return(returns),
            market_conditions=market_conditions
        )
        
        # Cache o resultado
        self.results_cache[strategy.id] = result
        return result
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calcula o Sharpe Ratio dos retornos"""
        if not returns:
            return 0.0
        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # Assume retornos diários
        if len(returns) > 1:
            return np.mean(excess_returns) / np.std(excess_returns, ddof=1) * np.sqrt(252)
        return 0.0
    
    def calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calcula o máximo drawdown da série de retornos"""
        if not returns:
            return 0.0
        cumulative = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = cumulative / running_max - 1
        return abs(min(drawdowns))
    
    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Calcula o fator de lucro (soma dos lucros / soma das perdas)"""
        profits = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        losses = sum(abs(t['pnl']) for t in trades if t['pnl'] < 0)
        return profits / losses if losses != 0 else float('inf')
    
    def calculate_risk_adjusted_return(self, returns: List[float]) -> float:
        """Calcula retorno ajustado ao risco"""
        if not returns:
            return 0.0
        return np.mean(returns) / (np.std(returns) if np.std(returns) > 0 else 1)
    
    def load_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Carrega dados históricos do ativo"""
        key = f"{symbol}_{start_date}_{end_date}"
        if key not in self.historical_data:
            # TODO: Implementar carregamento de dados de fonte externa
            pass
        return self.historical_data[key]

    def validate_strategy(
        self,
        strategy,
        symbol: str,
        validation_periods: List[Tuple[datetime, datetime]]
    ) -> Dict:
        """Valida estratégia em múltiplos períodos para evitar overfitting"""
        results = []
        for start_date, end_date in validation_periods:
            result = self.run_backtest(strategy, symbol, start_date, end_date)
            results.append(result)
        
        # Análise de consistência
        sharpe_ratios = [r.sharpe_ratio for r in results]
        drawdowns = [r.max_drawdown for r in results]
        win_rates = [r.win_rate for r in results]
        
        return {
            'mean_sharpe': np.mean(sharpe_ratios),
            'sharpe_std': np.std(sharpe_ratios),
            'mean_drawdown': np.mean(drawdowns),
            'mean_win_rate': np.mean(win_rates),
            'consistency_score': self.calculate_consistency_score(results)
        }
    
    def calculate_consistency_score(self, results: List[BacktestResult]) -> float:
        """Calcula pontuação de consistência baseada em múltiplos backtests"""
        if not results:
            return 0.0
        
        # Pesos para diferentes métricas
        weights = {
            'sharpe': 0.3,
            'drawdown': 0.2,
            'win_rate': 0.2,
            'profit_factor': 0.3
        }
        
        # Calcula scores normalizados para cada métrica
        sharpe_scores = [r.sharpe_ratio for r in results]
        drawdown_scores = [1 - r.max_drawdown for r in results]  # Menor drawdown é melhor
        win_rate_scores = [r.win_rate for r in results]
        profit_factor_scores = [min(r.profit_factor, 3) / 3 for r in results]  # Limita em 3 para normalização
        
        # Calcula média ponderada
        final_score = (
            np.mean(sharpe_scores) * weights['sharpe'] +
            np.mean(drawdown_scores) * weights['drawdown'] +
            np.mean(win_rate_scores) * weights['win_rate'] +
            np.mean(profit_factor_scores) * weights['profit_factor']
        )
        
        return final_score