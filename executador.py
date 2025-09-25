from typing import Dict
from datetime import datetime
from database_manager import DatabaseManager
from agentes.agente_tecnico_v4 import AgenteTecnicoV4
from agentes.agente_fundamentalista_v4 import AgenteFundamentalistaV4


class ExecutorV4:
    def __init__(self):
        self.db = DatabaseManager()
        self.trades_executados = []
        self.posicoes_abertas = {}
        self.capital = 100000.0
        self.pnl_total = 0.0
        self.agente_tecnico = AgenteTecnicoV4()
        self.agente_fundamentalista = AgenteFundamentalistaV4()

    def executar_trade_simulado(self, sinal: Dict) -> Dict:
        trade = {
            'timestamp': datetime.now().isoformat(),
            'ativo': sinal.get('ativo'),
            'tipo': sinal.get('action'),
            'preco_entrada': sinal.get('preco_entrada')
        }
        trade_id = self.db.salvar_trade(trade)
        self.trades_executados.append(trade)
        # registrar posicao simulada
        self.posicoes_abertas[trade['ativo']] = {**trade, 'quantidade': 1, 'valor': trade.get('preco_entrada', 0) * 1}
        return {'status': 'EXECUTADO', 'trade_id': trade_id}

    def fechar_posicao(self, ativo: str, preco_saida: float, motivo: str = 'MANUAL') -> dict:
        if ativo not in self.posicoes_abertas:
            return {}
        pos = self.posicoes_abertas.pop(ativo)
        quantidade = pos.get('quantidade', 1)
        valor_saida = preco_saida * quantidade
        pnl = valor_saida - pos.get('valor', 0)
        self.pnl_total += pnl
        return {'ativo': ativo, 'pnl': pnl, 'motivo': motivo}

    def obter_resumo(self) -> dict:
        return {'capital': self.capital, 'pnl_total': self.pnl_total, 'trades': len(self.trades_executados)}

    def analisar_mercado(self, simbolos: list) -> dict:
        # usa os agentes para gerar analises básicas
        dados_fake = {s: {'current_price': 100.0} for s in simbolos}
        tecnico = self.agente_tecnico.analisar_indicadores_completos(dados_fake)
        fundamental = self.agente_fundamentalista.analisar_fundamentos_completos(simbolos)
        return {'tecnico': tecnico, 'fundamental': fundamental}
