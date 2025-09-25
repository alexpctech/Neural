"""
Agente de análise técnica usando deep learning.
"""
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime

from .abstract_agent import AbstractAgent

class TechnicalNN(nn.Module):
    def __init__(self, input_size: int):
        super().__init__()
        
        # Arquitetura otimizada para GPU
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(input_size, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.MaxPool1d(2)
        )
        
        self.lstm = nn.LSTM(
            input_size=128,
            hidden_size=128,
            num_layers=2,
            dropout=0.2,
            batch_first=True
        )
        
        self.attention = nn.MultiheadAttention(
            embed_dim=128,
            num_heads=4,
            batch_first=True
        )
        
        self.predictor = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3)  # [down, neutral, up]
        )
        
class TechnicalAgent(AbstractAgent):
    def __init__(self, name: str = "TechnicalDL", gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        
        # Configuração do modelo
        self.input_size = 10  # Número de indicadores técnicos
        self.sequence_length = 100  # Tamanho da sequência temporal
        self.model = TechnicalNN(self.input_size)
        self.model.to(self.device)
        
        # Otimizações para GPU
        if torch.cuda.is_available():
            self.model = torch.compile(self.model)
            self.scaler = torch.cuda.amp.GradScaler()
            
        # Indicadores técnicos utilizados
        self.indicators = [
            'close', 'volume', 'rsi', 'macd', 'bollinger_upper',
            'bollinger_lower', 'stochastic_k', 'stochastic_d',
            'atr', 'obv'
        ]
        
        # Cache de análises recentes
        self.analysis_cache = {}
        self.cache_duration = 60  # 1 minuto
        
    def calculate_indicators(self, data: Dict[str, Any]) -> np.ndarray:
        """Calcula indicadores técnicos."""
        df = data['ohlcv']  # Assume DataFrame com OHLCV
        
        indicators = []
        
        # Normalização e cálculo de indicadores
        close = df['close'].values
        volume = df['volume'].values
        
        # RSI
        delta = np.diff(close)
        gain = (delta > 0) * delta
        loss = (delta < 0) * -delta
        avg_gain = np.convolve(gain, np.ones(14)/14, mode='valid')
        avg_loss = np.convolve(loss, np.ones(14)/14, mode='valid')
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        
        # Bollinger Bands
        sma = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        bollinger_upper = sma + (std * 2)
        bollinger_lower = sma - (std * 2)
        
        # Stochastic
        low_min = df['low'].rolling(14).min()
        high_max = df['high'].rolling(14).max()
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d = k.rolling(3).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean()
        
        # OBV
        obv = (np.sign(df['close'].diff()) * df['volume']).cumsum()
        
        # Normalização
        for ind in [close, volume, rsi, macd, bollinger_upper,
                   bollinger_lower, k, d, atr, obv]:
            ind = (ind - np.mean(ind)) / np.std(ind)
            indicators.append(ind)
            
        return np.stack(indicators, axis=0)
        
    def prepare_batch(self, data: List[Dict]) -> torch.Tensor:
        """Prepara batch de dados técnicos."""
        batch = []
        for d in data:
            indicators = self.calculate_indicators(d)
            # Pega últimos sequence_length pontos
            indicators = indicators[:, -self.sequence_length:]
            batch.append(indicators)
        return torch.FloatTensor(np.stack(batch)).to(self.device)
        
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """Executa forward pass do modelo."""
        with torch.no_grad():
            # Feature extraction
            features = self.model.feature_extractor(batch)
            
            # LSTM
            lstm_out, _ = self.model.lstm(features.transpose(1, 2))
            
            # Self-attention
            attn_out, _ = self.model.attention(lstm_out, lstm_out, lstm_out)
            
            # Final prediction
            pred = self.model.predictor(attn_out[:, -1, :])
            return torch.softmax(pred, dim=1)
            
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa dados técnicos e gera previsões."""
        # Verifica cache
        key = f"{data['symbol']}_{data['timestamp']}"
        now = datetime.now().timestamp()
        if key in self.analysis_cache:
            cached_time, cached_result = self.analysis_cache[key]
            if now - cached_time < self.cache_duration:
                return cached_result
                
        # Prepara dados
        batch = self.prepare_batch([data])
        
        # Processa na GPU
        scores = self.process_batch(batch)
        prediction = scores[0]  # [down, neutral, up]
        
        # Calcula métricas
        direction = prediction[2].item() - prediction[0].item()  # up - down
        confidence = torch.max(prediction).item()
        
        # Gera análise
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'prediction': direction,
            'confidence': confidence,
            'signal_type': 'TECHNICAL',
            'parameters': {
                'score': direction,
                'direction': 'LONG' if direction > 0 else 'SHORT',
                'strength': abs(direction)
            },
            'metadata': {
                'symbol': data['symbol'],
                'scores': {
                    'down': prediction[0].item(),
                    'neutral': prediction[1].item(),
                    'up': prediction[2].item()
                }
            }
        }
        
        # Atualiza cache
        self.analysis_cache[key] = (now, analysis)
        self.last_analysis = analysis
        
        return analysis
        
    def update_state(self, market_data: Dict[str, Any]) -> None:
        """Atualiza estado com novos dados de mercado."""
        # Limpa cache antigo
        now = datetime.now().timestamp()
        self.analysis_cache = {
            k: v for k, v in self.analysis_cache.items()
            if now - v[0] < self.cache_duration
        }
        
    def handle_signal(self, message: Dict[str, Any]) -> None:
        """Processa sinais de outros agentes."""
        if message['type'] == 'MARKET_DIRECTION':
            # Ajusta confidence threshold com base em confirmação de outros agentes
            if message['confidence'] > 0.8:
                self.confidence_threshold *= 0.95
                
    def handle_feedback(self, message: Dict[str, Any]) -> None:
        """Processa feedback sobre previsões anteriores."""
        if message['type'] == 'PREDICTION_FEEDBACK':
            # Ajusta threshold com base no feedback
            if message['success']:
                self.confidence_threshold *= 0.98
            else:
                self.confidence_threshold *= 1.02
                
            # Mantém threshold em limites razoáveis
            self.confidence_threshold = max(0.6, min(0.9, self.confidence_threshold))
            
    def cleanup(self) -> None:
        """Limpa recursos da GPU."""
        self.optimize_memory()
        self.analysis_cache.clear()