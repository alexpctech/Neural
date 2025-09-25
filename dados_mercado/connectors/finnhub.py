"""
Conector para Finnhub API.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from .base import MarketConnector
import pandas as pd
import numpy as np

class FinnhubConnector(MarketConnector):
    def __init__(self):
        super().__init__()
        self.api_key = self.credentials.get_credential("FINNHUB", "api_key")
        self.base_url = "https://finnhub.io/api/v1"
        self.ws_url = "wss://ws.finnhub.io"
        
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém cotação em tempo real.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Dados em tempo real
        """
        endpoint = f"{self.base_url}/quote"
        params = {
            "symbol": symbol,
            "token": self.api_key
        }
        
        data = await self._make_request(endpoint, params=params)
        return {
            "symbol": symbol,
            "price": data["c"],
            "change": data["d"],
            "change_percent": data["dp"],
            "high": data["h"],
            "low": data["l"],
            "open": data["o"],
            "previous_close": data["pc"],
            "timestamp": data["t"]
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
        endpoint = f"{self.base_url}/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": int(start_date.timestamp()),
            "to": int(end_date.timestamp()),
            "token": self.api_key
        }
        
        data = await self._make_request(endpoint, params=params)
        
        candles = []
        for i in range(len(data["c"])):
            candles.append({
                "timestamp": data["t"][i],
                "open": data["o"][i],
                "high": data["h"][i],
                "low": data["l"][i],
                "close": data["c"][i],
                "volume": data["v"][i]
            })
            
        return candles
        
    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém livro de ofertas nivel 2.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Book de ofertas
        """
        endpoint = f"{self.base_url}/stock/depth2"
        params = {
            "symbol": symbol,
            "token": self.api_key
        }
        
        data = await self._make_request(endpoint, params=params)
        return {
            "bids": [{"price": p, "quantity": q} for p, q in zip(data["bids"]["p"], data["bids"]["v"])],
            "asks": [{"price": p, "quantity": q} for p, q in zip(data["asks"]["p"], data["asks"]["v"])]
        }
        
    async def get_market_depth(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém profundidade de mercado agregada.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Profundidade de mercado
        """
        book = await self.get_order_book(symbol)
        
        # Agrupa por níveis de preço
        def aggregate_levels(orders: List[Dict], levels: int = 10) -> List[Dict]:
            df = pd.DataFrame(orders)
            df["price_level"] = pd.qcut(df["price"], levels, labels=False)
            agg = df.groupby("price_level").agg({
                "price": "mean",
                "quantity": "sum"
            }).reset_index()
            return agg.to_dict("records")
            
        return {
            "bids": aggregate_levels(book["bids"]),
            "asks": aggregate_levels(book["asks"])
        }
        
    async def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém informações da empresa.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Dados da empresa
        """
        endpoint = f"{self.base_url}/stock/profile2"
        params = {
            "symbol": symbol,
            "token": self.api_key
        }
        
        return await self._make_request(endpoint, params=params)
        
    async def get_financials(self, symbol: str) -> Dict[str, Any]:
        """
        Obtém dados financeiros.
        
        Args:
            symbol: Símbolo do ativo
            
        Returns:
            Dados financeiros
        """
        endpoint = f"{self.base_url}/stock/metric"
        params = {
            "symbol": symbol,
            "metric": "all",
            "token": self.api_key
        }
        
        return await self._make_request(endpoint, params=params)