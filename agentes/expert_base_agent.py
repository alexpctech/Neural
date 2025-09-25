"""
Classe base para agentes especialistas que implementam regras de decisão baseadas em conhecimento.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import torch
import numpy as np
import pandas as pd
from datetime import datetime
import logging
from .abstract_agent import AbstractAgent

class ExpertBaseAgent(AbstractAgent):
    def __init__(self, name: str, gpu_device: Optional[torch.device] = None):
        super().__init__(name, gpu_device)
        self.decision_rules = {}
        self.knowledge_base = {}
        self.confidence_weights = {}
        self.min_confidence = 0.80  # Confiança mínima para decisões
        
    def add_rule(self, rule_name: str, rule_function: callable, weight: float = 1.0):
        """Adiciona uma regra de decisão ao agente."""
        self.decision_rules[rule_name] = rule_function
        self.confidence_weights[rule_name] = weight
        
    def add_knowledge(self, key: str, value: Any):
        """Adiciona conhecimento específico ao agente."""
        self.knowledge_base[key] = value
        
    def evaluate_rules(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Avalia todas as regras de decisão e retorna os resultados com confiança."""
        results = {}
        for rule_name, rule_func in self.decision_rules.items():
            try:
                rule_result = rule_func(data, self.knowledge_base)
                confidence = rule_result.get('confidence', 0) * self.confidence_weights[rule_name]
                results[rule_name] = {
                    'decision': rule_result.get('decision'),
                    'confidence': confidence,
                    'metadata': rule_result.get('metadata', {})
                }
            except Exception as e:
                logging.error(f"Erro ao avaliar regra {rule_name}: {str(e)}")
                
        return results
        
    def aggregate_decisions(self, rule_results: Dict[str, Dict]) -> Dict[str, Any]:
        """Agrega resultados das regras usando média ponderada das confianças."""
        if not rule_results:
            return {
                'decision': 'NEUTRO',
                'confidence': 0,
                'metadata': {'reason': 'Sem regras avaliadas'}
            }
            
        # Agrupa decisões por tipo
        decision_groups = {}
        for rule_name, result in rule_results.items():
            decision = result['decision']
            if decision not in decision_groups:
                decision_groups[decision] = []
            decision_groups[decision].append({
                'confidence': result['confidence'],
                'rule': rule_name,
                'metadata': result['metadata']
            })
            
        # Calcula confiança média ponderada para cada decisão
        weighted_decisions = {}
        for decision, results in decision_groups.items():
            total_confidence = sum(r['confidence'] for r in results)
            weighted_decisions[decision] = {
                'confidence': total_confidence / len(results),
                'count': len(results),
                'rules': [r['rule'] for r in results],
                'metadata': [r['metadata'] for r in results]
            }
            
        # Encontra decisão com maior confiança
        best_decision = max(
            weighted_decisions.items(),
            key=lambda x: x[1]['confidence']
        )
        
        # Retorna apenas se atingir confiança mínima
        if best_decision[1]['confidence'] >= self.min_confidence:
            return {
                'decision': best_decision[0],
                'confidence': best_decision[1]['confidence'],
                'metadata': {
                    'rules_triggered': best_decision[1]['rules'],
                    'rule_count': best_decision[1]['count'],
                    'rule_details': best_decision[1]['metadata']
                }
            }
        else:
            return {
                'decision': 'NEUTRO',
                'confidence': best_decision[1]['confidence'],
                'metadata': {
                    'reason': 'Confiança insuficiente',
                    'best_decision': best_decision[0],
                    'rules_triggered': best_decision[1]['rules']
                }
            }
            
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa dados usando regras de decisão do especialista."""
        try:
            # Avalia todas as regras
            rule_results = self.evaluate_rules(data)
            
            # Agrega resultados
            decision = self.aggregate_decisions(rule_results)
            
            analysis = {
                'signal_type': 'EXPERT_DECISION',
                'confidence': decision['confidence'],
                'parameters': {
                    'decision': decision['decision'],
                    'rules_evaluated': len(rule_results)
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'decision_details': decision['metadata'],
                    'rule_results': rule_results
                }
            }
            
            self.last_analysis = analysis
            return analysis
            
        except Exception as e:
            logging.error(f"Erro na análise especialista: {str(e)}")
            return {
                'signal_type': 'ERROR',
                'confidence': 0,
                'parameters': {},
                'metadata': {'error': str(e)}
            }
            
    @abstractmethod
    def _model_forward(self, batch: torch.Tensor) -> torch.Tensor:
        """Implementação específica do forward pass do modelo."""
        pass
        
    def prepare_batch(self, data: List[Dict]) -> torch.Tensor:
        """Prepara batch de dados para processamento."""
        # Implementação específica para cada tipo de agente
        pass
        
    def explain_decision(self, analysis: Dict[str, Any]) -> str:
        """Gera explicação detalhada da decisão em linguagem natural."""
        try:
            if analysis['signal_type'] != 'EXPERT_DECISION':
                return "Análise não é uma decisão especialista"
                
            decision = analysis['parameters']['decision']
            confidence = analysis['confidence']
            metadata = analysis['metadata']
            
            explanation = [
                f"Decisão: {decision}",
                f"Confiança: {confidence:.2%}",
                "\nRegras ativadas:"
            ]
            
            for rule in metadata['decision_details'].get('rules_triggered', []):
                rule_result = metadata['rule_results'][rule]
                explanation.append(
                    f"- {rule}: {rule_result['decision']} "
                    f"(confiança: {rule_result['confidence']:.2%})"
                )
                
            if metadata['decision_details'].get('reason'):
                explanation.append(f"\nMotivo: {metadata['decision_details']['reason']}")
                
            return "\n".join(explanation)
            
        except Exception as e:
            logging.error(f"Erro ao gerar explicação: {str(e)}")
            return "Erro ao gerar explicação da decisão"