"""
Conector para NewsAPI - Análise de sentimento e notícias em tempo real.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .base import MarketConnector

class NewsAPIConnector(MarketConnector):
    def __init__(self):
        super().__init__()
        self.api_key = self.credentials.get_credential("NEWSAPI", "api_key")
        self.base_url = "https://newsapi.org/v2"
        
    async def get_market_news(self, 
                            query: Optional[str] = None,
                            sources: Optional[List[str]] = None,
                            from_date: Optional[datetime] = None,
                            to_date: Optional[datetime] = None,
                            language: str = "en",
                            sort_by: str = "publishedAt") -> List[Dict[str, Any]]:
        """
        Obtém notícias do mercado financeiro.
        
        Args:
            query: Termos de busca
            sources: Lista de fontes de notícias
            from_date: Data inicial
            to_date: Data final
            language: Idioma das notícias
            sort_by: Ordenação (relevancy, popularity, publishedAt)
            
        Returns:
            Lista de notícias
        """
        # Define parâmetros padrão
        if not from_date:
            from_date = datetime.now() - timedelta(days=1)
        if not to_date:
            to_date = datetime.now()
            
        # Monta query financeira
        if query:
            financial_terms = "(market OR stock OR trading OR economy OR finance)"
            query = f"{query} AND {financial_terms}"
        else:
            query = "(market OR stock OR trading OR economy OR finance)"
            
        params = {
            "q": query,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "language": language,
            "sortBy": sort_by,
            "apiKey": self.api_key
        }
        
        if sources:
            params["sources"] = ",".join(sources)
            
        endpoint = f"{self.base_url}/everything"
        response = await self._make_request(endpoint, params=params)
        
        return self._process_news(response["articles"])
        
    async def get_company_news(self, 
                             company: str,
                             days: int = 7) -> List[Dict[str, Any]]:
        """
        Obtém notícias específicas de uma empresa.
        
        Args:
            company: Nome da empresa
            days: Quantidade de dias para buscar
            
        Returns:
            Lista de notícias
        """
        from_date = datetime.now() - timedelta(days=days)
        
        return await self.get_market_news(
            query=company,
            from_date=from_date
        )
        
    async def get_breaking_news(self, category: str = "business") -> List[Dict[str, Any]]:
        """
        Obtém últimas notícias.
        
        Args:
            category: Categoria (business, technology, etc)
            
        Returns:
            Lista de notícias
        """
        endpoint = f"{self.base_url}/top-headlines"
        params = {
            "category": category,
            "language": "en",
            "apiKey": self.api_key
        }
        
        response = await self._make_request(endpoint, params=params)
        return self._process_news(response["articles"])
        
    def _process_news(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """
        Processa e formata artigos de notícias.
        
        Args:
            articles: Lista de artigos brutos
            
        Returns:
            Lista de artigos processados
        """
        processed = []
        for article in articles:
            # Converte timestamp
            if article.get("publishedAt"):
                published = datetime.fromisoformat(
                    article["publishedAt"].replace("Z", "+00:00")
                )
            else:
                published = datetime.now()
                
            processed.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article.get("url", ""),
                "source": article.get("source", {}).get("name", ""),
                "published_at": published.timestamp(),
                "author": article.get("author", ""),
                "image_url": article.get("urlToImage", "")
            })
            
        return processed
        
    # Métodos herdados não implementados
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("NewsAPI não fornece dados de mercado em tempo real")
        
    async def get_historical_data(self, symbol: str, 
                                start_date: datetime,
                                end_date: datetime) -> List[Dict[str, Any]]:
        raise NotImplementedError("NewsAPI não fornece dados históricos de mercado")
        
    async def get_order_book(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("NewsAPI não fornece dados de book")
        
    async def get_market_depth(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("NewsAPI não fornece profundidade de mercado")