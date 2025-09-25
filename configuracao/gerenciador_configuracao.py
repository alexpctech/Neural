"""
Módulo responsável pela configuração geral do sistema de trading.

Este módulo fornece:
1. Gerenciamento de configurações do sistema
2. Validação de parâmetros
3. Carregamento/salvamento de configurações
"""

from typing import Dict, List, Optional
import json
import os
from dataclasses import dataclass

@dataclass
class ConfiguracaoAPI:
    """
    Configuração das APIs de dados.
    
    Atributos:
        nome: Nome da API
        chave: Chave de acesso
        tipo: Tipo de dados fornecidos
        parametros: Parâmetros específicos
    """
    nome: str
    chave: str
    tipo: str
    parametros: Dict

@dataclass
class ConfiguracaoBacktest:
    """
    Configuração para backtesting.
    
    Atributos:
        periodo_inicial: Data inicial
        periodo_final: Data final
        capital_inicial: Capital inicial
        timeframes: Lista de timeframes para teste
        custos_operacionais: Custos por operação
    """
    periodo_inicial: str
    periodo_final: str
    capital_inicial: float
    timeframes: List[str]
    custos_operacionais: float

@dataclass
class ConfiguracaoGerenciamentoRisco:
    """
    Configuração de gerenciamento de risco.
    
    Atributos:
        stop_loss_maximo: Stop loss máximo permitido
        risco_maximo_dia: Risco máximo por dia
        risco_maximo_operacao: Risco máximo por operação
        drawdown_maximo: Drawdown máximo permitido
    """
    stop_loss_maximo: float
    risco_maximo_dia: float
    risco_maximo_operacao: float
    drawdown_maximo: float

class GerenciadorConfiguracao:
    """
    Gerencia todas as configurações do sistema de trading.
    """
    
    def __init__(self, arquivo_config: str = "configuracao/config.json"):
        """
        Inicializa o gerenciador de configuração.
        
        Args:
            arquivo_config: Caminho para o arquivo de configuração
        """
        self.arquivo_config = arquivo_config
        self.config = self._carregar_configuracao()
        self._validar_configuracao()
    
    def _carregar_configuracao(self) -> Dict:
        """
        Carrega configuração do arquivo.
        
        Returns:
            Dicionário com configurações
        """
        if not os.path.exists(self.arquivo_config):
            return self._criar_configuracao_padrao()
            
        try:
            with open(self.arquivo_config, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            return self._criar_configuracao_padrao()
    
    def _criar_configuracao_padrao(self) -> Dict:
        """
        Cria configuração padrão.
        
        Returns:
            Dicionário com configurações padrão
        """
        return {
            "ambiente": {
                "modo": "producao",  # ou "teste"
                "debug": False,
                "log_nivel": "INFO"
            },
            "apis": {
                "alpha_vantage": {
                    "nome": "Alpha Vantage",
                    "chave": "",
                    "tipo": "dados_mercado",
                    "parametros": {
                        "intervalo_requisicao": 12  # segundos
                    }
                }
            },
            "backtest": {
                "periodo_inicial": "2024-01-01",
                "periodo_final": "2024-12-31",
                "capital_inicial": 100000.0,
                "timeframes": ["1h", "4h", "1d"],
                "custos_operacionais": 0.1  # %
            },
            "gerenciamento_risco": {
                "stop_loss_maximo": 2.0,  # %
                "risco_maximo_dia": 5.0,  # %
                "risco_maximo_operacao": 1.0,  # %
                "drawdown_maximo": 10.0  # %
            },
            "estrategias": {
                "estrategia_exemplo": {
                    "ativa": True,
                    "parametros": {
                        "periodo_media_curta": 9,
                        "periodo_media_longa": 21,
                        "periodo_rsi": 14
                    }
                }
            }
        }
    
    def _validar_configuracao(self):
        """Valida a configuração carregada"""
        # Verifica campos obrigatórios
        campos_requeridos = [
            "ambiente",
            "apis",
            "backtest",
            "gerenciamento_risco",
            "estrategias"
        ]
        
        for campo in campos_requeridos:
            if campo not in self.config:
                raise ValueError(f"Campo obrigatório ausente: {campo}")
        
        # Valida ambiente
        ambiente = self.config["ambiente"]
        if ambiente["modo"] not in ["producao", "teste"]:
            raise ValueError("Modo de ambiente inválido")
        
        # Valida backtest
        backtest = self.config["backtest"]
        if backtest["capital_inicial"] <= 0:
            raise ValueError("Capital inicial deve ser positivo")
        if backtest["custos_operacionais"] < 0:
            raise ValueError("Custos operacionais não podem ser negativos")
        
        # Valida gerenciamento de risco
        risco = self.config["gerenciamento_risco"]
        if risco["stop_loss_maximo"] <= 0:
            raise ValueError("Stop loss máximo deve ser positivo")
        if risco["risco_maximo_dia"] <= 0:
            raise ValueError("Risco máximo por dia deve ser positivo")
        if risco["risco_maximo_operacao"] <= 0:
            raise ValueError("Risco máximo por operação deve ser positivo")
    
    def salvar_configuracao(self):
        """Salva configuração atual no arquivo"""
        try:
            os.makedirs(os.path.dirname(self.arquivo_config), exist_ok=True)
            with open(self.arquivo_config, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
    
    def obter_config_api(self, nome_api: str) -> Optional[ConfiguracaoAPI]:
        """
        Obtém configuração de uma API específica.
        
        Args:
            nome_api: Nome da API
            
        Returns:
            Objeto de configuração da API ou None se não encontrada
        """
        if nome_api in self.config["apis"]:
            api_config = self.config["apis"][nome_api]
            return ConfiguracaoAPI(
                nome=api_config["nome"],
                chave=api_config["chave"],
                tipo=api_config["tipo"],
                parametros=api_config["parametros"]
            )
        return None
    
    def obter_config_backtest(self) -> ConfiguracaoBacktest:
        """
        Obtém configuração de backtest.
        
        Returns:
            Objeto de configuração de backtest
        """
        backtest = self.config["backtest"]
        return ConfiguracaoBacktest(
            periodo_inicial=backtest["periodo_inicial"],
            periodo_final=backtest["periodo_final"],
            capital_inicial=backtest["capital_inicial"],
            timeframes=backtest["timeframes"],
            custos_operacionais=backtest["custos_operacionais"]
        )
    
    def obter_config_risco(self) -> ConfiguracaoGerenciamentoRisco:
        """
        Obtém configuração de gerenciamento de risco.
        
        Returns:
            Objeto de configuração de risco
        """
        risco = self.config["gerenciamento_risco"]
        return ConfiguracaoGerenciamentoRisco(
            stop_loss_maximo=risco["stop_loss_maximo"],
            risco_maximo_dia=risco["risco_maximo_dia"],
            risco_maximo_operacao=risco["risco_maximo_operacao"],
            drawdown_maximo=risco["drawdown_maximo"]
        )
    
    def atualizar_config_api(self, nome_api: str, config: ConfiguracaoAPI):
        """
        Atualiza configuração de uma API.
        
        Args:
            nome_api: Nome da API
            config: Nova configuração
        """
        self.config["apis"][nome_api] = {
            "nome": config.nome,
            "chave": config.chave,
            "tipo": config.tipo,
            "parametros": config.parametros
        }
        self.salvar_configuracao()
    
    def atualizar_config_backtest(self, config: ConfiguracaoBacktest):
        """
        Atualiza configuração de backtest.
        
        Args:
            config: Nova configuração
        """
        self.config["backtest"] = {
            "periodo_inicial": config.periodo_inicial,
            "periodo_final": config.periodo_final,
            "capital_inicial": config.capital_inicial,
            "timeframes": config.timeframes,
            "custos_operacionais": config.custos_operacionais
        }
        self.salvar_configuracao()
    
    def atualizar_config_risco(self, config: ConfiguracaoGerenciamentoRisco):
        """
        Atualiza configuração de gerenciamento de risco.
        
        Args:
            config: Nova configuração
        """
        self.config["gerenciamento_risco"] = {
            "stop_loss_maximo": config.stop_loss_maximo,
            "risco_maximo_dia": config.risco_maximo_dia,
            "risco_maximo_operacao": config.risco_maximo_operacao,
            "drawdown_maximo": config.drawdown_maximo
        }
        self.salvar_configuracao()