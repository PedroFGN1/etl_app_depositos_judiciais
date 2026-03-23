"""
Módulo de Logging
Sistema de logging com suporte a cores e comunicação com frontend via Eel.
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum
import eel


class LogLevel(Enum):
    """Níveis de log com cores associadas"""
    DEBUG = ("DEBUG", "#6c757d")      # Cinza
    INFO = ("INFO", "#17a2b8")        # Azul claro
    SUCCESS = ("SUCCESS", "#28a745")   # Verde
    WARNING = ("WARNING", "#ffc107")   # Amarelo
    ERROR = ("ERROR", "#dc3545")       # Vermelho
    CRITICAL = ("CRITICAL", "#6f42c1") # Roxo


class ETLLogger:
    """Logger personalizado para o sistema ETL"""
    
    def __init__(self, name: str = "ETL_Logger"):
        self.name = name
        self.logs: List[Dict[str, Any]] = []
        self.setup_logger()
    
    def setup_logger(self):
        """Configura o logger básico"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove handlers existentes para evitar duplicação
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formato personalizado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _log_message(self, level: LogLevel, message: str, details: str = None):
        """Método interno para registrar mensagens"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_entry = {
            'timestamp': timestamp,
            'level': level.value[0],
            'color': level.value[1],
            'message': message,
            'details': details or ""
        }
        
        self.logs.append(log_entry)
        
        # Enviar para o frontend via Eel (se disponível)
        try:
            eel.add_log_message(log_entry)
        except:
            pass  # Eel pode não estar disponível durante testes
        
        # Log no console também
        if level == LogLevel.DEBUG:
            self.logger.debug(message)
        elif level == LogLevel.INFO:
            self.logger.info(message)
        elif level == LogLevel.SUCCESS:
            self.logger.info(f"✔ {message}")
        elif level == LogLevel.WARNING:
            self.logger.warning(message)
        elif level == LogLevel.ERROR:
            self.logger.error(message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(message)
    
    def debug(self, message: str, details: str = None):
        """Log de debug"""
        self._log_message(LogLevel.DEBUG, message, details)
    
    def info(self, message: str, details: str = None):
        """Log de informação"""
        self._log_message(LogLevel.INFO, message, details)
    
    def success(self, message: str, details: str = None):
        """Log de sucesso"""
        self._log_message(LogLevel.SUCCESS, message, details)
    
    def warning(self, message: str, details: str = None):
        """Log de aviso"""
        self._log_message(LogLevel.WARNING, message, details)
    
    def error(self, message: str, details: str = None):
        """Log de erro"""
        self._log_message(LogLevel.ERROR, message, details)
    
    def critical(self, message: str, details: str = None):
        """Log crítico"""
        self._log_message(LogLevel.CRITICAL, message, details)
    
    def clear_logs(self):
        """Limpa todos os logs"""
        self.logs.clear()
        try:
            eel.clear_logs()
        except:
            pass
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Retorna todos os logs"""
        return self.logs.copy()
    
    def get_logs_by_level(self, level: LogLevel) -> List[Dict[str, Any]]:
        """Retorna logs filtrados por nível"""
        return [log for log in self.logs if log['level'] == level.value[0]]
    
    def export_logs(self, filepath: str):
        """Exporta logs para arquivo"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for log in self.logs:
                f.write(f"[{log['timestamp']}] {log['level']}: {log['message']}\n")
                if log['details']:
                    f.write(f"    Detalhes: {log['details']}\n")
                f.write("\n")


# Instância global do logger
etl_logger = ETLLogger()


# Funções de conveniência para uso direto
def log_debug(message: str, details: str = None):
    etl_logger.debug(message, details)

def log_info(message: str, details: str = None):
    etl_logger.info(message, details)

def log_success(message: str, details: str = None):
    etl_logger.success(message, details)

def log_warning(message: str, details: str = None):
    etl_logger.warning(message, details)

def log_error(message: str, details: str = None):
    etl_logger.error(message, details)

def log_critical(message: str, details: str = None):
    etl_logger.critical(message, details)

