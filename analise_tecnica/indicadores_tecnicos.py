"""
Sistema de Análise Técnica - Fase 4
Implementação de indicadores técnicos principais
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

@dataclass
class IndicadorResult:
    """Resultado de um indicador técnico"""
    nome: str
    valores: List[float]
    sinais: List[str]  # 'COMPRA', 'VENDA', 'NEUTRO'
    timestamp: List[str]
    parametros: Dict

class AnalisisTecnica:
    """
    Classe principal para análise técnica
    Implementa indicadores técnicos fundamentais
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.indicadores_disponiveis = [
            'RSI', 'MACD', 'BollingerBands', 'MediaMovel', 
            'Stochastic', 'Williams%R', 'CCI'
        ]
    
    def calcular_rsi(self, precos: List[float], periodo: int = 14) -> IndicadorResult:
        """
        Calcula o Relative Strength Index (RSI)
        
        Args:
            precos: Lista de preços de fechamento
            periodo: Período para cálculo (padrão: 14)
            
        Returns:
            IndicadorResult com valores e sinais do RSI
        """
        if len(precos) < periodo + 1:
            raise ValueError(f"Necessários pelo menos {periodo + 1} preços para calcular RSI")
        
        # Converter para numpy array
        precos_array = np.array(precos)
        
        # Calcular diferenças
        deltas = np.diff(precos_array)
        
        # Separar ganhos e perdas
        ganhos = np.where(deltas > 0, deltas, 0)
        perdas = np.where(deltas < 0, -deltas, 0)
        
        # Calcular médias móveis dos ganhos e perdas
        avg_ganhos = pd.Series(ganhos).rolling(window=periodo).mean()
        avg_perdas = pd.Series(perdas).rolling(window=periodo).mean()
        
        # Calcular RSI
        rs = avg_ganhos / avg_perdas
        rsi = 100 - (100 / (1 + rs))
        
        # Remover valores NaN
        rsi_values = rsi.dropna().tolist()
        
        # Gerar sinais
        sinais = []
        for valor in rsi_values:
            if valor >= 70:
                sinais.append('VENDA')  # Sobrecomprado
            elif valor <= 30:
                sinais.append('COMPRA')  # Sobrevendido
            else:
                sinais.append('NEUTRO')
        
        return IndicadorResult(
            nome='RSI',
            valores=rsi_values,
            sinais=sinais,
            timestamp=[f"t{i}" for i in range(len(rsi_values))],
            parametros={'periodo': periodo, 'sobrecompra': 70, 'sobrevenda': 30}
        )
    
    def calcular_macd(self, precos: List[float], 
                     periodo_rapido: int = 12, 
                     periodo_lento: int = 26, 
                     periodo_sinal: int = 9) -> IndicadorResult:
        """
        Calcula o MACD (Moving Average Convergence Divergence)
        
        Args:
            precos: Lista de preços de fechamento
            periodo_rapido: Período da EMA rápida
            periodo_lento: Período da EMA lenta
            periodo_sinal: Período da linha de sinal
            
        Returns:
            IndicadorResult com valores e sinais do MACD
        """
        if len(precos) < periodo_lento:
            raise ValueError(f"Necessários pelo menos {periodo_lento} preços para calcular MACD")
        
        precos_series = pd.Series(precos)
        
        # Calcular EMAs
        ema_rapida = precos_series.ewm(span=periodo_rapido).mean()
        ema_lenta = precos_series.ewm(span=periodo_lento).mean()
        
        # Calcular MACD
        macd_line = ema_rapida - ema_lenta
        signal_line = macd_line.ewm(span=periodo_sinal).mean()
        histogram = macd_line - signal_line
        
        # Remover valores NaN
        macd_values = histogram.dropna().tolist()
        
        # Gerar sinais
        sinais = []
        for i, valor in enumerate(macd_values):
            if i > 0:
                if valor > 0 and macd_values[i-1] <= 0:
                    sinais.append('COMPRA')  # Cruzamento para cima
                elif valor < 0 and macd_values[i-1] >= 0:
                    sinais.append('VENDA')  # Cruzamento para baixo
                else:
                    sinais.append('NEUTRO')
            else:
                sinais.append('NEUTRO')
        
        return IndicadorResult(
            nome='MACD',
            valores=macd_values,
            sinais=sinais,
            timestamp=[f"t{i}" for i in range(len(macd_values))],
            parametros={
                'periodo_rapido': periodo_rapido,
                'periodo_lento': periodo_lento,
                'periodo_sinal': periodo_sinal
            }
        )
    
    def calcular_bollinger_bands(self, precos: List[float], 
                                periodo: int = 20, 
                                desvios: float = 2.0) -> Dict[str, IndicadorResult]:
        """
        Calcula as Bandas de Bollinger
        
        Args:
            precos: Lista de preços de fechamento
            periodo: Período para média móvel
            desvios: Número de desvios padrão
            
        Returns:
            Dict com IndicadorResult para banda superior, inferior e média
        """
        if len(precos) < periodo:
            raise ValueError(f"Necessários pelo menos {periodo} preços para calcular Bollinger Bands")
        
        precos_series = pd.Series(precos)
        
        # Calcular média móvel e desvio padrão
        sma = precos_series.rolling(window=periodo).mean()
        std = precos_series.rolling(window=periodo).std()
        
        # Calcular bandas
        banda_superior = sma + (std * desvios)
        banda_inferior = sma - (std * desvios)
        
        # Remover valores NaN
        sma_values = sma.dropna().tolist()
        upper_values = banda_superior.dropna().tolist()
        lower_values = banda_inferior.dropna().tolist()
        
        # Gerar sinais para a banda média
        sinais = []
        for i, (preco, upper, lower) in enumerate(zip(precos[-len(sma_values):], upper_values, lower_values)):
            if preco <= lower:
                sinais.append('COMPRA')  # Preço na banda inferior
            elif preco >= upper:
                sinais.append('VENDA')  # Preço na banda superior
            else:
                sinais.append('NEUTRO')
        
        parametros = {'periodo': periodo, 'desvios': desvios}
        timestamp = [f"t{i}" for i in range(len(sma_values))]
        
        return {
            'media': IndicadorResult('BB_Media', sma_values, sinais, timestamp, parametros),
            'superior': IndicadorResult('BB_Superior', upper_values, ['NEUTRO'] * len(upper_values), timestamp, parametros),
            'inferior': IndicadorResult('BB_Inferior', lower_values, ['NEUTRO'] * len(lower_values), timestamp, parametros)
        }
    
    def calcular_media_movel(self, precos: List[float], 
                           periodo: int = 20, 
                           tipo: str = 'SMA') -> IndicadorResult:
        """
        Calcula média móvel (SMA ou EMA)
        
        Args:
            precos: Lista de preços de fechamento
            periodo: Período da média
            tipo: 'SMA' (Simple) ou 'EMA' (Exponential)
            
        Returns:
            IndicadorResult com valores e sinais da média móvel
        """
        if len(precos) < periodo:
            raise ValueError(f"Necessários pelo menos {periodo} preços para calcular média móvel")
        
        precos_series = pd.Series(precos)
        
        if tipo == 'SMA':
            media = precos_series.rolling(window=periodo).mean()
        elif tipo == 'EMA':
            media = precos_series.ewm(span=periodo).mean()
        else:
            raise ValueError("Tipo deve ser 'SMA' ou 'EMA'")
        
        media_values = media.dropna().tolist()
        
        # Gerar sinais comparando preço atual com média
        sinais = []
        precos_correspondentes = precos[-len(media_values):]
        
        for preco, media_val in zip(precos_correspondentes, media_values):
            if preco > media_val:
                sinais.append('COMPRA')  # Preço acima da média
            elif preco < media_val:
                sinais.append('VENDA')  # Preço abaixo da média
            else:
                sinais.append('NEUTRO')
        
        return IndicadorResult(
            nome=f'{tipo}_{periodo}',
            valores=media_values,
            sinais=sinais,
            timestamp=[f"t{i}" for i in range(len(media_values))],
            parametros={'periodo': periodo, 'tipo': tipo}
        )
    
    def analisar_multiplos_indicadores(self, precos: List[float]) -> Dict[str, IndicadorResult]:
        """
        Executa análise com múltiplos indicadores
        
        Args:
            precos: Lista de preços de fechamento
            
        Returns:
            Dict com resultados de todos os indicadores
        """
        resultados = {}
        
        try:
            # RSI
            resultados['RSI'] = self.calcular_rsi(precos)
            
            # MACD
            if len(precos) >= 26:
                resultados['MACD'] = self.calcular_macd(precos)
            
            # Bollinger Bands
            if len(precos) >= 20:
                bb_results = self.calcular_bollinger_bands(precos)
                resultados.update(bb_results)
            
            # Médias Móveis
            if len(precos) >= 20:
                resultados['SMA_20'] = self.calcular_media_movel(precos, 20, 'SMA')
                resultados['EMA_20'] = self.calcular_media_movel(precos, 20, 'EMA')
            
            if len(precos) >= 50:
                resultados['SMA_50'] = self.calcular_media_movel(precos, 50, 'SMA')
                
        except Exception as e:
            self.logger.error(f"Erro na análise técnica: {e}")
            
        return resultados
    
    def gerar_consenso_sinais(self, indicadores: Dict[str, IndicadorResult]) -> List[str]:
        """
        Gera consenso de sinais baseado em múltiplos indicadores
        
        Args:
            indicadores: Dict com resultados dos indicadores
            
        Returns:
            Lista de sinais de consenso
        """
        if not indicadores:
            return []
        
        # Encontrar o menor comprimento entre todos os indicadores
        min_length = min(len(ind.sinais) for ind in indicadores.values())
        
        consenso = []
        
        for i in range(min_length):
            votos_compra = 0
            votos_venda = 0
            votos_neutro = 0
            
            for indicador in indicadores.values():
                if i < len(indicador.sinais):
                    sinal = indicador.sinais[i]
                    if sinal == 'COMPRA':
                        votos_compra += 1
                    elif sinal == 'VENDA':
                        votos_venda += 1
                    else:
                        votos_neutro += 1
            
            # Determinar consenso (maioria simples)
            if votos_compra > votos_venda and votos_compra > votos_neutro:
                consenso.append('COMPRA')
            elif votos_venda > votos_compra and votos_venda > votos_neutro:
                consenso.append('VENDA')
            else:
                consenso.append('NEUTRO')
        
        return consenso


# Exemplo de uso
if __name__ == "__main__":
    # Dados de exemplo (simulando preços)
    precos_exemplo = [
        100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
        111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
        119, 121, 123, 122, 124, 126, 125, 127, 129, 128,
        130, 132, 131, 133, 135, 134, 136, 138, 137, 139
    ]
    
    # Inicializar análise técnica
    analise = AnalisisTecnica()
    
    # Executar análise
    resultados = analise.analisar_multiplos_indicadores(precos_exemplo)
    
    print("=== ANÁLISE TÉCNICA COMPLETA ===")
    for nome, resultado in resultados.items():
        print(f"\n{nome}:")
        print(f"  Último valor: {resultado.valores[-1]:.2f}")
        print(f"  Último sinal: {resultado.sinais[-1]}")
        print(f"  Parâmetros: {resultado.parametros}")
    
    # Consenso
    consenso = analise.gerar_consenso_sinais(resultados)
    if consenso:
        print(f"\nCONSENSO: {consenso[-1]}")