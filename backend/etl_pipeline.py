"""
Modulo Principal do Pipeline ETL
Orquestra a execucao do pipeline ETL completo para extrato PDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import traceback

import pandas as pd

from .config import config
from .extractor import DataExtractor
from .loader import data_loader
from .logger import etl_logger, log_critical, log_error, log_info, log_success
from .rules_engine import RulesEngine
from .transformer import DataTransformer


class ETLPipeline:
    """Classe principal que orquestra o pipeline ETL do extrato PDF."""

    TABLE_NAME = "Movimentacoes_Extrato"

    def __init__(self) -> None:
        self.config = config
        self.extractor = DataExtractor()
        self.rules_engine = RulesEngine()
        self.transformer = DataTransformer()
        self.loader = data_loader
        self.logger = etl_logger

        self.current_step = None
        self.progress = 0
        self.total_steps = 5
        self.results: Dict[str, Any] = {}

    def update_progress(self, step: str, progress: int) -> None:
        """Atualiza o progresso do pipeline."""
        self.current_step = step
        self.progress = progress
        log_info(f"Progresso: {progress}/{self.total_steps} - {step}")
        try:
            import eel

            eel.update_progress_callback(
                step, round((progress / self.total_steps) * 100, 1)
            )
        except Exception:
            pass

    def validate_input_file(self, pdf_path: str) -> bool:
        """Valida o arquivo de entrada do extrato."""
        try:
            log_info("Validando arquivo PDF de entrada...")
            pdf_file = Path(pdf_path)
            is_valid = self.extractor.validate_file(pdf_file)
            if is_valid:
                log_success("Validacao do arquivo concluida com sucesso")
            return is_valid
        except Exception as exc:
            log_error("Erro na validacao do arquivo", str(exc))
            return False

    def extract_phase(self, pdf_path: str) -> pd.DataFrame:
        """Fase de extracao dos dados."""
        self.update_progress("Extraindo movimentacoes do PDF", 2)
        extracted_df = self.extractor.extract_file(Path(pdf_path))
        self.results["extraction"] = {
            "input_file": Path(pdf_path).name,
            "rows": len(extracted_df),
            "columns": len(extracted_df.columns),
        }
        return extracted_df

    def transform_phase(
        self, extracted_df: pd.DataFrame, rules_dict: Dict[str, str]
    ) -> pd.DataFrame:
        """Fase de transformacao dos dados."""
        self.update_progress("Aplicando regras de negocio", 3)
        transformed_df = self.transformer.apply_business_rules(extracted_df, rules_dict)
        self.results["transformation"] = {
            "rows": len(transformed_df),
            "classified_rows": int(
                (transformed_df["Natureza_Operacao"] != "Desconhecido").sum()
            )
            if not transformed_df.empty
            else 0,
            "unknown_rows": int(
                (transformed_df["Natureza_Operacao"] == "Desconhecido").sum()
            )
            if not transformed_df.empty
            else 0,
        }
        return transformed_df

    def load_phase(self, transformed_df: pd.DataFrame) -> bool:
        """Fase de carga dos dados."""
        self.update_progress("Carregando movimentacoes no banco", 4)

        if not self.loader.test_connection():
            log_error("Falha na conexao com banco de dados")
            return False

        load_results = self.loader.load_multiple_dataframes(
            {self.TABLE_NAME: transformed_df}
        )
        success = load_results.get(self.TABLE_NAME, False)
        if not success:
            return False

        stats = self.loader.get_database_stats()
        self.results["load"] = {
            "tables_loaded": 1,
            "table_name": self.TABLE_NAME,
            "total_records": stats.get("tables", {})
            .get(self.TABLE_NAME, {})
            .get("rows", 0),
            "database_stats": stats,
        }
        return True

    def run_pipeline(self, pdf_path: str) -> Dict[str, Any]:
        """Executa o pipeline ETL completo."""
        try:
            self.logger.clear_logs()
            self.results = {}
            log_info("=== INICIANDO PIPELINE ETL DO EXTRATO ===")

            if not self.validate_input_file(pdf_path):
                return {"success": False, "error": "Validacao do arquivo falhou"}

            self.update_progress("Carregando regras dinamicas", 1)
            rules_dict = self.rules_engine.load_rules()
            self.results["rules"] = {"count": len(rules_dict)}

            extracted_df = self.extract_phase(pdf_path)
            transformed_df = self.transform_phase(extracted_df, rules_dict)

            load_success = self.load_phase(transformed_df)
            if not load_success:
                return {"success": False, "error": "Falha na carga dos dados"}

            self.update_progress("Pipeline concluido", 5)
            log_success("=== PIPELINE ETL CONCLUIDO COM SUCESSO ===")

            return {
                "success": True,
                "database_path": self.config.get_database_engine_url(),
                "results": self.results,
                "logs": self.logger.get_logs(),
            }

        except Exception as exc:
            error_msg = f"Erro no pipeline ETL: {str(exc)}"
            log_critical(error_msg, traceback.format_exc())
            return {
                "success": False,
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "logs": self.logger.get_logs(),
            }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Retorna o status atual do pipeline."""
        return {
            "current_step": self.current_step,
            "progress": self.progress,
            "total_steps": self.total_steps,
            "progress_percentage": round((self.progress / self.total_steps) * 100, 1)
            if self.total_steps
            else 0,
            "results": self.results,
        }

    def reset_pipeline(self) -> None:
        """Reseta o estado do pipeline atual."""
        self.current_step = None
        self.progress = 0
        self.results = {}
        self.logger.clear_logs()
        log_info("Pipeline resetado")


def create_pipeline() -> ETLPipeline:
    """Cria uma nova instancia do pipeline para uma execucao isolada."""
    return ETLPipeline()


def main(pdf_path: str | None = None) -> Dict[str, Any]:
    """Funcao principal adaptada ao novo contrato com um unico PDF."""
    pipeline = create_pipeline()

    if not pdf_path:
        pdf_path = str(config.DATA_SAMPLES_PATH / "extrato_exemplo_caixa.pdf")

    result = pipeline.run_pipeline(pdf_path)

    if result["success"]:
        print("Pipeline concluido com sucesso!")
        print(f"Banco de dados: {result['database_path']}")
    else:
        print(f"Pipeline falhou: {result['error']}")

    return result


if __name__ == "__main__":
    main()
