#!/usr/bin/env python3
"""
Script de teste para o sistema ETL.
Testa o pipeline sem interface web.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.config import config
from backend.etl_pipeline import create_pipeline
from backend.logger import log_error, log_info, log_success, log_warning


def test_etl_pipeline():
    """Testa o pipeline ETL com um PDF de exemplo."""
    try:
        log_info("=== TESTE DO PIPELINE ETL ===")

        pdf_path = str(config.PROJECT_ROOT / "data_samples" / "extrato_exemplo_caixa.pdf")
        log_info(f"Arquivo PDF de teste: {pdf_path}")

        if not Path(pdf_path).exists():
            log_warning(
                "Arquivo PDF de exemplo nao encontrado. "
                "Adicione data_samples/extrato_exemplo_caixa.pdf para executar o smoke test."
            )
            return False

        pipeline = create_pipeline()
        result = pipeline.run_pipeline(pdf_path)

        if result["success"]:
            log_success("Teste do pipeline concluido com sucesso!")
            log_info("Resultados:")

            if "results" in result:
                results = result["results"]

                if "rules" in results:
                    log_info(f"  Regras carregadas: {results['rules']['count']}")

                if "extraction" in results:
                    ext = results["extraction"]
                    log_info(f"  Extracao - Movimentacoes: {ext['rows']} linhas")

                if "transformation" in results:
                    trans = results["transformation"]
                    log_info(f"  Transformacao - Classificadas: {trans['classified_rows']} registros")
                    log_info(f"  Transformacao - Desconhecidas: {trans['unknown_rows']} registros")

                if "load" in results:
                    load = results["load"]
                    log_info(f"  Carga - Tabela: {load['table_name']}")
                    log_info(f"  Carga - Total de registros: {load['total_records']}")

            log_info(f"Banco de dados: {result['database_path']}")
            return True

        log_error(f"Teste falhou: {result['error']}")
        return False

    except Exception as exc:
        log_error(f"Erro no teste: {str(exc)}")
        return False


if __name__ == "__main__":
    success = test_etl_pipeline()
    sys.exit(0 if success else 1)
