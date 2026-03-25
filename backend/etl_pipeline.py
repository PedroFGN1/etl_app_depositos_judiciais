"""
Main ETL pipeline for bank statement PDFs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import traceback

import pandas as pd

from .config import config
from .extractor import BaseExtractor, ExtractorFactory
from .loader import data_loader
from .logger import etl_logger, log_critical, log_error, log_info, log_success
from .rules_engine import RulesEngine
from .transformer import DataTransformer


class ETLPipeline:
    """Orchestrate the ETL flow for a selected bank statement."""

    TABLE_PREFIX = "Movimentacoes_"

    def __init__(self) -> None:
        self.config = config
        self.rules_engine = RulesEngine()
        self.transformer = DataTransformer()
        self.loader = data_loader
        self.logger = etl_logger

        self.current_step = None
        self.progress = 0
        self.total_steps = 5
        self.results: Dict[str, Any] = {}

    def update_progress(self, step: str, progress: int) -> None:
        """Update pipeline progress for logs and frontend."""
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

    def get_table_name(self, bank_name: str) -> str:
        """Return the destination table name for a bank."""
        normalized_bank_name = RulesEngine.normalize_bank_name(bank_name)
        return f"{self.TABLE_PREFIX}{normalized_bank_name}"

    def create_extractor(self, bank_name: str, bank_rules: Dict[str, Any]) -> BaseExtractor:
        """Instantiate the bank-specific extractor."""
        return ExtractorFactory.create(bank_name, bank_rules)

    def validate_input_file(self, pdf_path: str, extractor: BaseExtractor) -> bool:
        """Validate the input PDF."""
        try:
            log_info("Validando arquivo PDF de entrada...")
            pdf_file = Path(pdf_path)
            is_valid = extractor.validate_file(pdf_file)
            if is_valid:
                log_success("Validacao do arquivo concluida com sucesso")
            return is_valid
        except Exception as exc:
            log_error("Erro na validacao do arquivo", str(exc))
            return False

    def extract_phase(self, pdf_path: str, extractor: BaseExtractor) -> pd.DataFrame:
        """Extract raw movements from the PDF."""
        self.update_progress("Extraindo movimentacoes do PDF", 2)
        extracted_df = extractor.extract_file(Path(pdf_path))
        self.results["extraction"] = {
            "input_file": Path(pdf_path).name,
            "bank_name": extractor.bank_name,
            "rows": len(extracted_df),
            "columns": len(extracted_df.columns),
        }
        return extracted_df

    def transform_phase(
        self, extracted_df: pd.DataFrame, bank_rules: Dict[str, Any]
    ) -> pd.DataFrame:
        """Transform raw movements into the shared schema."""
        self.update_progress("Aplicando regras de negocio", 3)
        transformed_df = self.transformer.apply_business_rules(extracted_df, bank_rules)
        self.results["transformation"] = {
            "bank_name": bank_rules["bank_name"],
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

    def load_phase(self, transformed_df: pd.DataFrame, table_name: str) -> bool:
        """Load the transformed data to the target database."""
        self.update_progress("Carregando movimentacoes no banco", 4)

        if not self.loader.test_connection():
            log_error("Falha na conexao com banco de dados")
            return False

        load_results = self.loader.load_multiple_dataframes({table_name: transformed_df})
        success = load_results.get(table_name, False)
        if not success:
            return False

        stats = self.loader.get_database_stats()
        self.results["load"] = {
            "tables_loaded": 1,
            "table_name": table_name,
            "total_records": stats.get("tables", {}).get(table_name, {}).get("rows", 0),
            "database_stats": stats,
        }
        return True

    def run_pipeline(self, pdf_path: str, bank_name: str) -> Dict[str, Any]:
        """Execute the ETL pipeline for a selected bank and PDF."""
        normalized_bank_name = RulesEngine.normalize_bank_name(bank_name)

        try:
            self.logger.clear_logs()
            self.results = {}
            log_info(
                f"=== INICIANDO PIPELINE ETL DO EXTRATO ({normalized_bank_name}) ==="
            )

            self.update_progress("Carregando regras dinamicas", 1)
            bank_rules = self.rules_engine.get_bank_rules(normalized_bank_name)
            extractor = self.create_extractor(normalized_bank_name, bank_rules)

            if not self.validate_input_file(pdf_path, extractor):
                return {"success": False, "error": "Validacao do arquivo falhou"}

            self.results["rules"] = {
                "bank_name": normalized_bank_name,
                "count": len(bank_rules.get("rubricas", {})),
            }

            extracted_df = self.extract_phase(pdf_path, extractor)
            transformed_df = self.transform_phase(extracted_df, bank_rules)

            table_name = self.get_table_name(normalized_bank_name)
            load_success = self.load_phase(transformed_df, table_name)
            if not load_success:
                return {"success": False, "error": "Falha na carga dos dados"}

            self.update_progress("Pipeline concluido", 5)
            log_success("=== PIPELINE ETL CONCLUIDO COM SUCESSO ===")

            return {
                "success": True,
                "bank_name": normalized_bank_name,
                "table_name": table_name,
                "database_path": self.config.get_database_engine_url(),
                "results": self.results,
                "logs": self.logger.get_logs(),
            }

        except Exception as exc:
            error_msg = f"Erro no pipeline ETL: {str(exc)}"
            log_critical(error_msg, traceback.format_exc())
            return {
                "success": False,
                "bank_name": normalized_bank_name,
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "logs": self.logger.get_logs(),
            }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Return current pipeline status."""
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
        """Reset current pipeline state."""
        self.current_step = None
        self.progress = 0
        self.results = {}
        self.logger.clear_logs()
        log_info("Pipeline resetado")


def create_pipeline() -> ETLPipeline:
    """Create a new isolated pipeline instance."""
    return ETLPipeline()


def main(pdf_path: str | None = None, bank_name: str = "CAIXA") -> Dict[str, Any]:
    """CLI-friendly entrypoint using the multi-bank contract."""
    pipeline = create_pipeline()

    if not pdf_path:
        pdf_path = str(config.DATA_SAMPLES_PATH / "extrato_exemplo_caixa.pdf")

    result = pipeline.run_pipeline(pdf_path, bank_name)

    if result["success"]:
        print("Pipeline concluido com sucesso!")
        print(f"Banco: {result['bank_name']}")
        print(f"Tabela: {result['table_name']}")
        print(f"Banco de dados: {result['database_path']}")
    else:
        print(f"Pipeline falhou: {result['error']}")

    return result


if __name__ == "__main__":
    main()
