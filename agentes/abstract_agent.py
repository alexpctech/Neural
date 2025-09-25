"""
Classe base para todos os agentes do sistema de trading.
Implementa a interface comum e funcionalidades básicas compartilhadas.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import torch
import numpy as np
from datetime import datetime
import logging
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbstractAgent(ABC):
    def __init__(self, name: str, gpu_device: Optional[torch.device] = None):
        self.name = name
        self.device = gpu_device if gpu_device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.confidence_threshold = 0.75  # Confiança mínima para gerar sinais
        self.last_analysis = None
        self.batch_size = 32  # Tamanho do batch para GPU
        
        # Inicializa embeddings para busca semântica
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa dados e retorna previsões/sinais."""
        pass
        
    @abstractmethod
    def prepare_batch(self, data: List[Dict]) -> torch.Tensor:
        """Prepara um batch de dados para processamento na GPU."""
        pass
        
    def process_batch(self, batch: torch.Tensor) -> torch.Tensor:
        """Processa um batch de dados na GPU com otimização de memória."""
        try:
            with torch.cuda.amp.autocast():  # Usa precisão mista para otimização
                batch = batch.to(self.device)
                # Limpa cache da GPU periodicamente
                if torch.cuda.memory_allocated(self.device) > 0.8 * torch.cuda.get_device_properties(self.device).total_memory:
                    torch.cuda.empty_cache()
                return self._model_forward(batch)
        except RuntimeError as e:
            logger.error(f"Erro de GPU: {str(e)}")
            # Reduz batch size se houver erro de memória
            if "out of memory" in str(e):
                self.batch_size = self.batch_size // 2
                logger.info(f"Reduzindo batch size para {self.batch_size}")
                return self.process_batch(batch[:self.batch_size])
            raise e
            
    @abstractmethod
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """Implementação específica do forward pass do modelo."""
        pass

    def index_documents(self, documents: List[Dict[str, str]]) -> None:
        """Indexa documentos para busca semântica usando FAISS."""
        try:
            texts = [doc['text'] for doc in documents]
            self.vector_store = FAISS.from_texts(texts, self.embeddings)
            logger.info(f"Indexados {len(texts)} documentos no FAISS")
        except Exception as e:
            logger.error(f"Erro ao indexar documentos: {str(e)}")

    def semantic_search(self, query: str, k: int = 3) -> List[Dict]:
        """Realiza busca semântica nos documentos indexados."""
        try:
            if self.vector_store:
                docs = self.vector_store.similarity_search(query, k=k)
                logger.info(f"Recuperados {len(docs)} documentos para a query")
                return [{'content': doc.page_content, 'score': doc.metadata.get('score', 0)} 
                       for doc in docs]
            return []
        except Exception as e:
            logger.error(f"Erro na busca semântica: {str(e)}")
            return []
            
    def generate_signal(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Gera um sinal de trading se a confiança for alta o suficiente."""
        try:
            if analysis['confidence'] >= self.confidence_threshold:
                signal = {
                    'agent': self.name,
                    'timestamp': datetime.now().isoformat(),
                    'type': analysis['signal_type'],
                    'confidence': analysis['confidence'],
                    'parameters': analysis['parameters'],
                    'metadata': analysis['metadata']
                }
                logger.info(f"Sinal gerado pelo agente {self.name} com confiança {analysis['confidence']}")
                return signal
            logger.debug(f"Confiança insuficiente ({analysis['confidence']}) para gerar sinal")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar sinal: {str(e)}")
            return None
        return None
        
    def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Valida um sinal antes de enviá-lo."""
        required_fields = ['type', 'confidence', 'parameters']
        return all(field in signal for field in required_fields)
        
    @abstractmethod
    def update_state(self, market_data: Dict[str, Any]) -> None:
        """Atualiza o estado interno do agente com novos dados."""
        pass
        
    def communicate(self, message: Dict[str, Any]) -> None:
        """Processa mensagens de outros agentes."""
        if 'type' in message and hasattr(self, f'handle_{message["type"]}'):
            handler = getattr(self, f'handle_{message["type"]}')
            handler(message)
            
    @abstractmethod
    def handle_signal(self, message: Dict[str, Any]) -> None:
        """Processa sinais de outros agentes."""
        pass
        
    @abstractmethod
    def handle_feedback(self, message: Dict[str, Any]) -> None:
        """Processa feedback sobre sinais anteriores."""
        pass
        
    def to_gpu(self, tensor: torch.Tensor) -> torch.Tensor:
        """Move um tensor para a GPU se disponível."""
        return tensor.to(self.device)
        
    def optimize_memory(self) -> None:
        """Otimiza uso de memória da GPU."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    def __str__(self) -> str:
        return f"{self.name} Agent (GPU: {self.device})"