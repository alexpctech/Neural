@echo off
echo Iniciando Neural Trading System...

REM Verifica se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao encontrado! Por favor, instale o Python 3.8 ou superior.
    pause
    exit /b 1
)

REM Verifica se o Node.js está instalado
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js nao encontrado! Por favor, instale o Node.js LTS.
    pause
    exit /b 1
)

REM Configuração do ambiente Python
echo Configurando ambiente Python...
if not exist "venv" (
    python -m venv venv
)
call .\venv\Scripts\activate

REM Atualiza pip e instala dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Configuração do Frontend
echo Configurando Frontend...
cd frontend

REM Instala dependências do Node se necessário
if not exist "node_modules" (
    echo Instalando dependencias do Frontend...
    npm install
)

REM Inicia os serviços em paralelo
echo Iniciando servicos...
start cmd /c "title Backend && ..\venv\Scripts\python ..\iniciar.py"
start cmd /c "title Frontend && npm start"

echo Sistema iniciado! Acesse http://localhost:3000