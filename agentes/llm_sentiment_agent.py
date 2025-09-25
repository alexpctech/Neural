"""
Agente que utiliza LLM para análise de sentimento do mercado.
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

from .abstract_agent import AbstractAgent

class LLMSentimentAgent(AbstractAgent):
    def __init__(self, name: str = "LLMSentiment", gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        
        # Carrega modelo pré-treinado otimizado para GPU
        self.model_name = "ProsusAI/finbert"  # Modelo especializado em finanças
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        
        # Otimizações para GPU
        if torch.cuda.is_available():
            self.model = torch.compile(self.model)  # Usa torch.compile para otimização
            
        # Cache de análises recentes
        self.sentiment_cache = {}
        self.cache_duration = 300  # 5 minutos
        
    def prepare_batch(self, data: List[Dict]) -> torch.Tensor:
        """Prepara batch de textos para análise."""
        texts = [d['text'] for d in data]
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        return {k: v.to(self.device) for k, v in encoded.items()}
        
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """Executa forward pass do modelo."""
        with torch.no_grad():
            outputs = self.model(**batch)
            return torch.softmax(outputs.logits, dim=1)
            
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa sentimento do mercado usando LLM."""
        # Verifica cache
        key = data.get('text', '')[:100]  # Usa primeiros 100 chars como key
        now = datetime.now().timestamp()
        if key in self.sentiment_cache:
            cached_time, cached_result = self.sentiment_cache[key]
            if now - cached_time < self.cache_duration:
                return cached_result
                
        # Prepara dados
        batch = self.prepare_batch([data])
        
        # Processa na GPU
        scores = self.process_batch(batch)
        sentiment_score = scores[0]  # [negative, neutral, positive]
        
        # Calcula métricas
        sentiment = sentiment_score[2].item() - sentiment_score[0].item()  # positive - negative
        confidence = torch.max(sentiment_score).item()
        
        # Gera análise
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'sentiment': sentiment,
            'confidence': confidence,
            'signal_type': 'SENTIMENT',
            'parameters': {
                'score': sentiment,
                'direction': 'LONG' if sentiment > 0 else 'SHORT',
                'strength': abs(sentiment)
            },
            'metadata': {
                'model': self.model_name,
                'text_sample': key,
                'scores': {
                    'negative': sentiment_score[0].item(),
                    'neutral': sentiment_score[1].item(),
                    'positive': sentiment_score[2].item()
                }
            }
        }
        
        # Atualiza cache
        self.sentiment_cache[key] = (now, analysis)
        self.last_analysis = analysis
        
        return analysis
        
    def update_state(self, market_data: Dict[str, Any]) -> None:
        """Atualiza estado com novos dados de mercado."""
        # Limpa cache antigo
        now = datetime.now().timestamp()
        self.sentiment_cache = {
            k: v for k, v in self.sentiment_cache.items()
            if now - v[0] < self.cache_duration
        }
        
    def handle_signal(self, message: Dict[str, Any]) -> None:
        """Processa sinais de outros agentes."""
        # Ajusta threshold de confiança com base em sinais correlacionados
        if message['type'] == 'MARKET_SENTIMENT':
            if message['confidence'] > 0.9:  # Alta confiança de outro agente
                self.confidence_threshold *= 0.95  # Reduz threshold
                
    def handle_feedback(self, message: Dict[str, Any]) -> None:
        """Processa feedback sobre previsões anteriores."""
        if message['type'] == 'PREDICTION_FEEDBACK':
            # Ajusta parâmetros com base no feedback
            if message['success']:
                self.confidence_threshold *= 0.98  # Reduz se acertou
            else:
                self.confidence_threshold *= 1.02  # Aumenta se errou
                
            # Mantém threshold em limites razoáveis
            self.confidence_threshold = max(0.6, min(0.9, self.confidence_threshold))
            
    def cleanup(self) -> None:
        """Limpa recursos da GPU."""
        self.optimize_memory()
        self.sentiment_cache.clear()