"""
Detector de Padrões de Análise Técnica
Identifica padrões gráficos clássicos
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class TipoPadrao(Enum):
    """Tipos de padrões detectáveis"""
    TRIANGULO_ASCENDENTE = "triangulo_ascendente"
    TRIANGULO_DESCENDENTE = "triangulo_descendente"
    TRIANGULO_SIMETRICO = "triangulo_simetrico"
    CABECA_OMBROS = "cabeca_ombros"
    CABECA_OMBROS_INVERTIDO = "cabeca_ombros_invertido"
    DUPLO_TOPO = "duplo_topo"
    DUPLO_FUNDO = "duplo_fundo"
    BANDEIRA = "bandeira"
    CUNHA_ASCENDENTE = "cunha_ascendente"
    CUNHA_DESCENDENTE = "cunha_descendente"
    CANAL_ALTA = "canal_alta"
    CANAL_BAIXA = "canal_baixa"

@dataclass
class PadraoDetectado:
    """Estrutura para um padrão detectado"""
    tipo: TipoPadrao
    inicio: int
    fim: int
    confianca: float  # 0-100
    pontos_chave: List[Tuple[int, float]]
    sinal: str  # 'COMPRA', 'VENDA', 'NEUTRO'
    preco_entrada: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class DetectorPadroes:
    """
    Classe para detecção de padrões técnicos
    """
    
    def __init__(self, min_confianca: float = 60.0):
        self.logger = logging.getLogger(__name__)
        self.min_confianca = min_confianca
        
    def detectar_topos_fundos(self, precos: List[float], janela: int = 5) -> Tuple[List[int], List[int]]:
        """
        Detecta topos e fundos locais
        
        Args:
            precos: Lista de preços
            janela: Janela para detecção de máximos/mínimos locais
            
        Returns:
            Tuple com índices dos topos e fundos
        """
        precos_array = np.array(precos)
        topos = []
        fundos = []
        
        for i in range(janela, len(precos) - janela):
            # Verificar se é um topo
            if all(precos_array[i] >= precos_array[i-j] for j in range(1, janela+1)) and \
               all(precos_array[i] >= precos_array[i+j] for j in range(1, janela+1)):
                topos.append(i)
            
            # Verificar se é um fundo
            elif all(precos_array[i] <= precos_array[i-j] for j in range(1, janela+1)) and \
                 all(precos_array[i] <= precos_array[i+j] for j in range(1, janela+1)):
                fundos.append(i)
        
        return topos, fundos
    
    def detectar_triangulo_ascendente(self, precos: List[float], topos: List[int], fundos: List[int]) -> Optional[PadraoDetectado]:
        """
        Detecta padrão de triângulo ascendente
        """
        if len(topos) < 2 or len(fundos) < 2:
            return None
        
        # Pegar os últimos topos e fundos
        ultimos_topos = sorted(topos[-3:])
        ultimos_fundos = sorted(fundos[-3:])
        
        if len(ultimos_topos) < 2 or len(ultimos_fundos) < 2:
            return None
        
        # Verificar se os topos estão no mesmo nível (resistência horizontal)
        niveis_topos = [precos[i] for i in ultimos_topos]
        variacao_topos = (max(niveis_topos) - min(niveis_topos)) / np.mean(niveis_topos)
        
        # Verificar se os fundos estão ascendentes (suporte ascendente)
        niveis_fundos = [precos[i] for i in ultimos_fundos]
        fundos_ascendentes = all(niveis_fundos[i] < niveis_fundos[i+1] for i in range(len(niveis_fundos)-1))
        
        if variacao_topos < 0.02 and fundos_ascendentes:  # Topos estáveis e fundos ascendentes
            confianca = 70.0 + (30.0 * (1 - variacao_topos))  # Mais confiança se topos mais estáveis
            
            pontos_chave = [(i, precos[i]) for i in ultimos_topos + ultimos_fundos]
            
            return PadraoDetectado(
                tipo=TipoPadrao.TRIANGULO_ASCENDENTE,
                inicio=min(ultimos_topos + ultimos_fundos),
                fim=max(ultimos_topos + ultimos_fundos),
                confianca=min(confianca, 95.0),
                pontos_chave=pontos_chave,
                sinal='COMPRA',  # Triângulo ascendente é bullish
                preco_entrada=max(niveis_topos) * 1.01,  # Breakout acima da resistência
                stop_loss=min(niveis_fundos[-2:]) * 0.98,
                take_profit=max(niveis_topos) * 1.10
            )
        
        return None
    
    def detectar_duplo_topo(self, precos: List[float], topos: List[int]) -> Optional[PadraoDetectado]:
        """
        Detecta padrão de duplo topo
        """
        if len(topos) < 2:
            return None
        
        # Pegar os dois últimos topos
        topo1_idx, topo2_idx = topos[-2], topos[-1]
        topo1_preco, topo2_preco = precos[topo1_idx], precos[topo2_idx]
        
        # Verificar se os topos estão em níveis similares
        diferenca = abs(topo1_preco - topo2_preco) / max(topo1_preco, topo2_preco)
        
        if diferenca < 0.03:  # Menos de 3% de diferença
            # Encontrar o vale entre os topos
            vale_idx = topo1_idx + np.argmin(precos[topo1_idx:topo2_idx+1])
            vale_preco = precos[vale_idx]
            
            # Verificar se há uma correção significativa entre os topos
            correcao = (min(topo1_preco, topo2_preco) - vale_preco) / min(topo1_preco, topo2_preco)
            
            if correcao > 0.05:  # Correção de pelo menos 5%
                confianca = 60.0 + (30.0 * (1 - diferenca)) + (10.0 * correcao)
                
                pontos_chave = [
                    (topo1_idx, topo1_preco),
                    (vale_idx, vale_preco),
                    (topo2_idx, topo2_preco)
                ]
                
                return PadraoDetectado(
                    tipo=TipoPadrao.DUPLO_TOPO,
                    inicio=topo1_idx,
                    fim=topo2_idx,
                    confianca=min(confianca, 95.0),
                    pontos_chave=pontos_chave,
                    sinal='VENDA',  # Duplo topo é bearish
                    preco_entrada=vale_preco * 0.99,  # Breakout abaixo do suporte
                    stop_loss=max(topo1_preco, topo2_preco) * 1.02,
                    take_profit=vale_preco - (max(topo1_preco, topo2_preco) - vale_preco)
                )
        
        return None
    
    def detectar_cabeca_ombros(self, precos: List[float], topos: List[int]) -> Optional[PadraoDetectado]:
        """
        Detecta padrão cabeça e ombros
        """
        if len(topos) < 3:
            return None
        
        # Pegar os três últimos topos
        ombro1_idx, cabeca_idx, ombro2_idx = topos[-3], topos[-2], topos[-1]
        ombro1_preco = precos[ombro1_idx]
        cabeca_preco = precos[cabeca_idx]
        ombro2_preco = precos[ombro2_idx]
        
        # Verificar se a cabeça é mais alta que os ombros
        if cabeca_preco > ombro1_preco and cabeca_preco > ombro2_preco:
            # Verificar se os ombros estão em níveis similares
            diferenca_ombros = abs(ombro1_preco - ombro2_preco) / max(ombro1_preco, ombro2_preco)
            
            if diferenca_ombros < 0.05:  # Ombros similares
                # Encontrar os vales (linha do pescoço)
                vale1_idx = ombro1_idx + np.argmin(precos[ombro1_idx:cabeca_idx+1])
                vale2_idx = cabeca_idx + np.argmin(precos[cabeca_idx:ombro2_idx+1])
                vale1_preco = precos[vale1_idx]
                vale2_preco = precos[vale2_idx]
                
                # Calcular linha do pescoço
                linha_pescoco = (vale1_preco + vale2_preco) / 2
                
                confianca = 65.0 + (25.0 * (1 - diferenca_ombros))
                
                pontos_chave = [
                    (ombro1_idx, ombro1_preco),
                    (vale1_idx, vale1_preco),
                    (cabeca_idx, cabeca_preco),
                    (vale2_idx, vale2_preco),
                    (ombro2_idx, ombro2_preco)
                ]
                
                return PadraoDetectado(
                    tipo=TipoPadrao.CABECA_OMBROS,
                    inicio=ombro1_idx,
                    fim=ombro2_idx,
                    confianca=min(confianca, 95.0),
                    pontos_chave=pontos_chave,
                    sinal='VENDA',  # Cabeça e ombros é bearish
                    preco_entrada=linha_pescoco * 0.99,
                    stop_loss=cabeca_preco * 1.02,
                    take_profit=linha_pescoco - (cabeca_preco - linha_pescoco)
                )
        
        return None
    
    def detectar_canal(self, precos: List[float], topos: List[int], fundos: List[int]) -> Optional[PadraoDetectado]:
        """
        Detecta canais de alta ou baixa
        """
        if len(topos) < 2 or len(fundos) < 2:
            return None
        
        # Analisar tendência dos topos e fundos
        ultimos_topos = sorted(topos[-3:])
        ultimos_fundos = sorted(fundos[-3:])
        
        if len(ultimos_topos) < 2 or len(ultimos_fundos) < 2:
            return None
        
        topos_precos = [precos[i] for i in ultimos_topos]
        fundos_precos = [precos[i] for i in ultimos_fundos]
        
        # Verificar tendência
        topos_crescentes = all(topos_precos[i] < topos_precos[i+1] for i in range(len(topos_precos)-1))
        fundos_crescentes = all(fundos_precos[i] < fundos_precos[i+1] for i in range(len(fundos_precos)-1))
        
        topos_decrescentes = all(topos_precos[i] > topos_precos[i+1] for i in range(len(topos_precos)-1))
        fundos_decrescentes = all(fundos_precos[i] > fundos_precos[i+1] for i in range(len(fundos_precos)-1))
        
        if topos_crescentes and fundos_crescentes:
            # Canal de alta
            pontos_chave = [(i, precos[i]) for i in ultimos_topos + ultimos_fundos]
            
            return PadraoDetectado(
                tipo=TipoPadrao.CANAL_ALTA,
                inicio=min(ultimos_topos + ultimos_fundos),
                fim=max(ultimos_topos + ultimos_fundos),
                confianca=75.0,
                pontos_chave=pontos_chave,
                sinal='COMPRA',
                preco_entrada=fundos_precos[-1] * 1.01,
                stop_loss=fundos_precos[-2] * 0.98,
                take_profit=topos_precos[-1] * 1.02
            )
        
        elif topos_decrescentes and fundos_decrescentes:
            # Canal de baixa
            pontos_chave = [(i, precos[i]) for i in ultimos_topos + ultimos_fundos]
            
            return PadraoDetectado(
                tipo=TipoPadrao.CANAL_BAIXA,
                inicio=min(ultimos_topos + ultimos_fundos),
                fim=max(ultimos_topos + ultimos_fundos),
                confianca=75.0,
                pontos_chave=pontos_chave,
                sinal='VENDA',
                preco_entrada=topos_precos[-1] * 0.99,
                stop_loss=topos_precos[-2] * 1.02,
                take_profit=fundos_precos[-1] * 0.98
            )
        
        return None
    
    def detectar_todos_padroes(self, precos: List[float]) -> List[PadraoDetectado]:
        """
        Detecta todos os padrões possíveis
        
        Args:
            precos: Lista de preços de fechamento
            
        Returns:
            Lista de padrões detectados
        """
        if len(precos) < 20:
            self.logger.warning("Poucos dados para detecção de padrões")
            return []
        
        padroes_detectados = []
        
        try:
            # Detectar topos e fundos
            topos, fundos = self.detectar_topos_fundos(precos)
            
            # Detectar diferentes padrões
            padroes_detectores = [
                self.detectar_triangulo_ascendente,
                self.detectar_duplo_topo,
                self.detectar_cabeca_ombros,
                self.detectar_canal
            ]
            
            for detector in padroes_detectores:
                try:
                    if detector == self.detectar_canal:
                        padrao = detector(precos, topos, fundos)
                    elif detector == self.detectar_triangulo_ascendente:
                        padrao = detector(precos, topos, fundos)
                    else:
                        padrao = detector(precos, topos)
                    
                    if padrao and padrao.confianca >= self.min_confianca:
                        padroes_detectados.append(padrao)
                        
                except Exception as e:
                    self.logger.error(f"Erro ao detectar padrão {detector.__name__}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de padrões: {e}")
        
        # Ordenar por confiança
        padroes_detectados.sort(key=lambda x: x.confianca, reverse=True)
        
        return padroes_detectados
    
    def gerar_relatorio_padroes(self, padroes: List[PadraoDetectado]) -> str:
        """
        Gera relatório dos padrões detectados
        """
        if not padroes:
            return "Nenhum padrão detectado com confiança suficiente."
        
        relatorio = "=== RELATÓRIO DE PADRÕES DETECTADOS ===\n\n"
        
        for i, padrao in enumerate(padroes, 1):
            relatorio += f"{i}. {padrao.tipo.value.upper()}\n"
            relatorio += f"   Confiança: {padrao.confianca:.1f}%\n"
            relatorio += f"   Sinal: {padrao.sinal}\n"
            relatorio += f"   Período: {padrao.inicio} - {padrao.fim}\n"
            
            if padrao.preco_entrada:
                relatorio += f"   Entrada sugerida: R$ {padrao.preco_entrada:.2f}\n"
            if padrao.stop_loss:
                relatorio += f"   Stop Loss: R$ {padrao.stop_loss:.2f}\n"
            if padrao.take_profit:
                relatorio += f"   Take Profit: R$ {padrao.take_profit:.2f}\n"
            
            relatorio += "\n"
        
        return relatorio


# Exemplo de uso
if __name__ == "__main__":
    # Dados de exemplo simulando um duplo topo
    precos_exemplo = [
        100, 102, 104, 106, 108, 110, 108, 106, 104, 102,  # Subida
        104, 106, 108, 110, 109, 107, 105, 103, 101, 99,   # Duplo topo
        101, 103, 105, 107, 109, 111, 109, 107, 105, 103,  # Recuperação
        105, 107, 109, 110, 108, 106, 104, 102, 100, 98    # Queda
    ]
    
    # Inicializar detector
    detector = DetectorPadroes(min_confianca=50.0)
    
    # Detectar padrões
    padroes = detector.detectar_todos_padroes(precos_exemplo)
    
    # Gerar relatório
    relatorio = detector.gerar_relatorio_padroes(padroes)
    print(relatorio)