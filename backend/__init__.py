"""
Backend ETL Application
Modulos para processamento ETL de extratos bancarios em PDF.
"""

from .config import AppConfig, DatabaseConfig, config
from .etl_pipeline import ETLPipeline, create_pipeline, main
from .extractor import DataExtractor, extract_data
from .loader import data_loader, load_data
from .logger import (
    etl_logger,
    log_critical,
    log_debug,
    log_error,
    log_info,
    log_success,
    log_warning,
)
from .rules_engine import RulesEngine
from .transformer import DataTransformer, apply_business_rules

__version__ = "2.0.0"
__author__ = "ETL Team"

__all__ = [
    "config",
    "AppConfig",
    "DatabaseConfig",
    "etl_logger",
    "log_info",
    "log_error",
    "log_success",
    "log_warning",
    "log_debug",
    "log_critical",
    "DataExtractor",
    "extract_data",
    "DataTransformer",
    "apply_business_rules",
    "RulesEngine",
    "data_loader",
    "load_data",
    "ETLPipeline",
    "create_pipeline",
    "main",
]
