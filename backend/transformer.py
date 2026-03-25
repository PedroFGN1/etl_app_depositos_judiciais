"""
Transformation logic for multi-bank statement movements.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .logger import log_error, log_info, log_success, log_warning


class DataTransformer:
    """Clean, type and classify extracted statement data."""

    OUTPUT_COLUMNS = [
        "Data",
        "Documento",
        "Historico",
        "Valor",
        "Tipo_Valor",
        "Saldo",
        "Tipo_Saldo",
        "Natureza_Operacao",
        "Banco",
        "Pagina",
        "Linha",
    ]

    @staticmethod
    def normalize_text(value: Any) -> str:
        """Normalize text for exact rule matching."""
        return " ".join(str(value).strip().upper().split())

    @staticmethod
    def clean_optional_text(value: Any) -> str | None:
        """Normalize optional text values, preserving nulls."""
        if value is None or pd.isna(value):
            return None

        normalized = str(value).strip()
        return normalized or None

    def clean_monetary_value(self, value: object) -> float | None:
        """Convert a Brazilian monetary string to float."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        raw_value = str(value).strip().replace(".", "").replace(",", ".")
        if not raw_value:
            return None

        return float(raw_value)

    def apply_business_rules(
        self, df: pd.DataFrame, bank_rules: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply cleanup, typing and classification using bank-specific rules."""
        bank_name = bank_rules.get("bank_name", "DESCONHECIDO")
        log_info(f"Iniciando transformacao das movimentacoes do extrato ({bank_name})...")

        if df.empty:
            log_warning("DataFrame de entrada vazio; nenhuma movimentacao para transformar")
            return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

        try:
            transformed_df = df.copy()
            transformed_df.rename(
                columns={
                    "data": "Data",
                    "documento": "Documento",
                    "historico": "Historico",
                    "valor": "Valor",
                    "tipo_valor": "Tipo_Valor",
                    "saldo": "Saldo",
                    "tipo_saldo": "Tipo_Saldo",
                    "banco": "Banco",
                    "pagina": "Pagina",
                    "linha": "Linha",
                },
                inplace=True,
            )

            for column in ["Documento", "Historico", "Tipo_Valor", "Tipo_Saldo", "Banco"]:
                if column not in transformed_df.columns:
                    transformed_df[column] = None

            transformed_df["Historico"] = transformed_df["Historico"].apply(
                self.clean_optional_text
            )
            transformed_df["Documento"] = transformed_df["Documento"].apply(
                self.clean_optional_text
            )
            transformed_df["Tipo_Valor"] = (
                transformed_df["Tipo_Valor"].apply(self.clean_optional_text).str.upper()
            )
            transformed_df["Tipo_Saldo"] = (
                transformed_df["Tipo_Saldo"].apply(self.clean_optional_text).str.upper()
            )
            transformed_df["Banco"] = (
                transformed_df["Banco"].apply(self.clean_optional_text).fillna(bank_name)
            )

            transformed_df["Valor"] = transformed_df["Valor"].apply(self.clean_monetary_value)
            transformed_df["Saldo"] = transformed_df["Saldo"].apply(self.clean_monetary_value)

            transformed_df["Data"] = pd.to_datetime(
                transformed_df["Data"],
                format=bank_rules["formato_data"],
                errors="coerce",
            )
            invalid_dates = int(transformed_df["Data"].isna().sum())
            transformed_df["Data"] = transformed_df["Data"].dt.strftime("%Y-%m-%d")

            normalized_rules = {
                self.normalize_text(key): value
                for key, value in bank_rules.get("rubricas", {}).items()
            }

            unknown_count = 0
            operation_natures = []

            for _, row in transformed_df.iterrows():
                normalized_history = self.normalize_text(row["Historico"])
                operation_nature = normalized_rules.get(normalized_history)

                if operation_nature is None:
                    operation_nature = "Desconhecido"
                    unknown_count += 1
                    log_warning(
                        "Historico sem mapeamento no arquivo de regras: "
                        f"{row['Historico']} (pagina {row['Pagina']}, linha {row['Linha']})"
                    )

                operation_natures.append(operation_nature)

            transformed_df["Natureza_Operacao"] = operation_natures

            if invalid_dates:
                log_warning(f"{invalid_dates} data(s) invalidas foram convertidas para nulo")

            if unknown_count:
                log_warning(f"{unknown_count} movimentacao(oes) classificadas como Desconhecido")

            for column in self.OUTPUT_COLUMNS:
                if column not in transformed_df.columns:
                    transformed_df[column] = None

            transformed_df = transformed_df[self.OUTPUT_COLUMNS]

            log_success(
                f"Transformacao concluida com sucesso: {len(transformed_df)} movimentacao(oes)"
            )
            return transformed_df

        except Exception as exc:
            log_error("Erro durante a transformacao dos dados", str(exc))
            raise


def apply_business_rules(df: pd.DataFrame, bank_rules: Dict[str, Any]) -> pd.DataFrame:
    """Convenience wrapper for direct module usage."""
    transformer = DataTransformer()
    return transformer.apply_business_rules(df, bank_rules)
