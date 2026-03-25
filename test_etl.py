#!/usr/bin/env python3
"""
Unit and smoke tests for the multi-bank ETL flow.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.config import config
from backend.etl_pipeline import create_pipeline
from backend.extractor import BBExtractor, CaixaExtractor, ExtractorFactory
from backend.rules_engine import RulesEngine
from backend.transformer import DataTransformer


class RulesEngineTests(unittest.TestCase):
    def test_loads_multi_bank_rules(self) -> None:
        rules_path = config.OUTPUT_PATH / "test_rules_engine_load.json"
        try:
            with open(rules_path, "w", encoding="utf-8") as file_obj:
                json.dump(RulesEngine.DEFAULT_RULES, file_obj, ensure_ascii=False)

            engine = RulesEngine(rules_path)
            rules = engine.load_rules()

            self.assertIn("CAIXA", rules)
            self.assertIn("BB", rules)
            self.assertEqual(rules["CAIXA"]["bank_name"], "CAIXA")
            self.assertEqual(rules["BB"]["bank_name"], "BB")
        finally:
            if rules_path.exists():
                rules_path.unlink()

    def test_raises_for_unknown_bank(self) -> None:
        rules_path = config.OUTPUT_PATH / "test_rules_engine_unknown.json"
        try:
            with open(rules_path, "w", encoding="utf-8") as file_obj:
                json.dump(RulesEngine.DEFAULT_RULES, file_obj, ensure_ascii=False)

            engine = RulesEngine(rules_path)

            with self.assertRaises(ValueError):
                engine.get_bank_rules("ITAU")
        finally:
            if rules_path.exists():
                rules_path.unlink()


class ExtractorFactoryTests(unittest.TestCase):
    def test_factory_returns_caixa_extractor(self) -> None:
        bank_rules = copy.deepcopy(RulesEngine.DEFAULT_RULES["CAIXA"])
        bank_rules["bank_name"] = "CAIXA"

        extractor = ExtractorFactory.create("CAIXA", bank_rules)

        self.assertIsInstance(extractor, CaixaExtractor)

    def test_factory_returns_bb_extractor(self) -> None:
        bank_rules = copy.deepcopy(RulesEngine.DEFAULT_RULES["BB"])
        bank_rules["bank_name"] = "BB"

        extractor = ExtractorFactory.create("BB", bank_rules)

        self.assertIsInstance(extractor, BBExtractor)


class BBExtractorTests(unittest.TestCase):
    def test_bb_extractor_builds_full_dates_and_rolls_year(self) -> None:
        bank_rules = copy.deepcopy(RulesEngine.DEFAULT_RULES["BB"])
        bank_rules["bank_name"] = "BB"
        extractor = BBExtractor("BB", bank_rules)

        extracted_df = extractor.extract_from_lines(
            [
                (1, 1, "Saldo em 31.12.2025"),
                (1, 2, "31.12 100 ANOTACAO DE RESGATE EM FUNDO GARANT 1.234,56 C"),
                (1, 3, "01.01 101 ATUALIZACAO DE REC APLICADOS 10,00 C"),
            ]
        )

        self.assertEqual(len(extracted_df), 2)
        self.assertEqual(extracted_df.iloc[0]["data"], "31.12.2025")
        self.assertEqual(extracted_df.iloc[1]["data"], "01.01.2026")
        self.assertEqual(extracted_df.iloc[0]["documento"], "100")
        self.assertEqual(extracted_df.iloc[1]["documento"], "101")


class TransformerTests(unittest.TestCase):
    def test_transformer_applies_bb_rules_and_preserves_shared_schema(self) -> None:
        transformer = DataTransformer()
        bank_rules = copy.deepcopy(RulesEngine.DEFAULT_RULES["BB"])
        bank_rules["bank_name"] = "BB"

        raw_df = pd.DataFrame(
            [
                {
                    "data": "01.01.2026",
                    "documento": None,
                    "historico": "ATUALIZACAO DE REC APLICADOS",
                    "valor": "10,00",
                    "tipo_valor": "C",
                    "saldo": None,
                    "tipo_saldo": None,
                    "banco": "BB",
                    "pagina": 1,
                    "linha": 3,
                }
            ]
        )

        transformed_df = transformer.apply_business_rules(raw_df, bank_rules)
        row = transformed_df.iloc[0]

        self.assertEqual(row["Data"], "2026-01-01")
        self.assertEqual(row["Natureza_Operacao"], "Rendimento")
        self.assertEqual(row["Banco"], "BB")
        self.assertTrue(pd.isna(row["Saldo"]))
        self.assertIsNone(row["Documento"])


class PipelineTests(unittest.TestCase):
    def test_caixa_smoke_pipeline(self) -> None:
        pdf_path = config.DATA_SAMPLES_PATH / "extrato_exemplo_caixa.pdf"
        if not pdf_path.exists():
            self.skipTest("Arquivo PDF de exemplo da CAIXA nao encontrado")

        pipeline = create_pipeline()
        table_name = pipeline.get_table_name("CAIXA")
        pipeline.loader.drop_table(table_name)

        result = pipeline.run_pipeline(str(pdf_path), "CAIXA")

        self.assertTrue(result["success"], msg=result.get("error"))
        self.assertEqual(result["bank_name"], "CAIXA")
        self.assertEqual(result["table_name"], table_name)
        self.assertGreater(result["results"]["extraction"]["rows"], 0)

        table_info = pipeline.loader.get_table_info(table_name)
        self.assertTrue(table_info["exists"])
        self.assertGreater(table_info["row_count"], 0)

    def test_pipeline_fails_when_layout_does_not_match_selected_bank(self) -> None:
        pdf_path = config.DATA_SAMPLES_PATH / "extrato_exemplo_caixa.pdf"
        if not pdf_path.exists():
            self.skipTest("Arquivo PDF de exemplo da CAIXA nao encontrado")

        pipeline = create_pipeline()
        result = pipeline.run_pipeline(str(pdf_path), "BB")

        self.assertFalse(result["success"])
        self.assertIn("layout esperado para o banco BB", result["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
