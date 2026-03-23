"""
Módulo de Configuração
Centraliza as configurações do projeto para fácil manutenção e flexibilidade.
"""

import os
from pathlib import Path
from typing import Dict, Any
import json


class DatabaseConfig:
    """Configurações de banco de dados flexíveis"""
    
    # Configurações padrão para diferentes tipos de banco
    DATABASE_CONFIGS = {
        'sqlite': {
            'driver': 'sqlite',
            'path': './output/contas_judiciais.db',
            'engine_template': 'sqlite:///{path}'
        },
        'postgresql': {
            'driver': 'postgresql+psycopg2',
            'host': 'localhost',
            'port': 5432,
            'database': 'etl_database',
            'username': 'postgres',
            'password': 'password',
            'engine_template': 'postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}'
        },
        'mysql': {
            'driver': 'mysql+pymysql',
            'host': 'localhost',
            'port': 3306,
            'database': 'etl_database',
            'username': 'root',
            'password': 'password',
            'engine_template': 'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
        },
        'sqlserver': {
            'driver': 'mssql+pyodbc',
            'host': 'localhost',
            'port': 1433,
            'database': 'etl_database',
            'username': 'sa',
            'password': 'password',
            'engine_template': 'mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
        }
    }
    
    def __init__(self, db_type: str = 'sqlite', custom_config: Dict[str, Any] = None):
        self.db_type = db_type
        self.config = self.DATABASE_CONFIGS.get(db_type, self.DATABASE_CONFIGS['sqlite']).copy()
        
        if custom_config:
            self.config.update(custom_config)
    
    def get_engine_url(self) -> str:
        """Retorna a URL de conexão do banco de dados"""
        if self.db_type == 'sqlite':
            # Garante que o diretório existe para SQLite
            db_path = Path(self.config['path'])
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return self.config['engine_template'].format(path=db_path.absolute())
        else:
            return self.config['engine_template'].format(**self.config)
    
    def update_config(self, **kwargs):
        """Atualiza configurações específicas"""
        self.config.update(kwargs)


class AppConfig:
    """Configurações gerais da aplicação"""
    
    def __init__(self):
        # Paths do projeto
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.BACKEND_PATH = self.PROJECT_ROOT / "backend"
        self.FRONTEND_PATH = self.PROJECT_ROOT / "frontend"
        self.DATA_SAMPLES_PATH = self.PROJECT_ROOT / "data_samples"
        self.OUTPUT_PATH = self.PROJECT_ROOT / "output"
        
        # Configurações de upload
        self.UPLOAD_FOLDER = self.PROJECT_ROOT / "uploads"
        self.MAX_FILE_SIZE = 150 * 1024 * 1024  # 150MB
        self.ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}
        
        # Nomes das tabelas no Data Warehouse
        self.TABLE_CONTAS = "Contas"
        self.TABLE_SALDOS = "Saldos"
        self.TABLE_RESGATES = "Resgates"
        
        # Configurações do servidor Eel
        self.EEL_HOST = 'localhost'
        self.EEL_PORT = 0
        self.EEL_DEBUG = True
        
        # Configuração de banco de dados
        self.database = DatabaseConfig()
        
        # Criar diretórios necessários
        self._create_directories()
    
    def _create_directories(self):
        """Cria os diretórios necessários se não existirem"""
        directories = [
            self.OUTPUT_PATH,
            self.UPLOAD_FOLDER,
            self.DATA_SAMPLES_PATH
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def set_database_config(self, db_type: str, **kwargs):
        """Configura o tipo de banco de dados"""
        self.database = DatabaseConfig(db_type, kwargs)
    
    def get_database_engine_url(self) -> str:
        """Retorna a URL de conexão do banco de dados"""
        return self.database.get_engine_url()
    
    def load_from_file(self, config_file: str):
        """Carrega configurações de um arquivo JSON"""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Atualizar configurações de banco se especificadas
            if 'database' in config_data:
                db_config = config_data['database']
                db_type = db_config.pop('type', 'sqlite')
                self.set_database_config(db_type, **db_config)
            
            # Atualizar outras configurações
            for key, value in config_data.items():
                if key != 'database' and hasattr(self, key.upper()):
                    setattr(self, key.upper(), value)
    
    def save_to_file(self, config_file: str):
        """Salva as configurações atuais em um arquivo JSON"""
        config_data = {
            'database': {
                'type': self.database.db_type,
                **self.database.config
            },
            'eel_host': self.EEL_HOST,
            'eel_port': self.EEL_PORT,
            'eel_debug': self.EEL_DEBUG,
            'max_file_size': self.MAX_FILE_SIZE
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)


# Instância global de configuração
config = AppConfig()

