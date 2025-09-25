from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum

class MarketEventType(Enum):
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    SUPPORT = "support"
    RESISTANCE = "resistance"
    CONSOLIDATION = "consolidation"
    VWAP_CROSS = "vwap_cross"
    NEWS_EVENT = "news_event"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    ADJUSTMENT = "adjustment"

@dataclass
class MarketLevel:
    """Representa um nível importante de mercado"""
    price: float
    level_type: MarketEventType
    strength: float  # 0-1, indica força do nível
    time_frame: str
    last_test: datetime
    test_count: int
    validation_count: int

@dataclass
class NewsEvent:
    """Representa um evento de notícia importante"""
    timestamp: datetime
    event_type: str
    importance: int  # 1-3
    expected_impact: float  # -1 a 1
    actual_impact: Optional[float] = None

class MarketLevelsAnalyzer:
    def __init__(self):
        self.levels: Dict[str, List[MarketLevel]] = {}  # Por símbolo
        self.news_events: Dict[str, List[NewsEvent]] = {}
        self.consolidation_zones: Dict[str, List[Tuple[float, float]]] = {}
        self.vwap_data: Dict[str, pd.DataFrame] = {}
        
    def analyze_market_structure(
        self,
        symbol: str,
        data: pd.DataFrame,
        timeframe: str = "1d"
    ) -> Dict[str, List[MarketLevel]]:
        """Analisa estrutura do mercado para identificar níveis importantes"""
        
        # Reset níveis para o símbolo
        self.levels[symbol] = []
        
        # Calcula VWAP
        self.vwap_data[symbol] = self._calculate_vwap(data)
        
        # Identifica suportes e resistências
        pivots = self._find_pivot_points(data)
        for price, strength in pivots:
            level_type = MarketEventType.RESISTANCE if self._is_resistance(data, price) else MarketEventType.SUPPORT
            self.levels[symbol].append(
                MarketLevel(
                    price=price,
                    level_type=level_type,
                    strength=strength,
                    time_frame=timeframe,
                    last_test=data.index[-1],
                    test_count=self._count_level_tests(data, price),
                    validation_count=self._count_level_validations(data, price)
                )
            )
        
        # Identifica zonas de consolidação
        consolidation_zones = self._find_consolidation_zones(data)
        self.consolidation_zones[symbol] = consolidation_zones
        
        # Identifica breakouts e pullbacks
        breakouts = self._identify_breakouts(data, self.levels[symbol])
        for price, strength in breakouts:
            self.levels[symbol].append(
                MarketLevel(
                    price=price,
                    level_type=MarketEventType.BREAKOUT,
                    strength=strength,
                    time_frame=timeframe,
                    last_test=data.index[-1],
                    test_count=1,
                    validation_count=1
                )
            )
        
        return self.levels[symbol]
    
    def _calculate_vwap(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula VWAP para os dados fornecidos"""
        df = data.copy()
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['hlc3_vol'] = df['hlc3'] * df['volume']
        df['cum_vol'] = df['volume'].cumsum()
        df['vwap'] = df['hlc3_vol'].cumsum() / df['cum_vol']
        return df
    
    def _find_pivot_points(self, data: pd.DataFrame, window: int = 20) -> List[Tuple[float, float]]:
        """Encontra pontos de pivô (suporte/resistência)"""
        pivots = []
        for i in range(window, len(data) - window):
            if self._is_pivot_high(data, i, window):
                strength = self._calculate_level_strength(data, data.iloc[i]['high'], window)
                pivots.append((data.iloc[i]['high'], strength))
            elif self._is_pivot_low(data, i, window):
                strength = self._calculate_level_strength(data, data.iloc[i]['low'], window)
                pivots.append((data.iloc[i]['low'], strength))
        return pivots
    
    def _is_pivot_high(self, data: pd.DataFrame, idx: int, window: int) -> bool:
        """Verifica se é um pivô de alta"""
        current_high = data.iloc[idx]['high']
        left_window = data.iloc[idx-window:idx]['high']
        right_window = data.iloc[idx+1:idx+window+1]['high']
        return all(current_high >= price for price in left_window) and \
               all(current_high >= price for price in right_window)
    
    def _is_pivot_low(self, data: pd.DataFrame, idx: int, window: int) -> bool:
        """Verifica se é um pivô de baixa"""
        current_low = data.iloc[idx]['low']
        left_window = data.iloc[idx-window:idx]['low']
        right_window = data.iloc[idx+1:idx+window+1]['low']
        return all(current_low <= price for price in left_window) and \
               all(current_low <= price for price in right_window)
    
    def _calculate_level_strength(self, data: pd.DataFrame, price: float, window: int) -> float:
        """Calcula força de um nível baseado em volume e número de testes"""
        price_range = 0.001 * price  # 0.1% do preço
        touches = data[
            (data['high'] >= price - price_range) &
            (data['low'] <= price + price_range)
        ]
        
        if len(touches) == 0:
            return 0.0
        
        # Força baseada em volume e número de testes
        volume_score = touches['volume'].sum() / data['volume'].sum()
        test_score = len(touches) / len(data)
        
        return (volume_score * 0.7 + test_score * 0.3)
    
    def _find_consolidation_zones(
        self,
        data: pd.DataFrame,
        min_period: int = 10,
        volatility_threshold: float = 0.02
    ) -> List[Tuple[float, float]]:
        """Identifica zonas de consolidação"""
        zones = []
        volatility = data['close'].pct_change().rolling(min_period).std()
        
        i = 0
        while i < len(data) - min_period:
            if volatility.iloc[i] <= volatility_threshold:
                start_idx = i
                while i < len(volatility) and volatility.iloc[i] <= volatility_threshold:
                    i += 1
                end_idx = i
                
                if end_idx - start_idx >= min_period:
                    period_data = data.iloc[start_idx:end_idx]
                    zones.append((
                        period_data['low'].min(),
                        period_data['high'].max()
                    ))
            i += 1
        
        return zones
    
    def _identify_breakouts(
        self,
        data: pd.DataFrame,
        levels: List[MarketLevel]
    ) -> List[Tuple[float, float]]:
        """Identifica breakouts de níveis importantes"""
        breakouts = []
        
        for level in levels:
            # Procura por candles que rompem o nível
            for i in range(1, len(data)):
                prev_candle = data.iloc[i-1]
                curr_candle = data.iloc[i]
                
                # Verifica rompimento para cima
                if prev_candle['high'] < level.price and curr_candle['close'] > level.price:
                    strength = self._calculate_breakout_strength(data, i, level.price, True)
                    breakouts.append((curr_candle['close'], strength))
                
                # Verifica rompimento para baixo
                elif prev_candle['low'] > level.price and curr_candle['close'] < level.price:
                    strength = self._calculate_breakout_strength(data, i, level.price, False)
                    breakouts.append((curr_candle['close'], strength))
        
        return breakouts
    
    def _calculate_breakout_strength(
        self,
        data: pd.DataFrame,
        breakout_idx: int,
        level_price: float,
        is_upward: bool
    ) -> float:
        """Calcula força de um breakout"""
        breakout_candle = data.iloc[breakout_idx]
        
        # Fatores que influenciam a força do breakout
        volume_ratio = breakout_candle['volume'] / data['volume'].mean()
        price_move = abs(breakout_candle['close'] - level_price) / level_price
        body_ratio = abs(breakout_candle['close'] - breakout_candle['open']) / \
                    (breakout_candle['high'] - breakout_candle['low'])
        
        # Normaliza os fatores
        volume_score = min(volume_ratio / 3, 1)  # Máximo 3x volume médio
        move_score = min(price_move / 0.02, 1)   # Máximo 2% de movimento
        body_score = min(body_ratio, 1)          # Máximo 1 (candle perfeito)
        
        # Combina os fatores com pesos
        return (volume_score * 0.4 + move_score * 0.4 + body_score * 0.2)
    
    def should_wait_for_confirmation(
        self,
        symbol: str,
        current_price: float,
        timeframe: str = "1d"
    ) -> Tuple[bool, str]:
        """Determina se deve esperar confirmação antes de operar"""
        if symbol not in self.levels:
            return False, "Sem níveis importantes registrados"
        
        # Verifica proximidade com níveis importantes
        for level in self.levels[symbol]:
            price_diff = abs(current_price - level.price) / current_price
            
            # Se preço está muito próximo de um nível forte
            if price_diff < 0.001 and level.strength > 0.7:  # 0.1% do preço
                return True, f"Próximo a {level.level_type.value} forte"
        
        # Verifica zonas de consolidação
        if symbol in self.consolidation_zones:
            for low, high in self.consolidation_zones[symbol]:
                if low <= current_price <= high:
                    return True, "Dentro de zona de consolidação"
        
        # Verifica proximidade com VWAP
        if symbol in self.vwap_data:
            vwap = self.vwap_data[symbol]['vwap'].iloc[-1]
            vwap_diff = abs(current_price - vwap) / current_price
            if vwap_diff < 0.001:  # 0.1% do VWAP
                return True, "Próximo ao VWAP"
        
        # Verifica eventos de notícias próximos
        if symbol in self.news_events:
            for event in self.news_events[symbol]:
                if event.importance >= 2:  # Eventos importantes
                    time_diff = abs((datetime.now() - event.timestamp).total_seconds())
                    if time_diff < 1800:  # 30 minutos
                        return True, "Próximo a notícia importante"
        
        return False, "Sem eventos significativos"
    
    def is_suitable_for_scalping(
        self,
        symbol: str,
        current_data: pd.DataFrame
    ) -> Tuple[bool, float]:
        """Determina se é apropriado fazer scalping no momento"""
        if len(current_data) < 20:
            return False, 0.0
        
        # Calcula volatilidade recente
        volatility = current_data['close'].pct_change().std()
        avg_volume = current_data['volume'].mean()
        
        # Condições ideais para scalping
        sufficient_volatility = 0.0005 < volatility < 0.002  # 0.05% a 0.2%
        sufficient_volume = current_data['volume'].iloc[-1] > avg_volume
        
        # Verifica se não está próximo a níveis importantes
        away_from_levels = True
        if symbol in self.levels:
            current_price = current_data['close'].iloc[-1]
            for level in self.levels[symbol]:
                price_diff = abs(current_price - level.price) / current_price
                if price_diff < 0.002:  # 0.2% do preço
                    away_from_levels = False
                    break
        
        score = (
            (sufficient_volatility * 0.4) +
            (sufficient_volume * 0.3) +
            (away_from_levels * 0.3)
        )
        
        return score > 0.7, score
    
    def is_suitable_for_hft(
        self,
        symbol: str,
        current_data: pd.DataFrame,
        tick_data: pd.DataFrame
    ) -> Tuple[bool, float]:
        """Determina se é apropriado usar HFT no momento"""
        if len(tick_data) < 100:
            return False, 0.0
        
        # Análise de microestrutura
        tick_volatility = tick_data['price'].diff().std()
        avg_tick_volume = tick_data['volume'].mean()
        spread = tick_data['ask'] - tick_data['bid']
        
        # Condições ideais para HFT
        low_spread = spread.mean() < tick_data['price'].mean() * 0.0001  # Spread < 0.01%
        high_liquidity = all(tick_data['volume'] > avg_tick_volume * 0.5)
        stable_volatility = tick_volatility < tick_data['price'].mean() * 0.0001
        
        # Verifica ausência de eventos importantes
        no_important_events = True
        if symbol in self.news_events:
            for event in self.news_events[symbol]:
                if event.importance >= 2:
                    time_diff = abs((datetime.now() - event.timestamp).total_seconds())
                    if time_diff < 3600:  # 1 hora
                        no_important_events = False
                        break
        
        score = (
            (low_spread * 0.3) +
            (high_liquidity * 0.3) +
            (stable_volatility * 0.2) +
            (no_important_events * 0.2)
        )
        
        return score > 0.8, score
    
    def register_news_event(self, symbol: str, event: NewsEvent):
        """Registra um evento de notícia"""
        if symbol not in self.news_events:
            self.news_events[symbol] = []
        self.news_events[symbol].append(event)
        
        # Limpa eventos antigos
        self.news_events[symbol] = [
            e for e in self.news_events[symbol]
            if (datetime.now() - e.timestamp).days < 7
        ]
    
    def update_level_validation(self, symbol: str, price: float, validated: bool):
        """Atualiza validação de um nível após um teste"""
        if symbol not in self.levels:
            return
        
        for level in self.levels[symbol]:
            price_diff = abs(price - level.price) / price
            if price_diff < 0.001:  # 0.1% do preço
                level.test_count += 1
                if validated:
                    level.validation_count += 1
                level.strength = level.validation_count / level.test_count