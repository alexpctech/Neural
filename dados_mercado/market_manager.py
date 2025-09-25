"""
Gerenciador central de dados de mercado.
Unifica o acesso a diferentes APIs e fontes de dados.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import numpy as np
from .connectors.finnhub import FinnhubConnector
from .connectors.alpha_vantage import AlphaVantageConnector
from .connectors.news_api import NewsAPIConnector
from .market_levels_analyzer import MarketLevelsAnalyzer

class MarketDataManager:
    def __init__(self):
        """Inicializa todos os conectores."""
        self.logger = logging.getLogger(__name__)
        self.finnhub = FinnhubConnector()
        self.alpha_vantage = AlphaVantageConnector()
        self.news_api = NewsAPIConnector()
        self.market_analyzer = MarketLevelsAnalyzer()
        
        # Cache para otimização
        self._cache = {}
        self._cache_timeout = 300  # 5 minutos
        
    async def __aenter__(self):
        """Gerencia o contexto assíncrono dos conectores."""
        await asyncio.gather(
            self.finnhub.__aenter__(),
            self.alpha_vantage.__aenter__(),
            self.news_api.__aenter__()
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Limpa recursos ao sair do contexto."""
        await asyncio.gather(
            self.finnhub.__aexit__(exc_type, exc_val, exc_tb),
            self.alpha_vantage.__aexit__(exc_type, exc_val, exc_tb),
            self.news_api.__aexit__(exc_type, exc_val, exc_tb)
        )
        
    async def get_market_data(self, 
                            symbol: str,
                            include_news: bool = True) -> Dict[str, Any]:
        """
        Obtém dados completos do mercado para um ativo.
        
        Args:
            symbol: Símbolo do ativo
            include_news: Incluir notícias relacionadas
            
        Returns:
            Dados consolidados do mercado
        """
        # Executa requisições em paralelo
        tasks = [
            self.finnhub.get_real_time_data(symbol),
            self.finnhub.get_order_book(symbol),
            self.alpha_vantage.get_technical_indicators(symbol, "RSI")
        ]
        
        if include_news:
            tasks.append(self.news_api.get_company_news(symbol))
            
        results = await asyncio.gather(*tasks)
        
        # Consolida resultados
        data = {
            "real_time": results[0],
            "order_book": results[1],
            "technical": results[2]
        }
        
        if include_news:
            data["news"] = results[3]
            
        return data
        
    async def get_historical_analysis(self,
                                    symbol: str,
                                    start_date: datetime,
                                    end_date: datetime) -> Dict[str, Any]:
        """
        Obtém análise histórica completa.
        
        Args:
            symbol: Símbolo do ativo
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Análise histórica consolidada
        """
        # Dados históricos de diferentes fontes
        hist_finnhub, hist_alpha = await asyncio.gather(
            self.finnhub.get_historical_data(symbol, start_date, end_date),
            self.alpha_vantage.get_historical_data(symbol, start_date, end_date)
        )
        
        # Consolida e valida dados
        return {
            "finnhub_data": hist_finnhub,
            "alpha_vantage_data": hist_alpha,
            "analysis": self._analyze_historical_data(hist_finnhub, hist_alpha)
        }
        
    def _analyze_historical_data(self,
                               data1: List[Dict],
                               data2: List[Dict]) -> Dict[str, Any]:
        """
        Analisa e compara dados históricos de diferentes fontes.
        
        Args:
            data1: Dados da primeira fonte
            data2: Dados da segunda fonte
            
        Returns:
            Análise comparativa
        """
        try:
            # Verifica se temos dados suficientes
            if not data1 or not data2:
                return {
                    "correlation": None,
                    "divergence_points": [],
                    "quality_score": 0.0,
                    "error": "Dados insuficientes"
                }
            
            # Compara preços de fechamento
            closes1 = [d.get('close', 0) for d in data1]
            closes2 = [d.get('close', 0) for d in data2]
            
            # Calcula correlação
            import numpy as np
            correlation = np.corrcoef(closes1, closes2)[0][1]
            
            # Identifica pontos de divergência
            divergence_points = []
            for i, (c1, c2) in enumerate(zip(closes1, closes2)):
                diff_pct = abs((c1 - c2) / c1 * 100)
                if diff_pct > 1.0:  # Divergência maior que 1%
                    divergence_points.append({
                        'index': i,
                        'diff_pct': diff_pct,
                        'price1': c1,
                        'price2': c2
                    })
            
            # Calcula score de qualidade baseado na correlação
            # e número de divergências
            quality_score = correlation * (1 - len(divergence_points)/len(closes1))
            
            return {
                "correlation": correlation,
                "divergence_points": divergence_points,
                "quality_score": quality_score,
                "data_points": len(closes1)
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise histórica: {e}")
            return {
                "correlation": None,
                "divergence_points": [],
                "quality_score": 0.0,
                "error": str(e)
            }
        
    async def get_market_sentiment(self, symbol: str) -> Dict[str, float]:
        """
        Analisa sentimento do mercado combinando diferentes fontes.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Indicadores de sentimento
        """
        try:
            # Obtém notícias e dados técnicos
            news, technical = await asyncio.gather(
                self.news_api.get_company_news(symbol),
                self.alpha_vantage.get_technical_indicators(symbol, "RSI")
            )
            
            # Analisa sentimento das notícias
            news_sentiment = self._analyze_news_sentiment(news)
            
            # Analisa indicadores técnicos
            technical_sentiment = self._analyze_technical_sentiment(technical)
            
            # Combina sentimentos com pesos
            combined_sentiment = (news_sentiment * 0.3 + technical_sentiment * 0.7)
            
            return {
                "news_sentiment": news_sentiment,
                "technical_sentiment": technical_sentiment,
                "combined_sentiment": combined_sentiment,
                "last_update": datetime.now().isoformat(),
                "data_points": {
                    "news": len(news) if news else 0,
                    "technical": len(technical) if technical else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar sentimento: {e}")
            return {
                "news_sentiment": 0.0,
                "technical_sentiment": 0.0,
                "combined_sentiment": 0.0,
                "error": str(e)
            }
            
    def _analyze_news_sentiment(self, news: List[Dict]) -> float:
        """Analisa o sentimento das notícias"""
        if not news:
            return 0.0
            
        try:
            # Soma os scores de sentimento das notícias
            sentiment_sum = sum(n.get('sentiment', 0) for n in news)
            return sentiment_sum / len(news)  # Média
        except:
            return 0.0
            
    def _analyze_technical_sentiment(self, technical: Dict) -> float:
        """Analisa o sentimento baseado em indicadores técnicos"""
        if not technical:
            return 0.0
            
        try:
            rsi = technical.get('RSI', 50)  # RSI padrão é 50
            
            # Converte RSI para sentimento (-1 a 1)
            # RSI < 30: Sobrevendido (sentimento positivo)
            # RSI > 70: Sobrecomprado (sentimento negativo)
            if rsi <= 30:
                return 1.0
            elif rsi >= 70:
                return -1.0
            else:
                # Escala linear entre 30 e 70
                return (50 - rsi) / 20
                
        except:
            return 0.0
        
    async def monitor_real_time(self, 
                              symbols: List[str],
                              callback: callable,
                              interval: int = 1) -> None:
        """
        Monitora dados em tempo real.
        
        Args:
            symbols: Lista de símbolos
            callback: Função de callback para novos dados
            interval: Intervalo em segundos entre atualizações
        """
        self.logger.info(f"Iniciando monitoramento para {len(symbols)} símbolos")
        active_tasks = {}
        
        try:
            while True:
                # Cria tasks para símbolos não monitorados
                for symbol in symbols:
                    if symbol not in active_tasks:
                        self.logger.debug(f"Iniciando monitoramento para {symbol}")
                        task = asyncio.create_task(self._monitor_symbol(
                            symbol, callback, interval
                        ))
                        active_tasks[symbol] = task
                        
                # Remove símbolos que não estão mais na lista
                for symbol in list(active_tasks.keys()):
                    if symbol not in symbols:
                        self.logger.debug(f"Parando monitoramento de {symbol}")
                        active_tasks[symbol].cancel()
                        del active_tasks[symbol]
                        
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            # Cancela todas as tasks ao parar
            for task in active_tasks.values():
                task.cancel()
            await asyncio.gather(*active_tasks.values(), return_exceptions=True)
            raise
        except Exception as e:
            self.logger.error(f"Erro no monitoramento principal: {e}")
            raise
            
    async def _monitor_symbol(self,
                            symbol: str,
                            callback: callable,
                            interval: int) -> None:
        """Monitora um símbolo específico"""
        last_error_time = None
        error_count = 0
        
        while True:
            try:
                # Obtém e processa dados
                data = await self.get_market_data(symbol)
                await callback(symbol, data)
                
                # Reseta contadores de erro após sucesso
                error_count = 0
                last_error_time = None
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                error_count += 1
                current_time = datetime.now()
                
                # Registra erro com nível baseado na frequência
                if not last_error_time or \
                   (current_time - last_error_time).seconds > 300:
                    # Primeiro erro ou mais de 5 minutos desde o último
                    self.logger.warning(
                        f"Erro no monitoramento de {symbol}: {e}"
                    )
                elif error_count > 10:
                    # Muitos erros seguidos
                    self.logger.error(
                        f"Erros persistentes no monitoramento de {symbol}: {e}"
                    )
                
                last_error_time = current_time
                
                # Aumenta intervalo após erros consecutivos
                backoff = min(300, interval * (2 ** (error_count - 1)))
                await asyncio.sleep(backoff)