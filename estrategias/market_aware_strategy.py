from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import numpy as np

from dados_mercado.market_levels_analyzer import (
    MarketLevelsAnalyzer,
    MarketLevel,
    MarketEventType,
    NewsEvent
)

class TradingMode(Enum):
    NORMAL = "normal"
    SCALPING = "scalping"
    HFT = "hft"
    WAITING = "waiting"

@dataclass
class TradingDecision:
    """Representa uma decisão de trading"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    mode: TradingMode
    reason: str
    levels: List[MarketLevel]
    timestamp: datetime

class MarketAwareStrategy:
    """Estratégia base que considera níveis importantes de mercado"""
    
    def __init__(self):
        self.market_analyzer = MarketLevelsAnalyzer()
        self.min_confirmation_confidence = 0.7
        self.scalping_threshold = 0.7
        self.hft_threshold = 0.8
    
    def analyze_market_context(
        self,
        symbol: str,
        data: Dict,
        tick_data: Optional[Dict] = None
    ) -> TradingDecision:
        """Analisa contexto de mercado para tomada de decisão"""
        
        # Atualiza análise de níveis
        levels = self.market_analyzer.analyze_market_structure(
            symbol,
            data['ohlcv'],
            data['timeframe']
        )
        
        current_price = data['ohlcv']['close'].iloc[-1]
        
        # Verifica se deve esperar confirmação
        should_wait, wait_reason = self.market_analyzer.should_wait_for_confirmation(
            symbol,
            current_price
        )
        
        if should_wait:
            return TradingDecision(
                symbol=symbol,
                action='HOLD',
                confidence=1.0,
                mode=TradingMode.WAITING,
                reason=wait_reason,
                levels=levels,
                timestamp=datetime.now()
            )
        
        # Verifica se condições são apropriadas para scalping
        can_scalp, scalp_score = self.market_analyzer.is_suitable_for_scalping(
            symbol,
            data['ohlcv']
        )
        
        # Verifica se condições são apropriadas para HFT
        can_hft = False
        hft_score = 0.0
        if tick_data is not None:
            can_hft, hft_score = self.market_analyzer.is_suitable_for_hft(
                symbol,
                data['ohlcv'],
                tick_data
            )
        
        # Determina modo de operação
        if can_hft and hft_score >= self.hft_threshold:
            mode = TradingMode.HFT
            strategy_signal = self.generate_hft_signal(data, tick_data)
        elif can_scalp and scalp_score >= self.scalping_threshold:
            mode = TradingMode.SCALPING
            strategy_signal = self.generate_scalping_signal(data)
        else:
            mode = TradingMode.NORMAL
            strategy_signal = self.generate_normal_signal(data)
        
        return TradingDecision(
            symbol=symbol,
            action=strategy_signal['action'],
            confidence=strategy_signal['confidence'],
            mode=mode,
            reason=strategy_signal['reason'],
            levels=levels,
            timestamp=datetime.now()
        )
    
    def generate_normal_signal(self, data: Dict) -> Dict:
        """Gera sinal para modo normal de operação"""
        # Implementado nas classes derivadas
        raise NotImplementedError
    
    def generate_scalping_signal(self, data: Dict) -> Dict:
        """Gera sinal para modo scalping"""
        # Implementado nas classes derivadas
        raise NotImplementedError
    
    def generate_hft_signal(self, data: Dict, tick_data: Dict) -> Dict:
        """Gera sinal para modo HFT"""
        # Implementado nas classes derivadas
        raise NotImplementedError
    
    def handle_market_event(
        self,
        symbol: str,
        event_type: MarketEventType,
        price: float,
        validated: bool = True
    ):
        """Processa evento de mercado"""
        self.market_analyzer.update_level_validation(symbol, price, validated)
    
    def handle_news_event(self, symbol: str, event: NewsEvent):
        """Processa evento de notícia"""
        self.market_analyzer.register_news_event(symbol, event)
    
    def get_market_context(self, symbol: str) -> Dict:
        """Retorna contexto atual do mercado"""
        return {
            'levels': self.market_analyzer.levels.get(symbol, []),
            'consolidation_zones': self.market_analyzer.consolidation_zones.get(symbol, []),
            'news_events': self.market_analyzer.news_events.get(symbol, [])
        }