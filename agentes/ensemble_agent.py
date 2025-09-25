"""
Agente ensemble que coordena e agrega sinais de todos os outros agentes.
"""
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .abstract_agent import AbstractAgent

class EnsembleNN(nn.Module):
    def __init__(self, num_agents: int):
        super().__init__()
        
        # Rede neural para agregação de sinais
        self.signal_processor = nn.Sequential(
            nn.Linear(num_agents * 3, 128),  # 3 features por agente
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3)  # [down, neutral, up]
        )
        
        # Attention para pesos dinâmicos dos agentes
        self.agent_attention = nn.MultiheadAttention(
            embed_dim=3,
            num_heads=1,
            batch_first=True
        )
        
class EnsembleAgent(AbstractAgent):
    def __init__(self, agents: List[AbstractAgent], name: str = "Ensemble", 
                 gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        
        self.agents = agents
        self.num_agents = len(agents)
        
        # Modelo de agregação
        self.model = EnsembleNN(self.num_agents)
        self.model.to(self.device)
        
        # Otimizações para GPU
        if torch.cuda.is_available():
            self.model = torch.compile(self.model)
            
        # Pesos dinâmicos dos agentes
        self.agent_weights = torch.ones(self.num_agents) / self.num_agents
        self.agent_weights = self.agent_weights.to(self.device)
        
        # Thread pool para paralelização
        self.executor = ThreadPoolExecutor(max_workers=self.num_agents)
        
        # Cache de decisões
        self.decision_cache = {}
        self.cache_duration = 30  # 30 segundos
        
    async def gather_analyses(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Coleta análises de todos os agentes de forma assíncrona."""
        loop = asyncio.get_event_loop()
        
        async def get_analysis(agent):
            return await loop.run_in_executor(
                self.executor,
                agent.analyze,
                data
            )
            
        tasks = [get_analysis(agent) for agent in self.agents]
        return await asyncio.gather(*tasks)
        
    def prepare_batch(self, analyses: List[Dict]) -> torch.Tensor:
        """Prepara batch com sinais de todos os agentes."""
        features = []
        
        for analysis in analyses:
            # Extrai características principais
            signal_strength = analysis['parameters']['strength']
            confidence = analysis['confidence']
            direction = 1 if analysis['parameters']['direction'] == 'LONG' else -1
            
            features.extend([signal_strength, confidence, direction])
            
        return torch.FloatTensor(features).view(1, -1).to(self.device)
        
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """Processa sinais agregados."""
        with torch.no_grad():
            # Reshape para attention
            agent_signals = batch.view(-1, self.num_agents, 3)
            
            # Aplica attention nos sinais dos agentes
            weighted_signals, attention_weights = self.model.agent_attention(
                agent_signals, agent_signals, agent_signals
            )
            
            # Atualiza pesos dos agentes
            self.agent_weights = attention_weights.mean(dim=0).squeeze()
            
            # Processa sinais ponderados
            signals_flat = weighted_signals.view(-1, self.num_agents * 3)
            predictions = self.model.signal_processor(signals_flat)
            
            return torch.softmax(predictions, dim=1)
            
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa mercado agregando sinais de todos os agentes."""
        # Verifica cache
        key = f"{data['symbol']}_{data['timestamp']}"
        now = datetime.now().timestamp()
        if key in self.decision_cache:
            cached_time, cached_result = self.decision_cache[key]
            if now - cached_time < self.cache_duration:
                return cached_result
                
        # Coleta análises de todos os agentes
        analyses = await self.gather_analyses(data)
        
        # Prepara batch com todos os sinais
        batch = self.prepare_batch(analyses)
        
        # Processa na GPU
        ensemble_prediction = self.process_batch(batch)
        pred = ensemble_prediction[0]  # [down, neutral, up]
        
        # Calcula decisão final
        direction = pred[2].item() - pred[0].item()  # up - down
        confidence = torch.max(pred).item()
        
        # Coleta votos individuais
        agent_votes = {
            agent.name: {
                'direction': analysis['parameters']['direction'],
                'confidence': analysis['confidence'],
                'weight': weight.item()
            }
            for agent, analysis, weight in zip(self.agents, analyses, self.agent_weights)
        }
        
        # Gera análise final
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'prediction': direction,
            'confidence': confidence,
            'signal_type': 'ENSEMBLE',
            'parameters': {
                'score': direction,
                'direction': 'LONG' if direction > 0 else 'SHORT',
                'strength': abs(direction)
            },
            'metadata': {
                'symbol': data['symbol'],
                'agent_votes': agent_votes,
                'scores': {
                    'down': pred[0].item(),
                    'neutral': pred[1].item(),
                    'up': pred[2].item()
                }
            }
        }
        
        # Atualiza cache
        self.decision_cache[key] = (now, analysis)
        self.last_analysis = analysis
        
        return analysis
        
    def update_state(self, market_data: Dict[str, Any]) -> None:
        """Atualiza estado de todos os agentes."""
        # Atualiza agentes individuais
        for agent in self.agents:
            agent.update_state(market_data)
            
        # Limpa cache antigo
        now = datetime.now().timestamp()
        self.decision_cache = {
            k: v for k, v in self.decision_cache.items()
            if now - v[0] < self.cache_duration
        }
        
    def handle_signal(self, message: Dict[str, Any]) -> None:
        """Processa sinais externos."""
        # Repassa sinais relevantes para agentes específicos
        for agent in self.agents:
            if message['target_agent'] in [agent.name, 'ALL']:
                agent.handle_signal(message)
                
    def handle_feedback(self, message: Dict[str, Any]) -> None:
        """Processa feedback sobre decisões anteriores."""
        if message['type'] == 'PREDICTION_FEEDBACK':
            # Ajusta pesos dos agentes com base no feedback
            for agent_name, vote in message['agent_votes'].items():
                idx = next(i for i, a in enumerate(self.agents) if a.name == agent_name)
                if message['success']:
                    self.agent_weights[idx] *= 1.02
                else:
                    self.agent_weights[idx] *= 0.98
                    
            # Renormaliza pesos
            self.agent_weights /= self.agent_weights.sum()
            
            # Repassa feedback para agentes individuais
            for agent in self.agents:
                agent.handle_feedback(message)
                
    def cleanup(self) -> None:
        """Limpa recursos de todos os agentes."""
        for agent in self.agents:
            agent.cleanup()
        self.optimize_memory()
        self.decision_cache.clear()
        self.executor.shutdown()