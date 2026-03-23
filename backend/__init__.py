"""
Backend ETL Application
Módulos para processamento ETL de dados judiciais.
"""

from .config import config, AppConfig, DatabaseConfig
from .logger import etl_logger, log_info, log_error, log_success, log_warning, log_debug, log_critical
from .extractor import data_extractor, extract_data
from .transformer import data_transformer
from .loader import data_loader, load_data
from .etl_pipeline import etl_pipeline, main

__version__ = "1.0.0"
__author__ = "ETL Team"

__all__ = [
    'config',
    'AppConfig', 
    'DatabaseConfig',
    'etl_logger',
    'log_info',
    'log_error', 
    'log_success',
    'log_warning',
    'log_debug',
    'log_critical',
    'data_extractor',
    'extract_data',
    'data_transformer', 
    'data_loader',
    'load_data',
    'etl_pipeline',
    'main'
]

