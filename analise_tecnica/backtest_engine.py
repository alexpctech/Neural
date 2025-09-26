"""
Engine de Backtesting para Análise Técnica
Testa estratégias baseadas em indicadores técnicos
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from .indicadores_tecnicos import AnalisisTecnica, IndicadorResult
from .detector_padroes import DetectorPadroes, PadraoDetectado

@dataclass
class Posicao:
    """Representa uma posição de trading"""
    simbolo: str
    entrada_preco: float
    entrada_data: str
    quantidade: int
    tipo: str  # 'LONG' ou 'SHORT'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    saida_preco: Optional[float] = None
    saida_data: Optional[str] = None
    resultado: Optional[float] = None
    motivo_saida: Optional[str] = None

@dataclass
class HistoricoBacktest:
    """Histórico completo do backtest"""
    capital_inicial: float
    capital_final: float
    total_trades: int
    trades_vencedores: int
    trades_perdedores: int
    maior_ganho: float
    maior_perda: float
    drawdown_maximo: float
    retorno_total: float
    sharpe_ratio: float
    posicoes: List[Posicao] = field(default_factory=list)
    equity_curve: List[Tuple[str, float]] = field(default_factory=list)

class BacktestEngine:
    """
    Engine de backtesting para estratégias de análise técnica
    """
    
    def __init__(self, capital_inicial: float = 100000.0):
        self.capital_inicial = capital_inicial
        self.capital_atual = capital_inicial
        self.logger = logging.getLogger(__name__)
        self.analise_tecnica = AnalisisTecnica()
        self.detector_padroes = DetectorPadroes()
        
    def executar_backtest_indicador(self, 
                                  dados: pd.DataFrame,
                                  indicador: str,
                                  parametros: Dict,
                                  stop_loss_pct: float = 0.02,
                                  take_profit_pct: float = 0.04) -> HistoricoBacktest:
        """
        Executa backtest baseado em um indicador específico
        
        Args:
            dados: DataFrame com colunas ['data', 'open', 'high', 'low', 'close', 'volume']
            indicador: Nome do indicador ('RSI', 'MACD', 'SMA', etc.)
            parametros: Parâmetros do indicador
            stop_loss_pct: Percentual de stop loss
            take_profit_pct: Percentual de take profit
            
        Returns:
            HistoricoBacktest com resultados
        """
        self.capital_atual = self.capital_inicial
        posicoes = []
        equity_curve = []
        posicao_atual = None
        
        # Calcular indicador
        precos = dados['close'].tolist()
        
        if indicador == 'RSI':
            resultado_indicador = self.analise_tecnica.calcular_rsi(
                precos, parametros.get('periodo', 14)
            )
        elif indicador == 'MACD':
            resultado_indicador = self.analise_tecnica.calcular_macd(
                precos,
                parametros.get('rapido', 12),
                parametros.get('lento', 26),
                parametros.get('sinal', 9)
            )
        elif indicador == 'SMA':
            resultado_indicador = self.analise_tecnica.calcular_media_movel(
                precos, parametros.get('periodo', 20), 'SMA'
            )
        else:
            raise ValueError(f"Indicador {indicador} não suportado")
        
        # Executar backtest
        for i in range(len(resultado_indicador.sinais)):
            data_atual = dados.iloc[i + len(dados) - len(resultado_indicador.sinais)]['data']
            preco_atual = dados.iloc[i + len(dados) - len(resultado_indicador.sinais)]['close']
            sinal = resultado_indicador.sinais[i]
            
            # Verificar se há posição aberta
            if posicao_atual:
                # Verificar condições de saída
                if posicao_atual.tipo == 'LONG':
                    # Stop loss ou take profit
                    if (posicao_atual.stop_loss and preco_atual <= posicao_atual.stop_loss) or \
                       (posicao_atual.take_profit and preco_atual >= posicao_atual.take_profit):
                        posicao_atual = self._fechar_posicao(posicao_atual, preco_atual, data_atual, 
                                                           "Stop/Take Profit")
                        posicoes.append(posicao_atual)
                        posicao_atual = None
                    # Sinal de venda
                    elif sinal == 'VENDA':
                        posicao_atual = self._fechar_posicao(posicao_atual, preco_atual, data_atual, 
                                                           "Sinal de venda")
                        posicoes.append(posicao_atual)
                        posicao_atual = None
                
                elif posicao_atual.tipo == 'SHORT':
                    # Stop loss ou take profit para short
                    if (posicao_atual.stop_loss and preco_atual >= posicao_atual.stop_loss) or \
                       (posicao_atual.take_profit and preco_atual <= posicao_atual.take_profit):
                        posicao_atual = self._fechar_posicao(posicao_atual, preco_atual, data_atual, 
                                                           "Stop/Take Profit")
                        posicoes.append(posicao_atual)
                        posicao_atual = None
                    # Sinal de compra
                    elif sinal == 'COMPRA':
                        posicao_atual = self._fechar_posicao(posicao_atual, preco_atual, data_atual, 
                                                           "Sinal de compra")
                        posicoes.append(posicao_atual)
                        posicao_atual = None
            
            # Abrir nova posição se não há posição atual
            if not posicao_atual:
                if sinal == 'COMPRA':
                    posicao_atual = self._abrir_posicao('LONG', preco_atual, data_atual, 
                                                      stop_loss_pct, take_profit_pct)
                elif sinal == 'VENDA':
                    posicao_atual = self._abrir_posicao('SHORT', preco_atual, data_atual, 
                                                      stop_loss_pct, take_profit_pct)
            
            # Registrar equity curve
            equity_curve.append((data_atual, self.capital_atual))
        
        # Fechar posição final se ainda aberta
        if posicao_atual:
            ultima_data = dados.iloc[-1]['data']
            ultimo_preco = dados.iloc[-1]['close']
            posicao_atual = self._fechar_posicao(posicao_atual, ultimo_preco, ultima_data, 
                                               "Fim do período")
            posicoes.append(posicao_atual)
        
        # Calcular métricas
        return self._calcular_metricas(posicoes, equity_curve)
    
    def executar_backtest_padroes(self, 
                                dados: pd.DataFrame,
                                min_confianca: float = 70.0) -> HistoricoBacktest:
        """
        Executa backtest baseado em padrões gráficos
        """
        self.capital_atual = self.capital_inicial
        posicoes = []
        equity_curve = []
        
        # Detectar padrões em janela deslizante
        janela = 50  # Janela de análise
        
        for i in range(janela, len(dados) - 10):  # Deixar margem para trades
            dados_janela = dados.iloc[i-janela:i]
            precos_janela = dados_janela['close'].tolist()
            
            # Detectar padrões
            padroes = self.detector_padroes.detectar_todos_padroes(precos_janela)
            padroes_validos = [p for p in padroes if p.confianca >= min_confianca]
            
            if padroes_validos:
                # Usar o padrão de maior confiança
                padrao = padroes_validos[0]
                
                # Verificar se ainda é válido (padrão recente)
                if padrao.fim >= len(precos_janela) - 10:
                    data_entrada = dados.iloc[i]['data']
                    
                    if padrao.sinal == 'COMPRA' and padrao.preco_entrada:
                        posicao = Posicao(
                            simbolo="TESTE",
                            entrada_preco=padrao.preco_entrada,
                            entrada_data=data_entrada,
                            quantidade=int(self.capital_atual * 0.1 / padrao.preco_entrada),
                            tipo='LONG',
                            stop_loss=padrao.stop_loss,
                            take_profit=padrao.take_profit
                        )
                        
                        # Simular execução nos próximos períodos
                        posicao_fechada = self._simular_execucao_padrao(posicao, dados.iloc[i:i+20])
                        if posicao_fechada.resultado is not None:
                            self.capital_atual += posicao_fechada.resultado
                            posicoes.append(posicao_fechada)
                    
                    elif padrao.sinal == 'VENDA' and padrao.preco_entrada:
                        posicao = Posicao(
                            simbolo="TESTE",
                            entrada_preco=padrao.preco_entrada,
                            entrada_data=data_entrada,
                            quantidade=int(self.capital_atual * 0.1 / padrao.preco_entrada),
                            tipo='SHORT',
                            stop_loss=padrao.stop_loss,
                            take_profit=padrao.take_profit
                        )
                        
                        posicao_fechada = self._simular_execucao_padrao(posicao, dados.iloc[i:i+20])
                        if posicao_fechada.resultado is not None:
                            self.capital_atual += posicao_fechada.resultado
                            posicoes.append(posicao_fechada)
            
            equity_curve.append((dados.iloc[i]['data'], self.capital_atual))
        
        return self._calcular_metricas(posicoes, equity_curve)
    
    def _abrir_posicao(self, tipo: str, preco: float, data: str, 
                      stop_loss_pct: float, take_profit_pct: float) -> Posicao:
        """Abre uma nova posição"""
        tamanho_posicao = self.capital_atual * 0.1  # 10% do capital
        quantidade = int(tamanho_posicao / preco)
        
        if tipo == 'LONG':
            stop_loss = preco * (1 - stop_loss_pct)
            take_profit = preco * (1 + take_profit_pct)
        else:  # SHORT
            stop_loss = preco * (1 + stop_loss_pct)
            take_profit = preco * (1 - take_profit_pct)
        
        return Posicao(
            simbolo="TESTE",
            entrada_preco=preco,
            entrada_data=data,
            quantidade=quantidade,
            tipo=tipo,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def _fechar_posicao(self, posicao: Posicao, preco_saida: float, 
                       data_saida: str, motivo: str) -> Posicao:
        """Fecha uma posição existente"""
        posicao.saida_preco = preco_saida
        posicao.saida_data = data_saida
        posicao.motivo_saida = motivo
        
        if posicao.tipo == 'LONG':
            resultado = (preco_saida - posicao.entrada_preco) * posicao.quantidade
        else:  # SHORT
            resultado = (posicao.entrada_preco - preco_saida) * posicao.quantidade
        
        posicao.resultado = resultado
        self.capital_atual += resultado
        
        return posicao
    
    def _simular_execucao_padrao(self, posicao: Posicao, dados_futuros: pd.DataFrame) -> Posicao:
        """Simula execução de uma posição baseada em padrão"""
        for _, row in dados_futuros.iterrows():
            preco = row['close']
            data = row['data']
            
            # Verificar condições de saída
            if posicao.tipo == 'LONG':
                if (posicao.stop_loss and preco <= posicao.stop_loss) or \
                   (posicao.take_profit and preco >= posicao.take_profit):
                    return self._fechar_posicao(posicao, preco, data, "Stop/Take Profit")
            else:  # SHORT
                if (posicao.stop_loss and preco >= posicao.stop_loss) or \
                   (posicao.take_profit and preco <= posicao.take_profit):
                    return self._fechar_posicao(posicao, preco, data, "Stop/Take Profit")
        
        # Se não saiu, fechar na última data
        ultimo_preco = dados_futuros.iloc[-1]['close']
        ultima_data = dados_futuros.iloc[-1]['data']
        return self._fechar_posicao(posicao, ultimo_preco, ultima_data, "Fim do período")
    
    def _calcular_metricas(self, posicoes: List[Posicao], 
                          equity_curve: List[Tuple[str, float]]) -> HistoricoBacktest:
        """Calcula métricas do backtest"""
        if not posicoes:
            return HistoricoBacktest(
                capital_inicial=self.capital_inicial,
                capital_final=self.capital_atual,
                total_trades=0,
                trades_vencedores=0,
                trades_perdedores=0,
                maior_ganho=0,
                maior_perda=0,
                drawdown_maximo=0,
                retorno_total=0,
                sharpe_ratio=0,
                posicoes=[],
                equity_curve=equity_curve
            )
        
        resultados = [p.resultado for p in posicoes if p.resultado is not None]
        
        trades_vencedores = len([r for r in resultados if r > 0])
        trades_perdedores = len([r for r in resultados if r < 0])
        maior_ganho = max(resultados) if resultados else 0
        maior_perda = min(resultados) if resultados else 0
        
        # Calcular drawdown máximo
        picos = []
        drawdown_maximo = 0
        pico_atual = self.capital_inicial
        
        for _, capital in equity_curve:
            if capital > pico_atual:
                pico_atual = capital
            picos.append(pico_atual)
            
            drawdown = (pico_atual - capital) / pico_atual
            if drawdown > drawdown_maximo:
                drawdown_maximo = drawdown
        
        retorno_total = (self.capital_atual - self.capital_inicial) / self.capital_inicial
        
        # Calcular Sharpe ratio simplificado
        if resultados:
            retornos_pct = [r / self.capital_inicial for r in resultados]
            media_retornos = np.mean(retornos_pct)
            std_retornos = np.std(retornos_pct)
            sharpe_ratio = media_retornos / std_retornos if std_retornos > 0 else 0
        else:
            sharpe_ratio = 0
        
        return HistoricoBacktest(
            capital_inicial=self.capital_inicial,
            capital_final=self.capital_atual,
            total_trades=len(posicoes),
            trades_vencedores=trades_vencedores,
            trades_perdedores=trades_perdedores,
            maior_ganho=maior_ganho,
            maior_perda=maior_perda,
            drawdown_maximo=drawdown_maximo * 100,  # Em percentual
            retorno_total=retorno_total * 100,  # Em percentual
            sharpe_ratio=sharpe_ratio,
            posicoes=posicoes,
            equity_curve=equity_curve
        )
    
    def gerar_relatorio_backtest(self, historico: HistoricoBacktest) -> str:
        """Gera relatório detalhado do backtest"""
        win_rate = (historico.trades_vencedores / historico.total_trades * 100) if historico.total_trades > 0 else 0
        
        relatorio = "=== RELATÓRIO DE BACKTEST ===\n\n"
        relatorio += f"Capital Inicial: R$ {historico.capital_inicial:,.2f}\n"
        relatorio += f"Capital Final: R$ {historico.capital_final:,.2f}\n"
        relatorio += f"Retorno Total: {historico.retorno_total:.2f}%\n"
        relatorio += f"Drawdown Máximo: {historico.drawdown_maximo:.2f}%\n\n"
        
        relatorio += f"Total de Trades: {historico.total_trades}\n"
        relatorio += f"Trades Vencedores: {historico.trades_vencedores}\n"
        relatorio += f"Trades Perdedores: {historico.trades_perdedores}\n"
        relatorio += f"Win Rate: {win_rate:.1f}%\n\n"
        
        relatorio += f"Maior Ganho: R$ {historico.maior_ganho:,.2f}\n"
        relatorio += f"Maior Perda: R$ {historico.maior_perda:,.2f}\n"
        relatorio += f"Sharpe Ratio: {historico.sharpe_ratio:.3f}\n\n"
        
        relatorio += "=== ÚLTIMOS 5 TRADES ===\n"
        for posicao in historico.posicoes[-5:]:
            resultado_pct = (posicao.resultado / (posicao.entrada_preco * posicao.quantidade)) * 100
            relatorio += f"{posicao.entrada_data}: {posicao.tipo} - "
            relatorio += f"R$ {posicao.entrada_preco:.2f} → R$ {posicao.saida_preco:.2f} "
            relatorio += f"({resultado_pct:+.1f}%) - {posicao.motivo_saida}\n"
        
        return relatorio


# Exemplo de uso
if __name__ == "__main__":
    # Dados de exemplo
    dados_exemplo = pd.DataFrame({
        'data': [f"2024-{i//30+1:02d}-{i%30+1:02d}" for i in range(100)],
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 105,
        'low': np.random.randn(100).cumsum() + 95,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Executar backtest
    engine = BacktestEngine(capital_inicial=100000)
    
    # Teste com RSI
    resultado = engine.executar_backtest_indicador(
        dados_exemplo, 
        'RSI', 
        {'periodo': 14}
    )
    
    print(engine.gerar_relatorio_backtest(resultado))