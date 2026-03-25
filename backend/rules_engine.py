"""
Dynamic rules engine for multi-bank statement processing.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict

from .config import config
from .logger import log_error, log_info, log_success, log_warning


class RulesEngine:
    """Load and validate extraction and classification rules from JSON."""

    DEFAULT_RULES: Dict[str, Dict[str, Any]] = {
        "CAIXA": {
            "padrao_linha_movimento": (
                r"^(\d{2}/\d{2}/\d{4})\s+(\S+)\s+(.+?)\s+([\d\.,]+)\s+([CD])"
                r"(?:\s+([\d\.,]+)\s+([CD]))?$"
            ),
            "formato_data": "%d/%m/%Y",
            "rubricas": {
                "DB TR CT": "Resgate",
                "CR J SELIC": "Rendimento",
                "TAR MANUT": "Tarifa",
            },
        },
        "BB": {
            "padrao_linha_saldo": "^Saldo em (\\d{2}\\.\\d{2}\\.\\d{4})(?:\\s+[\\d\\.,]+\\s+[CD])?$",
            "padrao_linha_movimento": (
                r"^(\d{2}\.\d{2})\s+(\d+)?\s*(.+?)\s+([\d\.,]+)\s+([CD])$"
            ),
            "formato_data": "%d.%m.%Y",
            "rubricas": {
                "ANOTACAO DE RESGATE EM FUNDO GARANT": "Resgate",
                "ATUALIZACAO DE REC APLICADOS": "Rendimento",
            },
        },
    }

    REQUIRED_BANK_KEYS = {"padrao_linha_movimento", "formato_data", "rubricas"}

    def __init__(self, rules_path: Path | None = None) -> None:
        self.rules_path = rules_path or (config.OUTPUT_PATH / "regras_extrato.json")

    @staticmethod
    def normalize_bank_name(bank_name: str) -> str:
        """Normalize bank names to a stable lookup format."""
        return " ".join(str(bank_name).strip().upper().split())

    @staticmethod
    def normalize_rule_key(raw_key: str) -> str:
        """Normalize text used for rule matching."""
        return " ".join(str(raw_key).strip().upper().split())

    def ensure_rules_file(self) -> Path:
        """Create a default multi-bank rules file if missing."""
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.rules_path.exists():
            log_warning(
                f"Arquivo de regras nao encontrado. Criando padrao em: {self.rules_path}"
            )
            with open(self.rules_path, "w", encoding="utf-8") as file_obj:
                json.dump(self.DEFAULT_RULES, file_obj, indent=2, ensure_ascii=False)
            log_success("Arquivo padrao multi-banco criado com sucesso")

        return self.rules_path

    def load_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load and validate all bank configurations."""
        rules_path = self.ensure_rules_file()
        log_info(f"Carregando regras dinamicas de: {rules_path}")

        try:
            with open(rules_path, "r", encoding="utf-8") as file_obj:
                raw_data = json.load(file_obj)
        except json.JSONDecodeError as exc:
            log_error("Arquivo de regras JSON invalido", str(exc))
            raise ValueError("Arquivo de regras JSON invalido") from exc
        except Exception as exc:
            log_error("Erro ao ler arquivo de regras", str(exc))
            raise

        if not isinstance(raw_data, dict):
            log_error("Arquivo de regras invalido: a raiz do JSON deve ser um objeto")
            raise ValueError("Arquivo de regras invalido: raiz do JSON deve ser objeto")

        safe_rules: Dict[str, Dict[str, Any]] = {}
        ignored_banks = 0

        for raw_bank_name, raw_bank_config in raw_data.items():
            bank_name = self.normalize_bank_name(raw_bank_name)

            if not isinstance(raw_bank_config, dict):
                ignored_banks += 1
                log_warning(f"Configuracao ignorada para banco invalido: {raw_bank_name}")
                continue

            missing_keys = self.REQUIRED_BANK_KEYS - set(raw_bank_config.keys())
            if missing_keys:
                ignored_banks += 1
                log_warning(
                    f"Banco {bank_name} ignorado por faltar chave(s): {sorted(missing_keys)}"
                )
                continue

            if bank_name == "BB" and not isinstance(
                raw_bank_config.get("padrao_linha_saldo"), str
            ):
                ignored_banks += 1
                log_warning(
                    "Banco BB ignorado: 'padrao_linha_saldo' deve ser informado como texto"
                )
                continue

            movement_pattern = raw_bank_config.get("padrao_linha_movimento")
            date_format = raw_bank_config.get("formato_data")
            rubricas = raw_bank_config.get("rubricas")

            if not isinstance(movement_pattern, str) or not movement_pattern.strip():
                ignored_banks += 1
                log_warning(
                    f"Banco {bank_name} ignorado: 'padrao_linha_movimento' invalido"
                )
                continue

            if not isinstance(date_format, str) or not date_format.strip():
                ignored_banks += 1
                log_warning(f"Banco {bank_name} ignorado: 'formato_data' invalido")
                continue

            if not isinstance(rubricas, dict):
                ignored_banks += 1
                log_warning(f"Banco {bank_name} ignorado: 'rubricas' deve ser um objeto")
                continue

            normalized_rubricas: Dict[str, str] = {}
            ignored_rules = 0

            for raw_key, raw_value in rubricas.items():
                if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                    ignored_rules += 1
                    continue

                key = self.normalize_rule_key(raw_key)
                value = raw_value.strip()
                if not key or not value:
                    ignored_rules += 1
                    continue

                normalized_rubricas[key] = value

            if not normalized_rubricas:
                ignored_banks += 1
                log_warning(f"Banco {bank_name} ignorado: nenhuma rubrica valida encontrada")
                continue

            safe_rules[bank_name] = {
                "bank_name": bank_name,
                "padrao_linha_movimento": movement_pattern.strip(),
                "formato_data": date_format.strip(),
                "rubricas": normalized_rubricas,
            }

            if "padrao_linha_saldo" in raw_bank_config:
                saldo_pattern = raw_bank_config.get("padrao_linha_saldo")
                if isinstance(saldo_pattern, str) and saldo_pattern.strip():
                    safe_rules[bank_name]["padrao_linha_saldo"] = saldo_pattern.strip()

            if ignored_rules:
                log_warning(
                    f"{ignored_rules} rubrica(s) invalida(s) foram ignoradas para {bank_name}"
                )

        if not safe_rules:
            log_error("Nenhuma configuracao valida de banco foi encontrada no arquivo")
            raise ValueError("Nenhuma configuracao valida de banco foi encontrada")

        if ignored_banks:
            log_warning(f"{ignored_banks} configuracao(oes) de banco foram ignoradas")

        log_success(
            f"Motor de regras carregado com {len(safe_rules)} configuracao(oes) de banco"
        )
        return safe_rules

    def get_bank_rules(self, bank_name: str) -> Dict[str, Any]:
        """Return the validated configuration for the selected bank."""
        normalized_bank_name = self.normalize_bank_name(bank_name)
        rules = self.load_rules()

        if normalized_bank_name not in rules:
            available_banks = ", ".join(sorted(rules.keys()))
            log_error(
                f"Banco nao encontrado nas regras: {normalized_bank_name}",
                f"Disponiveis: {available_banks}",
            )
            raise ValueError(
                f"Banco '{normalized_bank_name}' nao encontrado nas regras. "
                f"Disponiveis: {available_banks}"
            )

        return copy.deepcopy(rules[normalized_bank_name])
