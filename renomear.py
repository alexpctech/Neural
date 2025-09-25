import os
from pathlib import Path

# Mapeamento de nomes em inglês para português
mapeamento = {
    'market_data': 'dados_mercado',
    'database_manager.py': 'gerenciador_banco.py',
    'executor.py': 'executador.py',
    'live_trading': 'trading_ao_vivo',
    'patterns': 'padroes',
    'portfolio': 'carteira',
    'requirements.txt': 'requisitos.txt',
    'risk_management': 'gestao_risco',
    'run.py': 'iniciar.py',
    'tests': 'testes',
    'trades': 'operacoes',
    'trading': 'negociacao',
    'trading_system_v4_complete_full_fixed.py': 'sistema_trading.py',
    'utils': 'utilitarios',
    'backtest': 'backteste',
    'config': 'configuracao',
    'ml_models': 'modelos_ml',
    'notifications': 'notificacoes',
    'optimization': 'otimizacao',
    'configurator_v4_fixed.py': 'configurador.py'
}

def renomear_arquivos_e_pastas():
    """Renomeia arquivos e pastas do projeto para português."""
    diretorio_base = Path(__file__).parent
    
    print("Iniciando renomeação de arquivos e pastas...")
    
    # Primeiro renomeia os arquivos
    for arquivo_antigo, arquivo_novo in mapeamento.items():
        caminho_antigo = diretorio_base / arquivo_antigo
        caminho_novo = diretorio_base / arquivo_novo
        
        if caminho_antigo.exists():
            try:
                caminho_antigo.rename(caminho_novo)
                print(f"Renomeado: {arquivo_antigo} -> {arquivo_novo}")
            except Exception as e:
                print(f"Erro ao renomear {arquivo_antigo}: {str(e)}")

    print("\nRenomeação concluída!")

if __name__ == "__main__":
    renomear_arquivos_e_pastas()