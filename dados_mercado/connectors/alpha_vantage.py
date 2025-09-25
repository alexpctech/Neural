"""
Conector para Alpha Vantage API.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base import MarketConnector

class AlphaVantageConnector(MarketConnector):
    def __init__(self):
        super().__init__()
        self.api_key = self.credentials.get_credential("ALPHA_VANTAGE", "api_key")
        self.base_url = "https://www.alphavantage.co/query"
        
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém cotação em tempo real.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Dados em tempo real
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        data = await self._make_request(self.base_url, params=params)
        quote = data["Global Quote"]
        
        return {
            "symbol": quote["01. symbol"],
            "price": float(quote["05. price"]),
            "change": float(quote["09. change"]),
            "change_percent": float(quote["10. change percent"].strip("%")),
            "volume": int(quote["06. volume"]),
            "latest_day": quote["07. latest trading day"]
        }
        
    async def get_historical_data(self,
                                symbol: str,
                                start_date: datetime,
                                end_date: datetime) -> List[Dict[str, Any]]:
        """
        Obtém dados históricos.
        
        Args:
            symbol: Símbolo do ativo
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de candles
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": self.api_key
        }
        
        data = await self._make_request(self.base_url, params=params)
        time_series = data["Time Series (Daily)"]
        
        candles = []
        for date, values in time_series.items():
            dt = datetime.strptime(date, "%Y-%m-%d")
            if start_date <= dt <= end_date:
                candles.append({
                    "timestamp": dt.timestamp(),
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"])
                })
                
        return sorted(candles, key=lambda x: x["timestamp"])
        
    async def get_intraday_data(self,
                               symbol: str,
                               interval: str = "1min") -> List[Dict[str, Any]]:
        """
        Obtém dados intraday.
        
        Args:
            symbol: Símbolo do ativo
            interval: Intervalo (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            Lista de candles intraday
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": "full",
            "apikey": self.api_key
        }
        
        data = await self._make_request(self.base_url, params=params)
        time_series = data[f"Time Series ({interval})"]
        
        candles = []
        for timestamp, values in time_series.items():
            candles.append({
                "timestamp": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timestamp(),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            })
            
        return sorted(candles, key=lambda x: x["timestamp"])
        
    async def get_technical_indicators(self,
                                    symbol: str,
                                    indicator: str,
                                    interval: str = "daily",
                                    time_period: int = 14) -> Dict[str, Any]:
        """
        Obtém indicadores técnicos.
        
        Args:
            symbol: Símbolo do ativo
            indicator: Indicador (SMA, EMA, RSI, etc)
            interval: Intervalo temporal
            time_period: Período do indicador
            
        Returns:
            Dados do indicador
        """
        params = {
            "function": indicator,
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "apikey": self.api_key
        }
        
        return await self._make_request(self.base_url, params=params)
        
    # Métodos herdados não implementados pela Alpha Vantage
    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("Alpha Vantage não fornece dados de book")
        
    async def get_market_depth(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("Alpha Vantage não fornece profundidade de mercado")