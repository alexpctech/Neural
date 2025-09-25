# Sistema de Trading Neural v4.0
# Desenvolvido por AlexPCTech
# Última atualização: 25/09/2025

from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
import asyncio
import ccxt
import json
import logging
import numpy as np
import os
import pandas as pd
import random
import requests
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import venv
import websockets
import yfinance as yf
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import psutil
import GPUtil

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sistema.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NeuralTrading')

class NeuralTradingSystem:
    def __init__(self):
        self.root_dir = Path(__file__).parent.absolute()
        self.frontend_dir = self.root_dir / 'frontend'
        self.venv_dir = self.root_dir / 'venv'
        self.config_file = self.root_dir / 'configuracao' / 'config.json'
        self.app = FastAPI()
        self.setup_fastapi()
        self.load_config()
        self.connected_clients: List[WebSocket] = []
        self.trading_active = False
        self.monitor_thread = None
        self.system_info_thread = None

    def setup_fastapi(self):
        """Configura o servidor FastAPI"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket_connection(websocket)

        @self.app.get("/api/system/info")
        async def get_system_info():
            return self.get_system_info()

        @self.app.post("/api/trading/start")
        async def start_trading():
            return await self.start_trading()

        @self.app.post("/api/trading/stop")
        async def stop_trading():
            return await self.stop_trading()

    def load_config(self):
        """Carrega configurações do sistema"""
        try:
            with open(self.config_file) as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "apis": {},
                "estrategias": {},
                "parametros": {
                    "intervalo_atualizacao": 60,
                    "modo_simulacao": True
                }
            }
            self.save_config()

    def save_config(self):
        """Salva configurações do sistema"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_system_info(self) -> Dict:
        """Obtém informações do sistema"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        gpu_info = []
        
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_info.append({
                    'name': gpu.name,
                    'load': gpu.load * 100,
                    'memory_used': gpu.memoryUsed,
                    'memory_total': gpu.memoryTotal
                })
        except:
            pass

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'gpu_info': gpu_info,
            'python_version': sys.version,
            'trading_active': self.trading_active
        }

    async def broadcast_message(self, message: Dict):
        """Envia mensagem para todos os clientes conectados"""
        dead_clients = []
        for client in self.connected_clients:
            try:
                await client.send_json(message)
            except:
                dead_clients.append(client)
        
        for client in dead_clients:
            self.connected_clients.remove(client)

    async def handle_websocket_connection(self, websocket: WebSocket):
        """Gerencia conexões WebSocket"""
        await websocket.accept()
        self.connected_clients.append(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                await self.handle_websocket_message(websocket, data)
        except:
            self.connected_clients.remove(websocket)

    async def handle_websocket_message(self, websocket: WebSocket, data: Dict):
        """Processa mensagens recebidas via WebSocket"""
        message_type = data.get('type')
        if message_type == 'subscribe':
            # Implementar lógica de subscrição
            pass
        elif message_type == 'unsubscribe':
            # Implementar lógica de cancelamento de subscrição
            pass

    def monitor_system(self):
        """Monitora recursos do sistema"""
        while True:
            sys_info = self.get_system_info()
            asyncio.run(self.broadcast_message({
                'type': 'system_info',
                'data': sys_info
            }))
            time.sleep(5)

    async def start_trading(self) -> Dict:
        """Inicia o sistema de trading"""
        if not self.trading_active:
            self.trading_active = True
            # Iniciar threads de monitoramento
            if not self.monitor_thread:
                self.monitor_thread = threading.Thread(target=self.monitor_system)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
            return {"status": "success", "message": "Sistema de trading iniciado"}
        return {"status": "warning", "message": "Sistema já está ativo"}

    async def stop_trading(self) -> Dict:
        """Para o sistema de trading"""
        if self.trading_active:
            self.trading_active = False
            return {"status": "success", "message": "Sistema de trading parado"}
        return {"status": "warning", "message": "Sistema já está parado"}

    def setup_environment(self) -> bool:
        """Configura o ambiente de desenvolvimento"""
        try:
            # Verifica e cria ambiente virtual Python
            if not self.venv_dir.exists():
                logger.info("Criando ambiente virtual Python...")
                venv.create(self.venv_dir, with_pip=True)

            # Instala dependências Python
            pip_path = self.venv_dir / 'Scripts' / 'pip.exe'
            subprocess.run([str(pip_path), 'install', '-r', 'requirements.txt'], check=True)

            # Verifica Node.js e instala dependências do frontend
            if self.frontend_dir.exists():
                os.chdir(self.frontend_dir)
                subprocess.run(['npm', 'install'], check=True)
                os.chdir(self.root_dir)

            return True
        except Exception as e:
            logger.error(f"Erro ao configurar ambiente: {e}")
            return False

    def run(self):
        """Inicia o sistema completo"""
        if not self.setup_environment():
            logger.error("Falha ao configurar ambiente")
            return

        # Inicia o frontend em um processo separado
        frontend_process = None
        if self.frontend_dir.exists():
            os.chdir(self.frontend_dir)
            frontend_process = subprocess.Popen(['npm', 'start'])
            os.chdir(self.root_dir)

        try:
            # Inicia o servidor FastAPI
            uvicorn.run(
                self.app, 
                host="0.0.0.0", 
                port=5000,
                log_level="info"
            )
        finally:
            if frontend_process:
                frontend_process.terminate()

def main():
    """Função principal"""
    sistema = NeuralTradingSystem()
    sistema.run()

if __name__ == "__main__":
    main()


# ============================================================================
# CONFIGURADOR AVANÇADO DO SISTEMA v4.0
# ============================================================================


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)
