#!/usr/bin/env python3
"""
Aplicacao ETL - Arquivo Principal
Sistema de processamento ETL com interface web usando Eel.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.config import config
from backend.eel_interface import start_eel_app
from backend.logger import log_error, log_info


def check_dependencies():
    """Verifica se todas as dependencias necessarias estao instaladas."""
    required_packages = ["eel", "pandas", "sqlalchemy", "pdfplumber"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        log_error(f"Pacotes nao encontrados: {', '.join(missing_packages)}")
        log_info("Instale os pacotes com: pip install " + " ".join(missing_packages))
        return False

    return True


def setup_directories():
    """Cria os diretorios necessarios."""
    try:
        directories = [config.OUTPUT_PATH, config.UPLOAD_FOLDER, config.DATA_SAMPLES_PATH]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            log_info(f"Diretorio verificado: {directory}")
        return True
    except Exception as exc:
        log_error(f"Erro ao criar diretorios: {str(exc)}")
        return False


def create_sample_files():
    """Verifica a existencia de um PDF de exemplo."""
    try:
        sample_pdf = config.DATA_SAMPLES_PATH / "extrato_exemplo_caixa.pdf"
        if sample_pdf.exists():
            log_info(f"Arquivo de exemplo encontrado: {sample_pdf}")
        else:
            log_info(
                "Nenhum PDF de exemplo encontrado em data_samples. "
                "Use um PDF real do usuario na interface."
            )
        return True
    except Exception as exc:
        log_error(f"Erro ao verificar arquivos de exemplo: {str(exc)}")
        return False


def main():
    """Funcao principal da aplicacao."""
    try:
        print("=" * 60)
        print("    SISTEMA ETL - PROCESSAMENTO DE EXTRATOS PDF")
        print("=" * 60)
        print()

        log_info("Iniciando sistema ETL...")

        log_info("Verificando dependencias...")
        if not check_dependencies():
            log_error("Falha na verificacao de dependencias")
            return 1

        log_info("Configurando diretorios...")
        if not setup_directories():
            log_error("Falha na configuracao de diretorios")
            return 1

        log_info("Verificando arquivos de exemplo...")
        create_sample_files()

        log_info("Configuracoes do sistema:")
        log_info(f"  - Tipo de banco: {config.database.db_type}")
        log_info(f"  - Diretorio de uploads: {config.UPLOAD_FOLDER}")
        log_info(f"  - Diretorio de saida: {config.OUTPUT_PATH}")
        log_info(f"  - Host: {config.EEL_HOST}:{config.EEL_PORT}")

        print()
        print("Instrucoes de uso:")
        print("1. Acesse a interface web no navegador")
        print("2. Faca upload do PDF do extrato bancario")
        print("3. Selecione o banco do extrato (CAIXA ou BB)")
        print("4. Clique em 'Iniciar Processamento ETL'")
        print("5. Acompanhe o progresso no terminal de logs")
        print()
        print("Arquivos de exemplo disponiveis em:")
        print(f"  - {config.DATA_SAMPLES_PATH}")
        print()

        start_eel_app()
        return 0

    except KeyboardInterrupt:
        log_info("Aplicacao interrompida pelo usuario")
        return 0
    except Exception as exc:
        log_error(f"Erro fatal na aplicacao: {str(exc)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
