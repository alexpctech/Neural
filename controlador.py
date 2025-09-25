"""
Controlador central do sistema Neural Trading
"""
from configuracao.gerenciador_configuracao import GerenciadorConfiguracao
from dados_mercado.market_manager import MarketDataManager
from negociacao.engine import TradingEngine
from agentes.ensemble_agent import EnsembleAgent
from gestao_risco.risk_manager import RiskManager
from backteste.backtest_engine import BacktestEngine
from utilitarios.logger import setup_logger
from utilitarios.gpu_manager import GPUManager
from typing import Dict, List, Optional
import asyncio
import logging
import threading
import queue

class NeuralTradingController:
    """
    Controlador central que gerencia todos os módulos do sistema.
    Mantém a modularidade permitindo fácil manutenção e reuso.
    """
    def __init__(self):
        # Configura logging
        self.logger = setup_logger('NeuralTrading')
        
        # Fila de mensagens entre módulos
        self.message_queue = queue.Queue()
        
        # Inicializa componentes
        self.config_manager = GerenciadorConfiguracao()
        self.market_manager = MarketDataManager()
        self.trading_engine = TradingEngine()
        self.ensemble_agent = EnsembleAgent()
        self.risk_manager = RiskManager()
        self.backtest_engine = BacktestEngine()
        self.gpu_manager = GPUManager()
        
        # Estado do sistema
        self.is_running = False
        self.is_backtesting = False
        self.active_strategies = []
        
    def initialize(self):
        """Inicializa todos os módulos necessários"""
        try:
            # Carrega configurações
            self.config = self.config_manager.load_config()
            
            # Configura GPU se disponível
            self.gpu_manager.setup()
            
            # Inicializa conexões com mercado
            self.market_manager.initialize(self.config['apis'])
            
            # Configura engine de trading
            self.trading_engine.setup(
                market_manager=self.market_manager,
                risk_manager=self.risk_manager
            )
            
            # Carrega estratégias
            self.load_strategies()
            
            self.logger.info("Sistema inicializado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistema: {e}")
            return False
            
    def load_strategies(self):
        """Carrega e configura estratégias ativas"""
        strategies = self.config_manager.get_active_strategies()
        self.ensemble_agent.load_strategies(strategies)
        self.active_strategies = strategies
        
    async def start_trading(self):
        """Inicia operações de trading"""
        if self.is_running:
            self.logger.warning("Sistema já está em execução")
            return
            
        try:
            self.is_running = True
            
            # Inicia threads de monitoramento
            self.start_monitoring_threads()
            
            # Inicia engine de trading
            await self.trading_engine.start()
            
            self.logger.info("Sistema de trading iniciado")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar trading: {e}")
            self.is_running = False
            
    def stop_trading(self):
        """Para operações de trading"""
        if not self.is_running:
            return
            
        try:
            self.is_running = False
            self.trading_engine.stop()
            self.logger.info("Sistema de trading parado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar trading: {e}")
            
    def start_monitoring_threads(self):
        """Inicia threads de monitoramento"""
        # Thread de processamento de mensagens
        threading.Thread(
            target=self.process_message_queue,
            daemon=True
        ).start()
        
        # Thread de monitoramento de mercado
        threading.Thread(
            target=self.market_manager.start_monitoring,
            daemon=True
        ).start()
        
        # Thread de monitoramento de risco
        threading.Thread(
            target=self.risk_manager.monitor_positions,
            daemon=True
        ).start()
        
    def process_message_queue(self):
        """Processa mensagens entre módulos"""
        while self.is_running:
            try:
                message = self.message_queue.get(timeout=1)
                self.handle_message(message)
            except queue.Empty:
                continue
                
    def handle_message(self, message: Dict):
        """Processa mensagens do sistema"""
        msg_type = message.get('type')
        data = message.get('data')
        
        if msg_type == 'market_data':
            self.ensemble_agent.process_market_data(data)
            
        elif msg_type == 'trade_signal':
            self.trading_engine.process_signal(data)
            
        elif msg_type == 'risk_alert':
            self.handle_risk_alert(data)
            
        elif msg_type == 'system_status':
            self.update_system_status(data)
            
    def handle_risk_alert(self, alert: Dict):
        """Processa alertas de risco"""
        if alert['level'] == 'high':
            self.stop_trading()
            
    def update_system_status(self, status: Dict):
        """Atualiza status do sistema"""
        pass
        
    async def run_backtest(self, config: Dict):
        """Executa backtesting"""
        self.is_backtesting = True
        try:
            results = await self.backtest_engine.run(
                strategies=self.active_strategies,
                config=config
            )
            self.logger.info("Backtest concluído")
            return results
        finally:
            self.is_backtesting = False
            
    def get_system_status(self) -> Dict:
        """Retorna status atual do sistema"""
        return {
            'is_running': self.is_running,
            'is_backtesting': self.is_backtesting,
            'active_strategies': len(self.active_strategies),
            'gpu_status': self.gpu_manager.get_status(),
            'market_status': self.market_manager.get_status(),
            'risk_status': self.risk_manager.get_status()
        }

# Exemplo de uso
async def main():
    controller = NeuralTradingController()
    if controller.initialize():
        await controller.start_trading()
        
if __name__ == '__main__':
    asyncio.run(main())