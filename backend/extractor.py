"""
Modulo de Extracao (Extract)
Funcoes responsaveis por ler dados de extratos bancarios em PDF.
"""

from pathlib import Path
from typing import Any, Dict, List
import re

import pandas as pd

from .logger import log_error, log_info, log_success, log_warning

try:
    import pdfplumber
except ImportError:  # pragma: no cover - dependente do ambiente
    pdfplumber = None


class DataExtractor:
    """Classe responsavel pela extracao de dados de extratos PDF."""

    LINE_PATTERN = re.compile(
        r"^(?P<data>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<documento>\S+)\s+"
        r"(?P<historico>.+?)\s+"
        r"(?P<valor>\d[\d\.]*,\d{2})\s+"
        r"(?P<tipo_valor>[CD])\s+"
        r"(?P<saldo>\d[\d\.]*,\d{2})\s+"
        r"(?P<tipo_saldo>[CD])$"
    )

    def __init__(self) -> None:
        self.supported_formats = [".pdf"]

    def validate_file(self, file_path: Path) -> bool:
        """Valida se o arquivo existe e tem formato suportado."""
        if not file_path.exists():
            log_error(f"Arquivo nao encontrado: {file_path}")
            return False

        if file_path.suffix.lower() not in self.supported_formats:
            log_error(
                f"Formato nao suportado: {file_path.suffix}. "
                f"Formatos aceitos: {self.supported_formats}"
            )
            return False

        if pdfplumber is None:
            log_error("Dependencia ausente: pdfplumber nao esta instalado")
            return False

        return True

    def extract_file(self, file_path: Path) -> pd.DataFrame:
        """Extrai movimentacoes de um PDF de extrato bancario."""
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"Arquivo invalido para extracao: {file_path}")

        log_info(f"Lendo arquivo PDF: {file_path.name}")
        extracted_rows: List[Dict[str, Any]] = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    if not page_text.strip():
                        log_warning(f"Pagina {page_number} sem texto extraivel; pagina ignorada")
                        continue

                    for line_number, raw_line in enumerate(page_text.splitlines(), start=1):
                        line = " ".join(raw_line.split()).strip()
                        if not line:
                            continue

                        match = self.LINE_PATTERN.match(line)
                        if not match:
                            log_warning(
                                f"Linha ignorada na pagina {page_number}, linha {line_number}: {line}"
                            )
                            continue

                        row = match.groupdict()
                        row["pagina"] = page_number
                        row["linha"] = line_number
                        extracted_rows.append(row)

            if not extracted_rows:
                log_warning("Nenhuma movimentacao foi reconhecida no PDF informado")
                return pd.DataFrame(
                    columns=[
                        "data",
                        "documento",
                        "historico",
                        "valor",
                        "tipo_valor",
                        "saldo",
                        "tipo_saldo",
                        "pagina",
                        "linha",
                    ]
                )

            extracted_df = pd.DataFrame(extracted_rows)
            log_success(
                f"Extracao concluida com sucesso: {len(extracted_df)} movimentacoes reconhecidas"
            )
            return extracted_df

        except Exception as exc:
            log_error(f"Erro ao ler arquivo PDF {file_path.name}", str(exc))
            raise

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Retorna informacoes basicas sobre o arquivo PDF."""
        if not file_path.exists():
            return {"error": "Arquivo nao encontrado"}

        stat = file_path.stat()
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "extension": file_path.suffix.lower(),
            "supported": file_path.suffix.lower() in self.supported_formats,
        }


def extract_data(pdf_path: Path) -> pd.DataFrame:
    """Funcao de conveniencia para extracao do novo fluxo com um unico PDF."""
    extractor = DataExtractor()
    try:
        log_info("Iniciando extracao do extrato bancario...")
        extracted_df = extractor.extract_file(pdf_path)
        log_success("Extracao concluida com sucesso.")
        return extracted_df
    except Exception as exc:
        log_error("Erro durante a extracao dos dados", str(exc))
        raise
