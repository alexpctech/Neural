"""
Sistema de logging especializado para trading.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from logging.handlers import RotatingFileHandler
import threading
import queue

class TradingLogger:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TradingLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
            
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._setup_directories()
        self._setup_loggers()
        self._setup_queue()
        
    def _setup_directories(self):
        """Cria estrutura de diretórios para logs."""
        base_dir = Path("logs")
        self.log_dirs = {
            "trades": base_dir / "trades",
            "performance": base_dir / "performance",
            "errors": base_dir / "errors",
            "market_data": base_dir / "market_data",
            "agents": base_dir / "agents",
            "system": base_dir / "system"
        }
        
        for directory in self.log_dirs.values():
            directory.mkdir(parents=True, exist_ok=True)
            
    def _setup_loggers(self):
        """Configura diferentes loggers para cada tipo de log."""
        self.loggers = {}
        
        for log_type, directory in self.log_dirs.items():
            logger = logging.getLogger(f"trading.{log_type}")
            logger.setLevel(logging.DEBUG)
            
            # Arquivo rotativo (10MB, máximo 50 arquivos)
            file_handler = RotatingFileHandler(
                directory / f"{log_type}.log",
                maxBytes=10*1024*1024,
                backupCount=50
            )
            
            # Formato específico para cada tipo
            if log_type == "trades":
                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] TRADE: %(message)s'
                )
            elif log_type == "performance":
                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] PERF: %(message)s'
                )
            else:
                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                )
                
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Console handler para erros
            if log_type == "errors":
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
                
            self.loggers[log_type] = logger
            
    def _setup_queue(self):
        """Configura fila assíncrona para logging."""
        self.log_queue = queue.Queue()
        self._start_queue_worker()
        
    def _start_queue_worker(self):
        """Inicia worker thread para processar logs."""
        def worker():
            while True:
                try:
                    record = self.log_queue.get()
                    if record is None:
                        break
                    self._process_log_record(record)
                except Exception as e:
                    print(f"Erro no processamento de log: {e}")
                    
        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()
        
    def _process_log_record(self, record: Dict[str, Any]):
        """Processa registro de log da fila."""
        logger = self.loggers.get(record["type"])
        if logger:
            logger.log(
                record["level"],
                self._format_message(record["message"], record.get("extra", {}))
            )
            
    def _format_message(self, message: str, extra: Dict[str, Any]) -> str:
        """Formata mensagem de log com dados extras."""
        if extra:
            try:
                extra_str = json.dumps(extra, default=str)
                return f"{message} | {extra_str}"
            except:
                return message
        return message
        
    def log_trade(self, message: str, trade_data: Dict[str, Any]):
        """
        Registra informação de trade.
        
        Args:
            message: Mensagem descritiva
            trade_data: Dados do trade
        """
        self.log_queue.put({
            "type": "trades",
            "level": logging.INFO,
            "message": message,
            "extra": trade_data
        })
        
    def log_performance(self, metric_name: str, value: float, extra: Optional[Dict] = None):
        """
        Registra métrica de performance.
        
        Args:
            metric_name: Nome da métrica
            value: Valor
            extra: Dados adicionais
        """
        self.log_queue.put({
            "type": "performance",
            "level": logging.INFO,
            "message": f"{metric_name}: {value}",
            "extra": extra
        })
        
    def log_error(self, message: str, error: Optional[Exception] = None):
        """
        Registra erro.
        
        Args:
            message: Mensagem de erro
            error: Exceção (opcional)
        """
        extra = None
        if error:
            extra = {
                "error_type": error.__class__.__name__,
                "error_msg": str(error)
            }
            
        self.log_queue.put({
            "type": "errors",
            "level": logging.ERROR,
            "message": message,
            "extra": extra
        })
        
    def log_market_data(self, data_type: str, data: Dict[str, Any]):
        """
        Registra dados de mercado.
        
        Args:
            data_type: Tipo de dado
            data: Dados de mercado
        """
        self.log_queue.put({
            "type": "market_data",
            "level": logging.INFO,
            "message": f"Market Data [{data_type}]",
            "extra": data
        })
        
    def log_agent(self, agent_name: str, action: str, data: Dict[str, Any]):
        """
        Registra ação de agente.
        
        Args:
            agent_name: Nome do agente
            action: Ação realizada
            data: Dados da ação
        """
        self.log_queue.put({
            "type": "agents",
            "level": logging.INFO,
            "message": f"Agent {agent_name}: {action}",
            "extra": data
        })
        
    def log_system(self, message: str, level: int = logging.INFO, extra: Optional[Dict] = None):
        """
        Registra evento do sistema.
        
        Args:
            message: Mensagem
            level: Nível de log
            extra: Dados adicionais
        """
        self.log_queue.put({
            "type": "system",
            "level": level,
            "message": message,
            "extra": extra
        })
        
    def shutdown(self):
        """Finaliza sistema de logging."""
        self.log_queue.put(None)
        self.worker_thread.join()
        
    def get_latest_logs(self, log_type: str, n: int = 100) -> List[str]:
        """
        Obtém últimos logs de um tipo específico.
        
        Args:
            log_type: Tipo de log
            n: Número de logs
            
        Returns:
            Lista com últimos logs
        """
        log_file = self.log_dirs[log_type] / f"{log_type}.log"
        if not log_file.exists():
            return []
            
        with open(log_file, "r") as f:
            lines = f.readlines()
            return lines[-n:]