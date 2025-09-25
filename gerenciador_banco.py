import sqlite3
from typing import Dict, List, Optional
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "trading_system.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._criar_tabelas()

    def _criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ativo TEXT,
            tipo TEXT,
            preco_entrada REAL
        )
        """)
        # tabela de performance diaria simples
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_diaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE UNIQUE,
            capital_inicial REAL,
            capital_final REAL,
            pnl_dia REAL
        )
        """)
        self.conn.commit()

    def obter_trades(self, filtros: dict = None) -> list:
        try:
            query = "SELECT id, timestamp, ativo, tipo, preco_entrada FROM trades"
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            keys = ['id', 'timestamp', 'ativo', 'tipo', 'preco_entrada']
            return [dict(zip(keys, r)) for r in rows]
        except Exception as e:
            logger.error(f"Erro obtendo trades: {e}")
            return []


    def salvar_trade(self, trade: Dict) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO trades (timestamp, ativo, tipo, preco_entrada) VALUES (?, ?, ?, ?)",
                (trade.get('timestamp'), trade.get('ativo'), trade.get('tipo'), trade.get('preco_entrada'))
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Erro salvando trade: {e}")
            return 0

    def backup_database(self, backup_path: str = None) -> str:
        import shutil, datetime
        if not backup_path:
            backup_path = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup criado: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Erro criando backup: {e}")
            return ""
