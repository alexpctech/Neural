"""
Classe base para conectores de mercado.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
from datetime import datetime
import logging
from .credentials import APICredentials

class MarketConnector(ABC):
    def __init__(self):
        self.credentials = APICredentials()
        self.session = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def __aenter__(self):
        """Contexto assíncrono para gerenciar sessões HTTP."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Limpa recursos ao sair do contexto."""
        if self.session:
            await self.session.close()
            
    @abstractmethod
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Obtém dados em tempo real."""
        pass
        
    @abstractmethod
    async def get_historical_data(self, symbol: str, 
                                start_date: datetime,
                                end_date: datetime) -> List[Dict[str, Any]]:
        """Obtém dados históricos."""
        pass
        
    @abstractmethod
    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """Obtém livro de ofertas."""
        pass
        
    @abstractmethod
    async def get_market_depth(self, symbol: str) -> Dict[str, Any]:
        """Obtém profundidade de mercado."""
        pass
        
    async def _make_request(self, 
                          url: str, 
                          method: str = "GET",
                          params: Optional[Dict] = None,
                          headers: Optional[Dict] = None,
                          data: Optional[Dict] = None) -> Dict:
        """
        Faz requisição HTTP com retry e rate limiting.
        
        Args:
            url: URL da requisição
            method: Método HTTP
            params: Parâmetros da query
            headers: Headers HTTP
            data: Dados para POST/PUT
            
        Returns:
            Resposta da API
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', retry_delay))
                        await asyncio.sleep(retry_after)
                        continue
                        
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                self.logger.error(f"Request error: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay * (attempt + 1))
                
        raise Exception("Max retries exceeded")