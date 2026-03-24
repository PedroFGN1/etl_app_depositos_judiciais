"""
Modulo de Transformacao (Transform)
Funcoes para limpeza, padronizacao e classificacao das movimentacoes extraidas.
"""

from __future__ import annotations

from typing import Dict

import pandas as pd

from .logger import log_error, log_info, log_success, log_warning


class DataTransformer:
    """Classe responsavel pelas transformacoes do extrato bancario."""

    @staticmethod
    def normalize_text(value: str) -> str:
        """Normaliza historicos para comparacao exata com o dicionario de regras."""
        return " ".join(str(value).strip().upper().split())

    def clean_monetary_value(self, value: object) -> float:
        """Converte uma string monetaria brasileira para float."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        raw_value = str(value).strip().replace(".", "").replace(",", ".")
        if not raw_value:
            return None

        return float(raw_value)

    def apply_business_rules(
        self, df: pd.DataFrame, rules_dict: Dict[str, str]
    ) -> pd.DataFrame:
        """Aplica limpeza, tipagem e classificacao dinamica das movimentacoes."""
        log_info("Iniciando transformacao das movimentacoes do extrato...")

        if df.empty:
            log_warning("DataFrame de entrada vazio; nenhuma movimentacao para transformar")
            return pd.DataFrame(
                columns=[
                    "Data",
                    "Documento",
                    "Historico",
                    "Valor",
                    "Tipo_Valor",
                    "Saldo",
                    "Tipo_Saldo",
                    "Natureza_Operacao",
                    "Pagina",
                    "Linha",
                ]
            )

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
                    "pagina": "Pagina",
                    "linha": "Linha",
                },
                inplace=True,
            )

            transformed_df["Historico"] = transformed_df["Historico"].astype(str).str.strip()
            transformed_df["Documento"] = transformed_df["Documento"].astype(str).str.strip()
            transformed_df["Tipo_Valor"] = (
                transformed_df["Tipo_Valor"].astype(str).str.strip().str.upper()
            )
            transformed_df["Tipo_Saldo"] = (
                transformed_df["Tipo_Saldo"].astype(str).str.strip().str.upper()
            )

            transformed_df["Valor"] = transformed_df["Valor"].apply(self.clean_monetary_value)
            transformed_df["Saldo"] = transformed_df["Saldo"].apply(self.clean_monetary_value)

            transformed_df["Data"] = pd.to_datetime(
                transformed_df["Data"], format="%d/%m/%Y", errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            normalized_rules = {
                self.normalize_text(key): value for key, value in rules_dict.items()
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

            invalid_dates = transformed_df["Data"].isna().sum()
            if invalid_dates:
                log_warning(f"{invalid_dates} data(s) invalidas foram convertidas para nulo")

            if unknown_count:
                log_warning(f"{unknown_count} movimentacao(oes) classificadas como Desconhecido")

            ordered_columns = [
                "Data",
                "Documento",
                "Historico",
                "Valor",
                "Tipo_Valor",
                "Saldo",
                "Tipo_Saldo",
                "Natureza_Operacao",
                "Pagina",
                "Linha",
            ]
            transformed_df = transformed_df[ordered_columns]

            log_success(
                f"Transformacao concluida com sucesso: {len(transformed_df)} movimentacao(oes)"
            )
            return transformed_df

        except Exception as exc:
            log_error("Erro durante a transformacao dos dados", str(exc))
            raise


def apply_business_rules(df: pd.DataFrame, rules_dict: Dict[str, str]) -> pd.DataFrame:
    """Funcao de conveniencia para manter uso direto do modulo."""
    transformer = DataTransformer()
    return transformer.apply_business_rules(df, rules_dict)
