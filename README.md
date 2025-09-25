# Sistema de Trading Neural v4.0

Sistema de trading automatizado com múltiplos agentes e análise neural.

## Estrutura do Projeto

```
├── agentes/                    # Implementações dos agentes de trading
├── backteste/                 # Sistema de backtesting
├── carteira/                  # Gerenciamento de carteira
├── configuracao/              # Arquivos de configuração
├── dados/                     # Dados brutos e processados
├── dados_mercado/            # Conectores com fontes de dados
├── gestao_risco/             # Módulos de gestão de risco
├── modelos_ml/               # Modelos de machine learning
├── negociacao/               # Core do sistema de trading
├── notificacoes/             # Sistema de alertas
├── operacoes/                # Registro de operações
├── otimizacao/               # Otimização de estratégias
├── padroes/                  # Detectores de padrões
├── relatorios/               # Geração de relatórios
├── testes/                   # Testes unitários
├── trading_ao_vivo/          # Módulos de trading em tempo real
└── utilitarios/              # Funções auxiliares
```

## Arquivos Principais

- `configurador.py`: Configuração inicial do sistema
- `sistema_trading.py`: Sistema principal de trading
- `gerenciador_banco.py`: Gerenciamento do banco de dados
- `executador.py`: Executor de ordens
- `iniciar.py`: Script de inicialização

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual Python:
   ```bash
   python -m venv .venv
   ```
3. Ative o ambiente virtual:
   - Windows:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```
4. Instale as dependências:
   ```bash
   pip install -r requisitos.txt
   ```

## Uso

1. Configure suas credenciais no arquivo `.env`
2. Execute o configurador:
   ```bash
   python configurador.py
   ```
3. Inicie o sistema:
   ```bash
   python iniciar.py
   ```

## Desenvolvimento

- Use `pytest` para executar os testes
- Siga as convenções de código PEP 8
- Mantenha a documentação atualizada

## Licença

Este projeto está sob a licença MIT.