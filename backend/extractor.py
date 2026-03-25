"""
Statement extractors using a strategy/factory architecture.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd

from .logger import log_error, log_info, log_success, log_warning
from .rules_engine import RulesEngine

try:
    import pdfplumber
except ImportError:  # pragma: no cover - environment dependent
    pdfplumber = None


RawLine = Tuple[int, int, str]


class BaseExtractor(ABC):
    """Base class shared by all bank-specific PDF extractors."""

    OUTPUT_COLUMNS = [
        "data",
        "documento",
        "historico",
        "valor",
        "tipo_valor",
        "saldo",
        "tipo_saldo",
        "banco",
        "pagina",
        "linha",
    ]

    def __init__(self, bank_name: str, bank_rules: Dict[str, Any]) -> None:
        self.bank_name = RulesEngine.normalize_bank_name(bank_name)
        self.bank_rules = bank_rules
        self.supported_formats = [".pdf"]
        self.line_pattern = re.compile(bank_rules["padrao_linha_movimento"])
        self.reset_state()

    def reset_state(self) -> None:
        """Reset extractor state before a new file is processed."""

    def validate_file(self, file_path: Path) -> bool:
        """Validate file existence, extension and runtime dependencies."""
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

    def build_empty_dataframe(self) -> pd.DataFrame:
        """Return an empty dataframe with the raw extractor schema."""
        return pd.DataFrame(columns=self.OUTPUT_COLUMNS)

    def create_base_row(self, page_number: int, line_number: int) -> Dict[str, Any]:
        """Create a raw row shell compatible with the shared schema."""
        return {
            "data": None,
            "documento": None,
            "historico": None,
            "valor": None,
            "tipo_valor": None,
            "saldo": None,
            "tipo_saldo": None,
            "banco": self.bank_name,
            "pagina": page_number,
            "linha": line_number,
        }

    def iter_pdf_lines(self, file_path: Path) -> Iterable[RawLine]:
        """Yield normalized text lines from the PDF."""
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    log_warning(f"Pagina {page_number} sem texto extraivel; pagina ignorada")
                    continue

                for line_number, raw_line in enumerate(page_text.splitlines(), start=1):
                    line = " ".join(raw_line.split()).strip()
                    if line:
                        yield page_number, line_number, line

    def extract_file(self, file_path: Path) -> pd.DataFrame:
        """Extract statement movements from a PDF file."""
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"Arquivo invalido para extracao: {file_path}")

        self.reset_state()
        log_info(f"Lendo arquivo PDF ({self.bank_name}): {file_path.name}")

        try:
            extracted_df = self.extract_from_lines(self.iter_pdf_lines(file_path))
            log_success(
                f"Extracao concluida com sucesso: {len(extracted_df)} movimentacao(oes) reconhecida(s)"
            )
            return extracted_df
        except Exception as exc:
            log_error(
                f"Erro ao ler arquivo PDF {file_path.name} para {self.bank_name}",
                str(exc),
            )
            raise

    def extract_from_lines(self, lines: Iterable[RawLine]) -> pd.DataFrame:
        """Extract rows from an iterable of normalized lines."""
        extracted_rows: List[Dict[str, Any]] = []
        seen_text_lines = 0

        for page_number, line_number, line in lines:
            seen_text_lines += 1
            row = self.process_line(line, page_number, line_number)
            if row is not None:
                extracted_rows.append(row)

        if not seen_text_lines:
            raise ValueError(
                f"Nenhuma linha de texto foi encontrada no PDF para o banco {self.bank_name}"
            )

        if not extracted_rows:
            raise ValueError(
                "O PDF nao corresponde ao layout esperado para o banco "
                f"{self.bank_name} ou nao contem movimentacoes reconheciveis"
            )

        return pd.DataFrame(extracted_rows, columns=self.OUTPUT_COLUMNS)

    @abstractmethod
    def process_line(
        self, line: str, page_number: int, line_number: int
    ) -> Dict[str, Any] | None:
        """Process a normalized statement line."""


class CaixaExtractor(BaseExtractor):
    """Stateless extractor for CAIXA statements."""

    def process_line(
        self, line: str, page_number: int, line_number: int
    ) -> Dict[str, Any] | None:
        match = self.line_pattern.match(line)
        if not match:
            return None

        row = self.create_base_row(page_number, line_number)
        groups = match.groups()
        row.update(
            {
                "data": groups[0],
                "documento": groups[1] or None,
                "historico": groups[2].strip(),
                "valor": groups[3],
                "tipo_valor": groups[4],
                "saldo": groups[5] if len(groups) > 5 else None,
                "tipo_saldo": groups[6] if len(groups) > 6 else None,
            }
        )
        return row


class BBExtractor(BaseExtractor):
    """Stateful extractor for Banco do Brasil statements."""

    def __init__(self, bank_name: str, bank_rules: Dict[str, Any]) -> None:
        self.saldo_pattern = re.compile(bank_rules["padrao_linha_saldo"])
        super().__init__(bank_name, bank_rules)

    def reset_state(self) -> None:
        self.current_year: int | None = None
        self.previous_month: int | None = None

    def process_line(
        self, line: str, page_number: int, line_number: int
    ) -> Dict[str, Any] | None:
        saldo_match = self.saldo_pattern.match(line)
        if saldo_match:
            saldo_date = saldo_match.group(1)
            day, month, year = saldo_date.split(".")
            self.current_year = int(year)
            self.previous_month = int(month)
            log_info(
                f"Linha de saldo BB identificada na pagina {page_number}, linha {line_number}"
            )
            return None

        movement_match = self.line_pattern.match(line)
        if not movement_match:
            return None

        if self.current_year is None or self.previous_month is None:
            raise ValueError(
                "Extrato BB invalido: linha de movimento encontrada antes da linha "
                "'Saldo em DD.MM.AAAA'"
            )

        groups = movement_match.groups()
        day_month = groups[0]
        movement_month = int(day_month.split(".")[1])

        if movement_month == 1 and self.previous_month == 12:
            self.current_year += 1

        full_date = f"{day_month}.{self.current_year}"
        self.previous_month = movement_month

        row = self.create_base_row(page_number, line_number)
        row.update(
            {
                "data": full_date,
                "documento": groups[1] or None,
                "historico": groups[2].strip(),
                "valor": groups[3],
                "tipo_valor": groups[4],
            }
        )
        return row


class ExtractorFactory:
    """Instantiate the correct extractor for the selected bank."""

    EXTRACTOR_MAP = {
        "CAIXA": CaixaExtractor,
        "BB": BBExtractor,
    }

    @classmethod
    def create(cls, bank_name: str, bank_rules: Dict[str, Any]) -> BaseExtractor:
        normalized_bank_name = RulesEngine.normalize_bank_name(bank_name)
        extractor_cls = cls.EXTRACTOR_MAP.get(normalized_bank_name)

        if extractor_cls is None:
            raise ValueError(f"Nao ha extrator configurado para o banco {normalized_bank_name}")

        return extractor_cls(normalized_bank_name, bank_rules)


def extract_data(pdf_path: Path, bank_name: str) -> pd.DataFrame:
    """Convenience function for the multi-bank extraction flow."""
    rules_engine = RulesEngine()
    bank_rules = rules_engine.get_bank_rules(bank_name)
    extractor = ExtractorFactory.create(bank_name, bank_rules)

    try:
        log_info(f"Iniciando extracao do extrato bancario ({extractor.bank_name})...")
        extracted_df = extractor.extract_file(pdf_path)
        log_success("Extracao concluida com sucesso.")
        return extracted_df
    except Exception as exc:
        log_error("Erro durante a extracao dos dados", str(exc))
        raise
