"""
Sistema de gerenciamento seguro de credenciais para APIs.
"""
import os
from typing import Dict, Optional
from pathlib import Path
import base64
from cryptography.fernet import Fernet
import json

class APICredentials:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APICredentials, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._key = self._generate_or_load_key()
        self._cipher_suite = Fernet(self._key)
        self._credentials = self._initialize_credentials()
        
    def _generate_or_load_key(self) -> bytes:
        """Gera ou carrega a chave de criptografia."""
        key_file = Path("config/.key")
        if not key_file.exists():
            key = Fernet.generate_key()
            key_file.parent.mkdir(exist_ok=True)
            key_file.write_bytes(key)
        return key_file.read_bytes()
        
    def _initialize_credentials(self) -> Dict[str, str]:
        """Inicializa as credenciais das APIs."""
        return {
            "OPENAI": {
                "api_key": "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"
            },
            "FINNHUB": {
                "api_key": "d333rg1r01qs3vinsp70",
                "email": "alexpctec10@gmail.com"
            },
            "ALPHA_VANTAGE": {
                "api_key": "3DR9GX49WS50J1U7"
            },
            "NEWSAPI": {
                "api_key": "50952a189d414efe8725bc3020a2e889"
            }
        }
        
    def get_credential(self, api_name: str, key: str) -> Optional[str]:
        """Recupera uma credencial específica."""
        api_config = self._credentials.get(api_name.upper())
        if api_config:
            return api_config.get(key)
        return None
        
    def get_all_credentials(self, api_name: str) -> Optional[Dict[str, str]]:
        """Recupera todas as credenciais de uma API."""
        return self._credentials.get(api_name.upper())
        
    @property
    def available_apis(self) -> list:
        """Retorna lista de APIs configuradas."""
        return list(self._credentials.keys())