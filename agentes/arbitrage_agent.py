"""
Agente especializado em detectar e executar oportunidades de arbitragem.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime
from .abstract_agent import AbstractAgent

class ArbitrageAgent(AbstractAgent):
    def __init__(self, name: str = "ArbitrageAgent"):
        super().__init__(name)
        self.min_spread = 0.001  # 0.1% de spread mínimo
        self.max_latency = 0.5  # 500ms de latência máxima
        self.opportunities = []
        
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa oportunidades de arbitragem entre diferentes mercados."""
        try:
            # Extrai preços de diferentes mercados
            prices = self._extract_market_prices(market_data)
            
            # Detecta oportunidades
            opportunities = self._detect_arbitrage(prices)
            
            # Filtra por viabilidade
            viable_ops = self._filter_viable_opportunities(opportunities)
            
            # Calcula métricas
            if viable_ops:
                best_op = max(viable_ops, key=lambda x: x['expected_return'])
                signal_type = 'ARBITRAGE_OPPORTUNITY'
                confidence = min(0.99, best_op['expected_return'] / 0.05)
            else:
                signal_type = 'NO_OPPORTUNITY'
                confidence = 0
                best_op = None
            
            analysis = {
                'signal_type': signal_type,
                'confidence': confidence,
                'parameters': {
                    'opportunities': viable_ops,
                    'best_opportunity': best_op,
                    'total_opportunities': len(viable_ops)
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'markets_analyzed': list(prices.keys())
                }
            }
            
            self.last_analysis = analysis
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de arbitragem: {str(e)}")
            return self._error_analysis()
            
    def _extract_market_prices(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Extrai preços normalizados de diferentes mercados."""
        prices = {}
        for market, data in market_data.items():
            if 'last_price' in data:
                prices[market] = data['last_price']
            elif 'close' in data:
                prices[market] = data['close']
        return prices
        
    def _detect_arbitrage(self, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detecta oportunidades de arbitragem entre mercados."""
        opportunities = []
        markets = list(prices.keys())
        
        for i in range(len(markets)):
            for j in range(i + 1, len(markets)):
                market_a = markets[i]
                market_b = markets[j]
                
                price_a = prices[market_a]
                price_b = prices[market_b]
                
                # Calcula spread
                spread = abs(price_a - price_b) / min(price_a, price_b)
                
                if spread > self.min_spread:
                    opportunities.append({
                        'market_buy': market_a if price_a < price_b else market_b,
                        'market_sell': market_b if price_a < price_b else market_a,
                        'buy_price': min(price_a, price_b),
                        'sell_price': max(price_a, price_b),
                        'spread': spread,
                        'expected_return': spread - self.estimate_costs(market_a, market_b)
                    })
                    
        return opportunities
        
    def _filter_viable_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra oportunidades por viabilidade."""
        return [
            op for op in opportunities
            if (op['expected_return'] > 0 and
                self.check_liquidity(op) and
                self.check_latency(op))
        ]
        
    def estimate_costs(self, market_a: str, market_b: str) -> float:
        """Estima custos totais da operação."""
        # Taxas de mercado típicas
        market_fees = {
            'binance': 0.001,  # 0.1%
            'ftx': 0.0007,    # 0.07%
            'kraken': 0.0016  # 0.16%
        }
        
        # Pega taxas ou usa taxa padrão
        fee_a = market_fees.get(market_a.lower(), 0.002)
        fee_b = market_fees.get(market_b.lower(), 0.002)
        
        # Inclui slippage estimado
        slippage = 0.0005  # 0.05%
        
        return fee_a + fee_b + slippage
        
    def check_liquidity(self, opportunity: Dict[str, Any]) -> bool:
        """Verifica se há liquidez suficiente."""
        # Implementar verificação real de liquidez
        # Por enquanto retorna True para teste
        return True
        
    def check_latency(self, opportunity: Dict[str, Any]) -> bool:
        """Verifica se a latência está dentro do aceitável."""
        # Implementar verificação real de latência
        # Por enquanto retorna True para teste
        return True
        
    def update_state(self, market_data: Dict[str, Any]) -> None:
        """Atualiza estado interno com novos dados."""
        analysis = self.analyze(market_data)
        if analysis['signal_type'] == 'ARBITRAGE_OPPORTUNITY':
            self.opportunities.append(analysis['parameters']['best_opportunity'])
            # Mantém apenas últimas 100 oportunidades
            self.opportunities = self.opportunities[-100:]