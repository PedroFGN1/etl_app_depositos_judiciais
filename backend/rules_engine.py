"""
Motor de regras dinamico para classificacao de extratos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .config import config
from .logger import log_error, log_info, log_success, log_warning


class RulesEngine:
    """Carrega e valida regras de classificacao a partir de um arquivo JSON."""

    DEFAULT_RULES = {
        "DB TR CT": "Resgate",
        "CR J SELIC": "Rendimento",
        "TAR MANUT": "Tarifa",
    }

    def __init__(self, rules_path: Path | None = None) -> None:
        self.rules_path = rules_path or (config.OUTPUT_PATH / "regras_extrato.json")

    def ensure_rules_file(self) -> Path:
        """Cria o arquivo padrao caso ele nao exista."""
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.rules_path.exists():
            log_warning(
                f"Arquivo de regras nao encontrado. Criando padrao em: {self.rules_path}"
            )
            with open(self.rules_path, "w", encoding="utf-8") as file_obj:
                json.dump(self.DEFAULT_RULES, file_obj, indent=2, ensure_ascii=False)
            log_success("Arquivo padrao de regras criado com sucesso")

        return self.rules_path

    def load_rules(self) -> Dict[str, str]:
        """Carrega, valida e retorna as regras seguras para o sistema."""
        rules_path = self.ensure_rules_file()
        log_info(f"Carregando regras dinamicas de: {rules_path}")

        try:
            with open(rules_path, "r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
        except json.JSONDecodeError as exc:
            log_error("Arquivo de regras JSON invalido", str(exc))
            raise ValueError("Arquivo de regras JSON invalido") from exc
        except Exception as exc:
            log_error("Erro ao ler arquivo de regras", str(exc))
            raise

        if not isinstance(data, dict):
            log_error("Arquivo de regras invalido: a raiz do JSON deve ser um objeto")
            raise ValueError("Arquivo de regras invalido: raiz do JSON deve ser objeto")

        safe_rules: Dict[str, str] = {}
        ignored_entries = 0

        for raw_key, raw_value in data.items():
            if not isinstance(raw_key, str) or not isinstance(raw_value, str):
                ignored_entries += 1
                continue

            key = " ".join(raw_key.strip().upper().split())
            value = raw_value.strip()

            if not key or not value:
                ignored_entries += 1
                continue

            safe_rules[key] = value

        if not safe_rules:
            log_error("Nenhuma regra valida foi encontrada no arquivo de regras")
            raise ValueError("Nenhuma regra valida foi encontrada no arquivo de regras")

        if ignored_entries:
            log_warning(f"{ignored_entries} regra(s) invalida(s) foram ignoradas")

        log_success(f"Motor de regras carregado com {len(safe_rules)} regra(s) valida(s)")
        return safe_rules
