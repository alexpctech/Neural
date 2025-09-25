import os
from executor import ExecutorV4


def test_executar_trade_simulado():
    exe = ExecutorV4()
    sinal = {'ativo': 'TESTE1', 'action': 'COMPRAR', 'preco_entrada': 10.0}
    res = exe.executar_trade_simulado(sinal)
    assert res['status'] == 'EXECUTADO'


def test_salvar_trade_db():
    exe = ExecutorV4()
    trades = exe.db.obter_trades()
    assert isinstance(trades, list)
