"""
Testes para o Sistema de Análise Técnica
"""

import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch
import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analise_tecnica.indicadores_tecnicos import AnalisisTecnica
from analise_tecnica.detector_padroes import DetectorPadroes
from analise_tecnica.backtest_engine import BacktestEngine

class TestIndicadoresTecnicos(unittest.TestCase):
    """Testes para indicadores técnicos"""
    
    def setUp(self):
        self.analise = AnalisisTecnica()
        self.precos_teste = [
            100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
            111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
            119, 121, 123, 122, 124, 126, 125, 127, 129, 128
        ]
    
    def test_calcular_rsi(self):
        """Testa cálculo do RSI"""
        resultado = self.analise.calcular_rsi(self.precos_teste, periodo=14)
        
        self.assertEqual(resultado.nome, 'RSI')
        self.assertIsInstance(resultado.valores, list)
        self.assertIsInstance(resultado.sinais, list)
        self.assertEqual(len(resultado.valores), len(resultado.sinais))
        self.assertTrue(all(0 <= valor <= 100 for valor in resultado.valores))
        
    def test_calcular_macd(self):
        """Testa cálculo do MACD"""
        resultado = self.analise.calcular_macd(self.precos_teste)
        
        self.assertEqual(resultado.nome, 'MACD')
        self.assertIsInstance(resultado.valores, list)
        self.assertIsInstance(resultado.sinais, list)
        self.assertEqual(len(resultado.valores), len(resultado.sinais))
        
    def test_calcular_bollinger_bands(self):
        """Testa cálculo das Bandas de Bollinger"""
        resultado = self.analise.calcular_bollinger_bands(self.precos_teste, periodo=10)
        
        self.assertIn('media', resultado)
        self.assertIn('superior', resultado)
        self.assertIn('inferior', resultado)
        
        # Verificar se banda superior > média > banda inferior
        for i in range(len(resultado['media'].valores)):
            self.assertGreaterEqual(
                resultado['superior'].valores[i], 
                resultado['media'].valores[i]
            )
            self.assertGreaterEqual(
                resultado['media'].valores[i], 
                resultado['inferior'].valores[i]
            )
    
    def test_calcular_media_movel(self):
        """Testa cálculo de médias móveis"""
        # Teste SMA
        resultado_sma = self.analise.calcular_media_movel(self.precos_teste, 10, 'SMA')
        self.assertEqual(resultado_sma.nome, 'SMA_10')
        
        # Teste EMA
        resultado_ema = self.analise.calcular_media_movel(self.precos_teste, 10, 'EMA')
        self.assertEqual(resultado_ema.nome, 'EMA_10')
        
    def test_analisar_multiplos_indicadores(self):
        """Testa análise com múltiplos indicadores"""
        resultados = self.analise.analisar_multiplos_indicadores(self.precos_teste)
        
        self.assertIn('RSI', resultados)
        self.assertTrue(len(resultados) > 1)
        
    def test_gerar_consenso_sinais(self):
        """Testa geração de consenso de sinais"""
        resultados = self.analise.analisar_multiplos_indicadores(self.precos_teste)
        consenso = self.analise.gerar_consenso_sinais(resultados)
        
        self.assertIsInstance(consenso, list)
        self.assertTrue(all(sinal in ['COMPRA', 'VENDA', 'NEUTRO'] for sinal in consenso))

class TestDetectorPadroes(unittest.TestCase):
    """Testes para detector de padrões"""
    
    def setUp(self):
        self.detector = DetectorPadroes(min_confianca=50.0)
        
        # Dados simulando um duplo topo
        self.precos_duplo_topo = [
            100, 102, 104, 106, 108, 110, 108, 106, 104, 102,  # Primeiro topo
            104, 106, 108, 110, 109, 107, 105, 103, 101, 99,   # Segundo topo
            101, 103, 105, 107, 109, 111, 109, 107, 105, 103
        ]
        
        # Dados simulando canal de alta
        self.precos_canal_alta = [
            100 + i * 0.5 + np.sin(i * 0.3) * 2 for i in range(40)
        ]
    
    def test_detectar_topos_fundos(self):
        """Testa detecção de topos e fundos"""
        topos, fundos = self.detector.detectar_topos_fundos(self.precos_duplo_topo)
        
        self.assertIsInstance(topos, list)
        self.assertIsInstance(fundos, list)
        self.assertTrue(len(topos) > 0)
        self.assertTrue(len(fundos) > 0)
    
    def test_detectar_duplo_topo(self):
        """Testa detecção de duplo topo"""
        topos, _ = self.detector.detectar_topos_fundos(self.precos_duplo_topo)
        
        if len(topos) >= 2:
            padrao = self.detector.detectar_duplo_topo(self.precos_duplo_topo, topos)
            
            if padrao:
                self.assertEqual(padrao.sinal, 'VENDA')
                self.assertGreaterEqual(padrao.confianca, 50.0)
    
    def test_detectar_todos_padroes(self):
        """Testa detecção de todos os padrões"""
        padroes = self.detector.detectar_todos_padroes(self.precos_duplo_topo)
        
        self.assertIsInstance(padroes, list)
        # Verificar se padrões estão ordenados por confiança
        if len(padroes) > 1:
            for i in range(len(padroes) - 1):
                self.assertGreaterEqual(padroes[i].confianca, padroes[i+1].confianca)
    
    def test_gerar_relatorio_padroes(self):
        """Testa geração de relatório"""
        padroes = self.detector.detectar_todos_padroes(self.precos_duplo_topo)
        relatorio = self.detector.gerar_relatorio_padroes(padroes)
        
        self.assertIsInstance(relatorio, str)
        self.assertTrue(len(relatorio) > 0)

class TestBacktestEngine(unittest.TestCase):
    """Testes para engine de backtesting"""
    
    def setUp(self):
        self.engine = BacktestEngine(capital_inicial=100000)
        
        # Criar dados de teste
        self.dados_teste = pd.DataFrame({
            'data': [f"2024-01-{i+1:02d}" for i in range(50)],
            'open': 100 + np.random.randn(50).cumsum() * 0.5,
            'high': 105 + np.random.randn(50).cumsum() * 0.5,
            'low': 95 + np.random.randn(50).cumsum() * 0.5,
            'close': 100 + np.random.randn(50).cumsum() * 0.5,
            'volume': np.random.randint(1000, 10000, 50)
        })
    
    def test_executar_backtest_rsi(self):
        """Testa backtest com RSI"""
        resultado = self.engine.executar_backtest_indicador(
            self.dados_teste,
            'RSI',
            {'periodo': 14}
        )
        
        self.assertIsInstance(resultado.capital_inicial, float)
        self.assertIsInstance(resultado.capital_final, float)
        self.assertIsInstance(resultado.total_trades, int)
        self.assertGreaterEqual(resultado.total_trades, 0)
    
    def test_executar_backtest_macd(self):
        """Testa backtest com MACD"""
        resultado = self.engine.executar_backtest_indicador(
            self.dados_teste,
            'MACD',
            {'rapido': 12, 'lento': 26, 'sinal': 9}
        )
        
        self.assertIsInstance(resultado.retorno_total, float)
        self.assertIsInstance(resultado.drawdown_maximo, float)
    
    def test_executar_backtest_padroes(self):
        """Testa backtest com padrões"""
        resultado = self.engine.executar_backtest_padroes(self.dados_teste)
        
        self.assertIsInstance(resultado.sharpe_ratio, float)
        self.assertIsInstance(resultado.posicoes, list)
    
    def test_gerar_relatorio_backtest(self):
        """Testa geração de relatório de backtest"""
        resultado = self.engine.executar_backtest_indicador(
            self.dados_teste,
            'RSI',
            {'periodo': 14}
        )
        
        relatorio = self.engine.gerar_relatorio_backtest(resultado)
        
        self.assertIsInstance(relatorio, str)
        self.assertIn('RELATÓRIO DE BACKTEST', relatorio)
        self.assertIn('Capital Inicial', relatorio)
        self.assertIn('Capital Final', relatorio)

class TestIntegracao(unittest.TestCase):
    """Testes de integração do sistema completo"""
    
    def test_fluxo_completo_analise(self):
        """Testa fluxo completo de análise técnica"""
        # Dados de teste
        precos = [100 + i + np.sin(i * 0.1) * 5 for i in range(50)]
        
        # Análise técnica
        analise = AnalisisTecnica()
        indicadores = analise.analisar_multiplos_indicadores(precos)
        
        self.assertTrue(len(indicadores) > 0)
        
        # Detecção de padrões
        detector = DetectorPadroes()
        padroes = detector.detectar_todos_padroes(precos)
        
        # Consenso de sinais
        consenso = analise.gerar_consenso_sinais(indicadores)
        
        self.assertIsInstance(consenso, list)
        
        # Relatórios
        relatorio_padroes = detector.gerar_relatorio_padroes(padroes)
        
        self.assertIsInstance(relatorio_padroes, str)

if __name__ == '__main__':
    # Executar todos os testes
    unittest.main(verbosity=2)