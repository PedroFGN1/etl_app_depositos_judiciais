"""
Logging helpers for console and optional Eel frontend integration.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

try:
    import eel
except ImportError:  # pragma: no cover - optional in tests/CLI
    eel = None


class LogLevel(Enum):
    """Log levels and colors shared with the frontend."""

    DEBUG = ("DEBUG", "#6c757d")
    INFO = ("INFO", "#17a2b8")
    SUCCESS = ("SUCCESS", "#28a745")
    WARNING = ("WARNING", "#ffc107")
    ERROR = ("ERROR", "#dc3545")
    CRITICAL = ("CRITICAL", "#6f42c1")


class ETLLogger:
    """Application logger with in-memory history."""

    def __init__(self, name: str = "ETL_Logger") -> None:
        self.name = name
        self.logs: List[Dict[str, Any]] = []
        self.setup_logger()

    def setup_logger(self) -> None:
        """Configure the base console logger."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _notify_frontend(self, method_name: str, *args: Any) -> None:
        """Send a best-effort event to the Eel frontend if available."""
        if eel is None:
            return

        try:
            getattr(eel, method_name)(*args)
        except Exception:
            pass

    def _log_message(self, level: LogLevel, message: str, details: str | None = None) -> None:
        """Store, forward and print a log entry."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level.value[0],
            "color": level.value[1],
            "message": message,
            "details": details or "",
        }
        self.logs.append(log_entry)
        self._notify_frontend("add_log_message", log_entry)

        if level == LogLevel.DEBUG:
            self.logger.debug(message)
        elif level == LogLevel.INFO:
            self.logger.info(message)
        elif level == LogLevel.SUCCESS:
            self.logger.info(f"[OK] {message}")
        elif level == LogLevel.WARNING:
            self.logger.warning(message)
        elif level == LogLevel.ERROR:
            self.logger.error(message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(message)

    def debug(self, message: str, details: str | None = None) -> None:
        self._log_message(LogLevel.DEBUG, message, details)

    def info(self, message: str, details: str | None = None) -> None:
        self._log_message(LogLevel.INFO, message, details)

    def success(self, message: str, details: str | None = None) -> None:
        self._log_message(LogLevel.SUCCESS, message, details)

    def warning(self, message: str, details: str | None = None) -> None:
        self._log_message(LogLevel.WARNING, message, details)

    def error(self, message: str, details: str | None = None) -> None:
        self._log_message(LogLevel.ERROR, message, details)

    def critical(self, message: str, details: str | None = None) -> None:
        self._log_message(LogLevel.CRITICAL, message, details)

    def clear_logs(self) -> None:
        self.logs.clear()
        self._notify_frontend("clear_logs")

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs.copy()

    def get_logs_by_level(self, level: LogLevel) -> List[Dict[str, Any]]:
        return [log for log in self.logs if log["level"] == level.value[0]]

    def export_logs(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as file_obj:
            for log in self.logs:
                file_obj.write(f"[{log['timestamp']}] {log['level']}: {log['message']}\n")
                if log["details"]:
                    file_obj.write(f"    Detalhes: {log['details']}\n")
                file_obj.write("\n")


etl_logger = ETLLogger()


def log_debug(message: str, details: str | None = None) -> None:
    etl_logger.debug(message, details)


def log_info(message: str, details: str | None = None) -> None:
    etl_logger.info(message, details)


def log_success(message: str, details: str | None = None) -> None:
    etl_logger.success(message, details)


def log_warning(message: str, details: str | None = None) -> None:
    etl_logger.warning(message, details)


def log_error(message: str, details: str | None = None) -> None:
    etl_logger.error(message, details)


def log_critical(message: str, details: str | None = None) -> None:
    etl_logger.critical(message, details)
