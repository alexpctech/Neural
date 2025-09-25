"""
Estratégia de exemplo que implementa a interface base.
Esta estratégia combina indicadores técnicos simples para gerar sinais.
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd
from datetime import datetime

from estrategias.estrategia_base import (
    EstrategiaBase,
    ConfiguracaoEstrategia,
    SinalTrading,
    Direcao,
    TipoOrdem
)

class EstrategiaExemplo(EstrategiaBase):
    """
    Estratégia de exemplo que usa médias móveis e RSI.
    """
    
    def __init__(self):
        """Inicializa a estratégia com configuração padrão"""
        config = ConfiguracaoEstrategia(
            nome="Estratégia Exemplo",
            versao="1.0.0",
            timeframes=["1h", "4h", "1d"],
            parametros={
                "periodo_media_curta": 9,
                "periodo_media_longa": 21,
                "periodo_rsi": 14,
                "sobrevenda_rsi": 30,
                "sobrecompra_rsi": 70
            },
            stop_loss=2.0,  # 2%
            take_profit=4.0,  # 4%
            capital_por_operacao=1.0  # 1% do capital por operação
        )
        super().__init__(config)
    
    def analisar_mercado(
        self,
        dados: Dict[str, pd.DataFrame],
        ativo: str
    ) -> Optional[SinalTrading]:
        """
        Analisa o mercado usando médias móveis e RSI.
        
        Args:
            dados: Dicionário com DataFrames de dados por timeframe
            ativo: Símbolo do ativo sendo analisado
            
        Returns:
            Sinal de trading se houver oportunidade, None caso contrário
        """
        # Analisa cada timeframe
        sinais = []
        for timeframe in self.timeframes:
            if timeframe not in dados:
                continue
                
            df = dados[timeframe]
            
            # Calcula indicadores
            media_curta = df['close'].rolling(
                self.parametros['periodo_media_curta']
            ).mean()
            
            media_longa = df['close'].rolling(
                self.parametros['periodo_media_longa']
            ).mean()
            
            rsi = self._calcular_rsi(
                df['close'],
                self.parametros['periodo_rsi']
            )
            
            # Condições de compra
            compra = (
                media_curta.iloc[-1] > media_longa.iloc[-1] and  # Média curta acima da longa
                media_curta.iloc[-2] <= media_longa.iloc[-2] and  # Cruzamento recente
                rsi.iloc[-1] <= self.parametros['sobrevenda_rsi']  # RSI em sobrevenda
            )
            
            # Condições de venda
            venda = (
                media_curta.iloc[-1] < media_longa.iloc[-1] and  # Média curta abaixo da longa
                media_curta.iloc[-2] >= media_longa.iloc[-2] and  # Cruzamento recente
                rsi.iloc[-1] >= self.parametros['sobrecompra_rsi']  # RSI em sobrecompra
            )
            
            # Se houver sinal, cria objeto de sinal
            if compra or venda:
                direcao = Direcao.COMPRA if compra else Direcao.VENDA
                preco_atual = df['close'].iloc[-1]
                
                # Calcula stops
                stop_loss = (
                    preco_atual * (1 - self.config.stop_loss/100)
                    if compra else
                    preco_atual * (1 + self.config.stop_loss/100)
                )
                
                take_profit = (
                    preco_atual * (1 + self.config.take_profit/100)
                    if compra else
                    preco_atual * (1 - self.config.take_profit/100)
                )
                
                # Calcula confiança do sinal
                confianca = self.calcular_confianca(dados, ativo, direcao)
                
                sinal = SinalTrading(
                    ativo=ativo,
                    direcao=direcao,
                    tipo_ordem=TipoOrdem.MERCADO,
                    preco_entrada=preco_atual,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    timeframe=timeframe,
                    data_hora=datetime.now(),
                    confianca=confianca,
                    metadados={
                        "rsi": rsi.iloc[-1],
                        "media_curta": media_curta.iloc[-1],
                        "media_longa": media_longa.iloc[-1]
                    }
                )
                
                # Valida o sinal antes de adicionar
                if self.validar_sinal(sinal, dados):
                    sinais.append(sinal)
        
        # Retorna o sinal com maior confiança se houver sinais
        if sinais:
            return max(sinais, key=lambda x: x.confianca)
        return None
    
    def atualizar_parametros(self, resultados_backtest: Dict):
        """
        Atualiza parâmetros baseado em resultados de backtest.
        
        Args:
            resultados_backtest: Resultados do backtest
        """
        if not resultados_backtest:
            return
            
        # Exemplo de ajuste baseado em resultados
        # Aqui você pode implementar otimização de parâmetros
        
        retorno = resultados_backtest.get('retorno_total', 0)
        trades = resultados_backtest.get('total_trades', 0)
        
        if trades > 0:
            taxa_acerto = resultados_backtest.get('trades_lucro', 0) / trades
            
            # Ajusta períodos baseado na taxa de acerto
            if taxa_acerto < 0.4:  # Taxa de acerto muito baixa
                # Aumenta períodos para ser mais conservador
                self.parametros['periodo_media_curta'] += 1
                self.parametros['periodo_media_longa'] += 2
                
            elif taxa_acerto > 0.6:  # Taxa de acerto boa
                # Mantém períodos atuais
                pass
                
            # Ajusta níveis do RSI baseado no retorno
            if retorno < 0:
                # Torna níveis mais extremos para reduzir sinais
                self.parametros['sobrevenda_rsi'] = max(20, self.parametros['sobrevenda_rsi'] - 5)
                self.parametros['sobrecompra_rsi'] = min(80, self.parametros['sobrecompra_rsi'] + 5)
    
    def calcular_confianca(
        self,
        dados: Dict[str, pd.DataFrame],
        ativo: str,
        direcao: Direcao
    ) -> float:
        """
        Calcula nível de confiança para uma direção.
        
        Args:
            dados: Dicionário com DataFrames de dados por timeframe
            ativo: Símbolo do ativo
            direcao: Direção a ser avaliada
            
        Returns:
            Nível de confiança entre 0 e 1
        """
        if not dados:
            return 0.0
            
        # Inicializa pesos por timeframe
        pesos = {
            "1h": 0.2,
            "4h": 0.3,
            "1d": 0.5
        }
        
        confianca_total = 0
        peso_total = 0
        
        # Analisa cada timeframe
        for timeframe, df in dados.items():
            if timeframe not in pesos:
                continue
                
            peso = pesos[timeframe]
            
            # Calcula indicadores
            rsi = self._calcular_rsi(df['close'], self.parametros['periodo_rsi'])
            
            # Calcula tendência usando médias
            media_curta = df['close'].rolling(self.parametros['periodo_media_curta']).mean()
            media_longa = df['close'].rolling(self.parametros['periodo_media_longa']).mean()
            
            tendencia = (media_curta.iloc[-1] - media_longa.iloc[-1]) / media_longa.iloc[-1]
            
            # Calcula confiança para este timeframe
            if direcao == Direcao.COMPRA:
                confianca_rsi = max(0, (self.parametros['sobrevenda_rsi'] - rsi.iloc[-1]) / 30)
                confianca_tendencia = max(0, tendencia)
            else:
                confianca_rsi = max(0, (rsi.iloc[-1] - self.parametros['sobrecompra_rsi']) / 30)
                confianca_tendencia = max(0, -tendencia)
            
            # Combina confiança dos indicadores
            confianca_timeframe = 0.6 * confianca_rsi + 0.4 * confianca_tendencia
            
            # Adiciona ao total ponderado
            confianca_total += confianca_timeframe * peso
            peso_total += peso
        
        # Retorna confiança média ponderada
        return min(1.0, max(0.0, confianca_total / peso_total if peso_total > 0 else 0.0))
    
    def _calcular_rsi(self, precos: pd.Series, periodo: int) -> pd.Series:
        """
        Calcula o RSI (Relative Strength Index).
        
        Args:
            precos: Série de preços
            periodo: Período para cálculo
            
        Returns:
            Série com valores do RSI
        """
        delta = precos.diff()
        
        ganhos = delta.copy()
        perdas = delta.copy()
        
        ganhos[ganhos < 0] = 0
        perdas[perdas > 0] = 0
        perdas = abs(perdas)
        
        media_ganhos = ganhos.rolling(window=periodo).mean()
        media_perdas = perdas.rolling(window=periodo).mean()
        
        rs = media_ganhos / media_perdas
        rsi = 100 - (100 / (1 + rs))
        
        return rsi