#!/usr/bin/env python3
"""
Script de teste para o sistema ETL
Testa o pipeline sem interface web
"""

import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.etl_pipeline import etl_pipeline
from backend.config import config
from backend.logger import log_info, log_success, log_error


def test_etl_pipeline():
    """Testa o pipeline ETL com arquivos de exemplo"""
    try:
        log_info("=== TESTE DO PIPELINE ETL ===")
        
        # Caminhos dos arquivos de teste
        saldos_path = str(config.PROJECT_ROOT / "data_samples" / "base_operacional.csv")
        resgates_path = str(config.PROJECT_ROOT / "data_samples" / "base_resgates.csv")
        
        log_info(f"Arquivo de saldos: {saldos_path}")
        log_info(f"Arquivo de resgates: {resgates_path}")
        
        # Verificar se os arquivos existem
        if not Path(saldos_path).exists():
            log_error(f"Arquivo não encontrado: {saldos_path}")
            return False
            
        if not Path(resgates_path).exists():
            log_error(f"Arquivo não encontrado: {resgates_path}")
            return False
        
        # Executar pipeline
        result = etl_pipeline.run_pipeline(saldos_path, resgates_path)
        
        if result["success"]:
            log_success("Teste do pipeline concluído com sucesso!")
            log_info("Resultados:")
            
            if "results" in result:
                results = result["results"]
                
                if "extraction" in results:
                    ext = results["extraction"]
                    log_info(f"  Extração - Saldos: {ext['saldos_rows']} linhas")
                    log_info(f"  Extração - Resgates: {ext['resgates_rows']} linhas")
                
                if "transformation" in results:
                    trans = results["transformation"]
                    log_info(f"  Transformação - Contas: {trans['dim_contas_rows']} registros")
                    log_info(f"  Transformação - Saldos: {trans['fact_saldos_rows']} registros")
                    log_info(f"  Transformação - Resgates: {trans['fact_resgates_rows']} registros")
                
                if "load" in results:
                    load = results["load"]
                    log_info(f"  Carga - Total de registros: {load['total_records']}")
            
            log_info(f"Banco de dados: {result['database_path']}")
            return True
        else:
            log_error(f"Teste falhou: {result['error']}")
            return False
            
    except Exception as e:
        log_error(f"Erro no teste: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_etl_pipeline()
    sys.exit(0 if success else 1)

