import os
import sys
import platform
import subprocess
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional

# Função para instalar pacotes básicos necessários para o setup
def install_basic_requirements():
    basic_packages = ['psutil', 'gputil']
    for package in basic_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except:
            logging.warning(f"Não foi possível instalar {package}")

# Tenta importar pacotes necessários, instala se não existirem
try:
    import psutil
except ImportError:
    install_basic_requirements()
    try:
        import psutil
    except ImportError:
        psutil = None

try:
    import GPUtil
except ImportError:
    if not 'psutil' in locals():  # Se ainda não tentou instalar os básicos
        install_basic_requirements()
    try:
        import GPUtil
    except ImportError:
        GPUtil = None

class SystemSetup:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent
        self.venv_path = self.root_dir / ".venv"
        self.venv_python = None
        self.venv_pip = None
        self.frontend_path = self.root_dir / "frontend"
        self.config_path = self.root_dir / "configuracao" / "config.json"
        
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def setup_virtual_env(self) -> bool:
        """Configura o ambiente virtual Python."""
        try:
            if not self.venv_path.exists():
                self.logger.info("Criando ambiente virtual...")
                subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)

            # Define o caminho do python e pip do ambiente virtual baseado no SO
            if platform.system() == "Windows":
                self.venv_python = str(self.venv_path / "Scripts" / "python.exe")
                self.venv_pip = str(self.venv_path / "Scripts" / "pip.exe")
                os.environ["PATH"] = str(self.venv_path / "Scripts") + os.pathsep + os.environ["PATH"]
            else:
                self.venv_python = str(self.venv_path / "bin" / "python")
                self.venv_pip = str(self.venv_path / "bin" / "pip")
                os.environ["PATH"] = str(self.venv_path / "bin") + os.pathsep + os.environ["PATH"]
            
            # Atualiza pip no ambiente virtual
            subprocess.run([self.venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)

            self.logger.info("Ambiente virtual configurado com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao configurar ambiente virtual: {str(e)}")
            return False

    def check_dependencies(self) -> List[str]:
        """Verifica quais dependências precisam ser instaladas."""
        try:
            # Lê os requisitos do arquivo
            requirements = self.root_dir / "requirements.txt"
            if not requirements.exists():
                self.logger.error("Arquivo requirements.txt não encontrado")
                return []

            # Lista pacotes instalados
            result = subprocess.run(
                [self.venv_pip, "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )

            # Processa resultado
            import json
            installed = {pkg["name"].lower(): pkg["version"] for pkg in json.loads(result.stdout)}
            
            # Lê requirements.txt
            missing = []
            with open(requirements, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Remove versão para comparação
                        package = line.split(">=")[0].split("==")[0].strip().lower()
                        if package not in installed:
                            missing.append(line)
            
            return missing
        except Exception as e:
            self.logger.error(f"Erro ao verificar dependências: {str(e)}")
            return []

    def install_dependencies(self, packages: List[str]) -> bool:
        """Instala pacotes faltantes."""
        try:
            if packages:
                self.logger.info(f"Instalando {len(packages)} pacotes...")
                
                # Instala pacotes um por um para maior confiabilidade
                for package in packages:
                    try:
                        self.logger.info(f"Instalando {package}...")
                        subprocess.run(
                            [self.venv_python, "-m", "pip", "install", "--no-cache-dir", "--prefer-binary", package],
                            check=True
                        )
                    except subprocess.CalledProcessError as e:
                        self.logger.warning(f"Erro ao instalar {package}: {str(e)}")
                        # Tenta uma segunda vez com --no-deps se falhou
                        try:
                            subprocess.run(
                                [self.venv_python, "-m", "pip", "install", "--no-cache-dir", "--no-deps", "--prefer-binary", package],
                                check=True
                            )
                        except:
                            self.logger.error(f"Falha definitiva ao instalar {package}")
                            continue
                        
            return True
        except Exception as e:
            self.logger.error(f"Erro ao instalar dependências: {str(e)}")
            return False

    def verificar_ambiente(self) -> bool:
        """Verifica os requisitos do sistema."""
        try:
            # Verificar Python
            versao_python = sys.version_info
            if versao_python.major != 3 or versao_python.minor < 8:
                self.logger.error('Python 3.8+ é necessário')
                return False

            # Verificar memória
            try:
                import psutil
                memoria = psutil.virtual_memory()
                if memoria.total < 8 * 1024 * 1024 * 1024:  # 8GB
                    self.logger.warning('Recomendado ter pelo menos 8GB de RAM')
            except ImportError:
                self.logger.warning('Não foi possível verificar a memória')

            # Verificar GPU
            if GPUtil:
                gpus = GPUtil.getGPUs()
                if not gpus:
                    self.logger.warning('Nenhuma GPU detectada - performance pode ser limitada')
                else:
                    for gpu in gpus:
                        self.logger.info(f'GPU detectada: {gpu.name} ({gpu.memoryTotal}MB)')
            else:
                self.logger.warning('Não foi possível verificar GPUs')

            return True
        except Exception as e:
            self.logger.error(f'Erro ao verificar ambiente: {str(e)}')
            return False

    def configurar_frontend(self) -> bool:
        """Configura o frontend React."""
        try:
            if not self.frontend_path.exists():
                self.logger.error('Diretório frontend não encontrado')
                return False

            self.logger.info('Configurando frontend...')
            
            # Verificar Node.js
            try:
                subprocess.check_call(['node', '--version'], stdout=subprocess.DEVNULL)
            except:
                self.logger.error('Node.js não encontrado. Por favor, instale o Node.js')
                return False

            # Instalar dependências
            subprocess.check_call(
                'npm install',
                cwd=str(self.frontend_path),
                shell=True
            )
            
            self.logger.info('Frontend configurado com sucesso')
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f'Erro ao configurar frontend: {str(e)}')
            return False

    def configurar_banco_dados(self) -> bool:
        """Configura o banco de dados."""
        try:
            # Importa o gerenciador de banco de dados
            from gerenciador_banco import GerenciadorBancoDados
            
            db = GerenciadorBancoDados()
            if db.inicializar():
                self.logger.info('Banco de dados configurado com sucesso')
                return True
            
            self.logger.error('Erro ao configurar banco de dados')
            return False
        except Exception as e:
            self.logger.error(f'Erro ao configurar banco de dados: {str(e)}')
            return False

    def configurar_apis(self) -> bool:
        """Configura as APIs necessárias."""
        try:
            config_dir = self.root_dir / 'configuracao'
            config_dir.mkdir(exist_ok=True)
            
            config_api = config_dir / 'api_config.json'
            if not config_api.exists():
                config_padrao = {
                    "apis": {
                        "alpha_vantage": {
                            "ativa": False,
                            "chave": "",
                            "limite_requisicoes": "5 por minuto (plano gratuito)"
                        },
                        "finnhub": {
                            "ativa": False,
                            "chave": "",
                            "limite_requisicoes": "60 por minuto (plano gratuito)"
                        }
                    }
                }
                with open(config_api, 'w', encoding='utf-8') as f:
                    json.dump(config_padrao, f, indent=4)
                
            self.logger.info('Configuração de APIs inicializada')
            return True
        except Exception as e:
            self.logger.error(f'Erro ao configurar APIs: {str(e)}')
            return False

    def setup(self) -> bool:
        """Configura todo o ambiente."""
        try:
            # Cria diretórios necessários
            diretorios = [
                'logs',
                'logs/alertas',
                'logs/performance',
                'logs/trades',
                'dados',
                'dados_mercado',
                'modelos_ml',
                'configuracao',
                'frontend/src',
                'testes'
            ]
            
            for dir_path in diretorios:
                path = self.root_dir / dir_path
                path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f'Diretório criado/verificado: {dir_path}')

            # Lista de tarefas a executar
            tarefas = [
                (self.verificar_ambiente, "Verificação do ambiente"),
                (self.setup_virtual_env, "Configuração do ambiente virtual"),
                (lambda: self.install_dependencies(self.check_dependencies()), "Instalação de dependências Python"),
                (self.configurar_frontend, "Configuração do frontend"),
                (self.configurar_banco_dados, "Configuração do banco de dados"),
                (self.configurar_apis, "Configuração das APIs")
            ]

            for funcao, descricao in tarefas:
                self.logger.info(f'\nExecutando: {descricao}...')
                if not funcao():
                    self.logger.error(f'Falha em: {descricao}')
                    return False
                self.logger.info(f'✓ {descricao} concluída com sucesso')

            self.logger.info("\n✓ Setup concluído com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro durante setup: {str(e)}")
            return False

if __name__ == "__main__":
    setup = SystemSetup()
    if not setup.setup():
        sys.exit(1)