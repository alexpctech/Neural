"""
Agente responsável por indexar e recuperar documentos e dados relevantes.
Usa embeddings, FAISS e reranking para busca semântica eficiente.
"""
from typing import Dict, List, Optional, Any, Tuple
import torch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from transformers import AutoModel, AutoTokenizer
from .abstract_agent import AbstractAgent
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

class RetrieverAgent(AbstractAgent):
    def __init__(self, name: str = "RetrieverAgent", gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        self._setup_retrieval_system()
        self.relevance_threshold = 0.7
        self.max_context_size = 10  # Máximo de documentos no contexto
        self.memory_window = 30  # Dias para manter documentos
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50
        )

    def _setup_retrieval_system(self):
        """Configura sistema de recuperação de informações."""
        # Embeddings para busca semântica
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': str(self.device)}
        )
        
        # Vector store por tipo de documento
        self.vector_stores = {
            'news': None,
            'reports': None,
            'research': None,
            'social': None
        }
        
        # Modelo de reranking
        self.rerank_tokenizer = AutoTokenizer.from_pretrained(
            "cross-encoder/ms-marco-MiniLM-L-12-v2"
        )
        self.rerank_model = AutoModel.from_pretrained(
            "cross-encoder/ms-marco-MiniLM-L-12-v2"
        ).to(self.device)
        
        # Cache de busca
        self.search_cache = {}
        self.cache_duration = 300  # 5 minutos

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza busca e recuperação de informações."""
        try:
            query = data.get('query', '')
            doc_types = data.get('doc_types', list(self.vector_stores.keys()))
            
            # Verifica cache
            cache_key = f"{query}_{','.join(doc_types)}"
            now = datetime.now().timestamp()
            if cache_key in self.search_cache:
                cached_time, cached_result = self.search_cache[cache_key]
                if now - cached_time < self.cache_duration:
                    return cached_result
                    
            # Busca em cada tipo de documento
            all_results = []
            for doc_type in doc_types:
                if self.vector_stores[doc_type]:
                    results = self._search_documents(
                        query,
                        doc_type,
                        k=self.max_context_size
                    )
                    all_results.extend(results)
                    
            # Reranking dos resultados
            if all_results:
                reranked_results = self._rerank_results(query, all_results)
                relevant_results = self._filter_relevant_results(reranked_results)
            else:
                relevant_results = []
                
            # Análise dos resultados
            analysis = self._analyze_search_results(query, relevant_results)
            
            # Atualiza cache
            self.search_cache[cache_key] = (now, analysis)
            self.last_analysis = analysis
            
            return analysis
            
        except Exception as e:
            logging.error(f"Erro na análise: {str(e)}")
            return {
                'signal_type': 'ERROR',
                'confidence': 0,
                'parameters': {},
                'metadata': {'error': str(e)}
            }

    def prepare_batch(self, query: str) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """Prepara query para busca."""
        # Tokeniza query
        query_tokens = self.rerank_tokenizer(
            query,
            padding=True,
            truncation=True,
            return_tensors='pt'
        )
        
        # Metadata
        metadata = {
            'query_length': len(query.split()),
            'timestamp': datetime.now().isoformat()
        }
        
        return query_tokens, metadata
        
    def _model_forward(self, batch: Tuple[torch.Tensor, Dict[str, Any]]) -> torch.Tensor:
        """Forward pass do modelo de reranking."""
        query_tokens, _ = batch
        
        with torch.no_grad():
            query_tokens = {k: v.to(self.device) for k, v in query_tokens.items()}
            outputs = self.rerank_model(**query_tokens)
            return outputs.last_hidden_state.mean(dim=1)

    def _search_documents(self,
                         query: str,
                         doc_type: str,
                         k: int = 10) -> List[Dict[str, Any]]:
        """Realiza busca em documentos de um tipo específico."""
        if not self.vector_stores[doc_type]:
            return []
            
        results = self.vector_stores[doc_type].similarity_search_with_score(
            query,
            k=k
        )
        
        return [{
            'content': doc.page_content,
            'metadata': {**doc.metadata, 'score': score},
            'doc_type': doc_type
        } for doc, score in results]
        
    def _rerank_results(self,
                       query: str,
                       results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reordena resultados usando modelo de reranking."""
        if not results:
            return []
            
        # Prepara batch para reranking
        query_tokens, _ = self.prepare_batch(query)
        query_embedding = self.process_batch((query_tokens, {}))
        
        # Calcula scores para cada documento
        rerank_scores = []
        for result in results:
            doc_tokens = self.rerank_tokenizer(
                result['content'],
                padding=True,
                truncation=True,
                return_tensors='pt'
            )
            doc_tokens = {k: v.to(self.device) for k, v in doc_tokens.items()}
            
            with torch.no_grad():
                doc_embedding = self.rerank_model(**doc_tokens).last_hidden_state.mean(dim=1)
                score = torch.cosine_similarity(query_embedding, doc_embedding)
                rerank_scores.append(score.item())
                
        # Reordena resultados
        reranked = sorted(
            zip(results, rerank_scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [{
            **result,
            'metadata': {
                **result['metadata'],
                'rerank_score': score
            }
        } for result, score in reranked]

    def _filter_relevant_results(self,
                               results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra resultados por relevância."""
        return [
            result for result in results
            if result['metadata']['rerank_score'] >= self.relevance_threshold
        ]
        
    def _analyze_search_results(self,
                              query: str,
                              results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analisa resultados da busca."""
        if not results:
            return {
                'signal_type': 'NO_RESULTS',
                'confidence': 0,
                'parameters': {},
                'metadata': {'query': query}
            }
            
        # Agrupa por tipo de documento
        by_type = {}
        for result in results:
            doc_type = result['doc_type']
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(result)
            
        # Análise por tipo
        type_analysis = {}
        for doc_type, docs in by_type.items():
            avg_score = np.mean([doc['metadata']['rerank_score'] for doc in docs])
            type_analysis[doc_type] = {
                'count': len(docs),
                'avg_score': avg_score,
                'top_score': max(doc['metadata']['rerank_score'] for doc in docs)
            }
            
        # Calcula métricas gerais
        avg_score = np.mean([doc['metadata']['rerank_score'] for doc in results])
        top_docs = sorted(
            results,
            key=lambda x: x['metadata']['rerank_score'],
            reverse=True
        )[:3]
        
        return {
            'signal_type': 'SEARCH_RESULTS',
            'confidence': avg_score,
            'parameters': {
                'total_results': len(results),
                'type_distribution': {
                    t: analysis['count'] for t, analysis in type_analysis.items()
                },
                'top_sources': [
                    {
                        'doc_type': doc['doc_type'],
                        'score': doc['metadata']['rerank_score']
                    }
                    for doc in top_docs
                ]
            },
            'metadata': {
                'query': query,
                'type_analysis': type_analysis,
                'timestamp': datetime.now().isoformat()
            }
        }
        
    def index_documents(self,
                       documents: List[Dict[str, Any]],
                       doc_type: str) -> None:
        """Indexa novos documentos."""
        try:
            if doc_type not in self.vector_stores:
                raise ValueError(f"Tipo de documento inválido: {doc_type}")
                
            # Processa documentos
            processed_docs = []
            for doc in documents:
                # Split em chunks
                chunks = self.text_splitter.split_text(doc['content'])
                
                # Adiciona metadata
                processed_docs.extend([{
                    'text': chunk,
                    'metadata': {
                        **doc.get('metadata', {}),
                        'chunk_id': i,
                        'total_chunks': len(chunks)
                    }
                } for i, chunk in enumerate(chunks)])
                
            # Cria ou atualiza vector store
            if self.vector_stores[doc_type] is None:
                self.vector_stores[doc_type] = FAISS.from_texts(
                    [doc['text'] for doc in processed_docs],
                    self.embeddings,
                    [doc['metadata'] for doc in processed_docs]
                )
            else:
                self.vector_stores[doc_type].add_texts(
                    [doc['text'] for doc in processed_docs],
                    [doc['metadata'] for doc in processed_docs]
                )
                
            logging.info(
                f"Indexados {len(documents)} documentos do tipo {doc_type}"
            )
            
        except Exception as e:
            logging.error(f"Erro ao indexar documentos: {str(e)}")
            
    def cleanup_old_documents(self) -> None:
        """Remove documentos antigos do índice."""
        cutoff = datetime.now() - timedelta(days=self.memory_window)
        
        for doc_type, store in self.vector_stores.items():
            if store is not None:
                # Filtra documentos por data
                current_docs = store.get()
                filtered_docs = [
                    doc for doc in current_docs
                    if doc.metadata.get('date') and
                    datetime.fromisoformat(doc.metadata['date']) > cutoff
                ]
                
                # Recria store se necessário
                if len(filtered_docs) < len(current_docs):
                    self.vector_stores[doc_type] = FAISS.from_texts(
                        [doc.page_content for doc in filtered_docs],
                        self.embeddings,
                        [doc.metadata for doc in filtered_docs]
                    )
                    
    def update_state(self, market_data: Dict[str, Any]) -> None:
        """Atualiza estado com novos dados de mercado."""
        # Indexa novos documentos se disponíveis
        for doc_type in self.vector_stores:
            if doc_type in market_data:
                self.index_documents(market_data[doc_type], doc_type)
                
        # Limpa documentos antigos periodicamente
        self.cleanup_old_documents()
        
        # Limpa cache antigo
        now = datetime.now().timestamp()
        self.search_cache = {
            k: v for k, v in self.search_cache.items()
            if now - v[0] < self.cache_duration
        }
        
    def handle_signal(self, message: Dict[str, Any]) -> None:
        """Processa sinais do sistema."""
        if message['type'] == 'NEW_DOCUMENTS':
            doc_type = message['doc_type']
            documents = message['documents']
            self.index_documents(documents, doc_type)
            
    def handle_feedback(self, message: Dict[str, Any]) -> None:
        """Processa feedback sobre buscas anteriores."""
        if message['type'] == 'SEARCH_FEEDBACK':
            # Ajusta threshold baseado no feedback
            relevance = message.get('relevance', 0)
            self.relevance_threshold = max(0.5, min(0.9,
                self.relevance_threshold * (1.0 + 0.1 * (relevance - 0.5))
            ))