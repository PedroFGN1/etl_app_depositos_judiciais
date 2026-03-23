#!/usr/bin/env python3
"""
Aplicação ETL - Arquivo Principal
Sistema de processamento ETL com interface web usando Eel.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Imports do projeto
from backend.config import config
from backend.logger import log_info, log_error, log_success
from backend.eel_interface import start_eel_app


def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    required_packages = [
        'eel',
        'pandas', 
        'sqlalchemy',
        'openpyxl'  # Para suporte a Excel
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        log_error(f"Pacotes não encontrados: {', '.join(missing_packages)}")
        log_info("Instale os pacotes com: pip install " + " ".join(missing_packages))
        return False
    
    return True


def setup_directories():
    """Cria os diretórios necessários"""
    try:
        directories = [
            config.OUTPUT_PATH,
            config.UPLOAD_FOLDER,
            config.DATA_SAMPLES_PATH
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            log_info(f"Diretório verificado: {directory}")
        
        return True
        
    except Exception as e:
        log_error(f"Erro ao criar diretórios: {str(e)}")
        return False


def create_sample_files():
    """Cria arquivos de exemplo se não existirem"""
    try:
        sample_saldos = config.DATA_SAMPLES_PATH / "exemplo_saldos.csv"
        sample_resgates = config.DATA_SAMPLES_PATH / "exemplo_resgates.csv"
        
        if not sample_saldos.exists():
            sample_saldos_content = """Conta Judicial;Parcela;Saldo JANEIRO23;Saldo FEVEREIRO23;Saldo MARÇO23
12345;1;R$ 1.000,50;R$ 1.100,75;R$ 1.200,00
12346;1;R$ 2.500,00;R$ 2.600,25;R$ 2.700,50
12347;2;R$ 500,75;R$ 550,80;R$ 600,90"""
            
            with open(sample_saldos, 'w', encoding='utf-8') as f:
                f.write(sample_saldos_content)
            
            log_info(f"Arquivo de exemplo criado: {sample_saldos}")
        
        if not sample_resgates.exists():
            sample_resgates_content = """Número da Conta Judicial;Número da Parcela;Número do Convênio de Repasse;DT_RSGT_DEP_JDCL;Competencia;Saldo Conta;Valor total resgatado
12345;1;CONV001;2023-01-15;15/01/2023;R$ 1.000,50;R$ 100,00
12346;1;CONV002;2023-02-20;20/02/2023;R$ 2.500,00;R$ 250,00
12347;2;CONV003;2023-03-10;10/03/2023;R$ 500,75;R$ 50,00"""
            
            with open(sample_resgates, 'w', encoding='utf-8') as f:
                f.write(sample_resgates_content)
            
            log_info(f"Arquivo de exemplo criado: {sample_resgates}")
        
        return True
        
    except Exception as e:
        log_error(f"Erro ao criar arquivos de exemplo: {str(e)}")
        return False


def main():
    """Função principal da aplicação"""
    try:
        print("=" * 60)
        print("    SISTEMA ETL - PROCESSAMENTO DE DADOS JUDICIAIS")
        print("=" * 60)
        print()
        
        log_info("Iniciando sistema ETL...")
        
        # Verificar dependências
        log_info("Verificando dependências...")
        if not check_dependencies():
            log_error("Falha na verificação de dependências")
            return 1
        
        # Configurar diretórios
        log_info("Configurando diretórios...")
        if not setup_directories():
            log_error("Falha na configuração de diretórios")
            return 1
        
        # Criar arquivos de exemplo
        log_info("Verificando arquivos de exemplo...")
        create_sample_files()
        
        # Exibir informações de configuração
        log_info("Configurações do sistema:")
        log_info(f"  - Tipo de banco: {config.database.db_type}")
        log_info(f"  - Diretório de uploads: {config.UPLOAD_FOLDER}")
        log_info(f"  - Diretório de saída: {config.OUTPUT_PATH}")
        log_info(f"  - Host: {config.EEL_HOST}:{config.EEL_PORT}")
        
        print()
        print("Instruções de uso:")
        print("1. Acesse a interface web no navegador")
        print("2. Faça upload dos arquivos de saldos e resgates")
        print("3. Clique em 'Iniciar Processamento ETL'")
        print("4. Acompanhe o progresso no terminal de logs")
        print()
        print("Arquivos de exemplo disponíveis em:")
        print(f"  - {config.DATA_SAMPLES_PATH}")
        print()
        
        # Iniciar aplicação Eel
        start_eel_app()
        
        return 0
        
    except KeyboardInterrupt:
        log_info("Aplicação interrompida pelo usuário")
        return 0
    except Exception as e:
        log_error(f"Erro fatal na aplicação: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
