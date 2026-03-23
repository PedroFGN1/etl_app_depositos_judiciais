"""
Módulo de Carga (Load)
Funções para carregar os dados transformados no Data Warehouse.
"""

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text, inspect
from typing import Dict, List, Any
from pathlib import Path

from .config import config
from .logger import log_info, log_error, log_success, log_warning, log_debug


class DataLoader:
    """Classe responsável pela carga de dados no banco"""
    
    def __init__(self, database_config=None):
        self.database_config = database_config or config.database
        self.engine = None
        self._connect()
    
    def _connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            engine_url = self.database_config.get_engine_url()
            log_info(f"Conectando ao banco: {self.database_config.db_type}")
            log_debug(f"URL de conexão: {engine_url.split('@')[0]}@***")  # Ocultar credenciais
            
            self.engine = create_engine(engine_url)
            
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            log_success("Conexão com banco de dados estabelecida")
            
        except Exception as e:
            log_error("Erro ao conectar com banco de dados", str(e))
            raise
    
    def test_connection(self) -> bool:
        """Testa a conexão com o banco de dados"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log_success("Teste de conexão bem-sucedido")
            return True
        except Exception as e:
            log_error("Teste de conexão falhou", str(e))
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Retorna informações sobre uma tabela"""
        try:
            inspector = inspect(self.engine)
            
            if not inspector.has_table(table_name):
                return {"exists": False}
            
            columns = inspector.get_columns(table_name)
            
            # Contar registros
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
            
            return {
                "exists": True,
                "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
                "row_count": row_count
            }
            
        except Exception as e:
            log_error(f"Erro ao obter informações da tabela {table_name}", str(e))
            return {"exists": False, "error": str(e)}
    
    def list_tables(self) -> List[str]:
        """Lista todas as tabelas no banco"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            log_info(f"Tabelas encontradas: {tables}")
            return tables
        except Exception as e:
            log_error("Erro ao listar tabelas", str(e))
            return []
    
    def drop_table(self, table_name: str) -> bool:
        """Remove uma tabela do banco"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
            log_success(f"Tabela {table_name} removida")
            return True
        except Exception as e:
            log_error(f"Erro ao remover tabela {table_name}", str(e))
            return False
    
    def load_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace') -> bool:
        """Carrega um DataFrame para uma tabela"""
        try:
            log_info(f"Carregando tabela '{table_name}' com {len(df)} registros...")
            
            # Validar DataFrame
            if df.empty:
                log_warning(f"DataFrame vazio para tabela {table_name}")
                return False
            
            # Verificar se a tabela já existe
            table_info = self.get_table_info(table_name)
            if table_info.get("exists"):
                log_info(f"Tabela {table_name} já existe com {table_info.get('row_count', 0)} registros")
                if if_exists == 'fail':
                    log_error(f"Tabela {table_name} já existe e if_exists='fail'")
                    return False
                elif if_exists == 'append':
                    log_info(f"Adicionando dados à tabela existente {table_name}")
                elif if_exists == 'replace':
                    log_info(f"Substituindo tabela {table_name}")
            
            # Carregar dados
            with self.engine.connect() as conn:
                df.to_sql(table_name, conn, if_exists=if_exists, index=False)
                conn.commit()
            
            # Verificar resultado
            final_info = self.get_table_info(table_name)
            final_count = final_info.get('row_count', 0)
            
            log_success(f"Tabela '{table_name}' carregada com {final_count} registros")
            return True
            
        except Exception as e:
            log_error(f"Erro ao carregar tabela {table_name}", str(e))
            return False
    
    def load_multiple_dataframes(self, dataframes: Dict[str, pd.DataFrame], if_exists: str = 'replace') -> Dict[str, bool]:
        """Carrega múltiplos DataFrames"""
        log_info(f"Iniciando carga de {len(dataframes)} tabelas...")
        
        results = {}
        success_count = 0
        
        for table_name, df in dataframes.items():
            try:
                success = self.load_dataframe(df, table_name, if_exists)
                results[table_name] = success
                if success:
                    success_count += 1
            except Exception as e:
                log_error(f"Erro ao carregar {table_name}", str(e))
                results[table_name] = False
        
        if success_count == len(dataframes):
            log_success("Todas as tabelas foram carregadas com sucesso")
        else:
            failed_count = len(dataframes) - success_count
            log_warning(f"Carga concluída: {success_count} sucessos, {failed_count} falhas")
        
        return results
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Executa uma query e retorna o resultado como DataFrame"""
        try:
            log_debug(f"Executando query: {query[:100]}...")
            
            with self.engine.connect() as conn:
                result_df = pd.read_sql(query, conn)
            
            log_success(f"Query executada: {len(result_df)} registros retornados")
            return result_df
            
        except Exception as e:
            log_error("Erro ao executar query", str(e))
            raise
    
    def backup_database(self, backup_path: str) -> bool:
        """Cria backup do banco de dados (SQLite apenas)"""
        try:
            if self.database_config.db_type != 'sqlite':
                log_warning("Backup automático disponível apenas para SQLite")
                return False
            
            import shutil
            source_path = Path(self.database_config.config['path'])
            backup_path = Path(backup_path)
            
            if source_path.exists():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, backup_path)
                log_success(f"Backup criado: {backup_path}")
                return True
            else:
                log_error("Arquivo de banco não encontrado para backup")
                return False
                
        except Exception as e:
            log_error("Erro ao criar backup", str(e))
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        try:
            stats = {
                "database_type": self.database_config.db_type,
                "tables": {},
                "total_tables": 0,
                "total_records": 0
            }
            
            tables = self.list_tables()
            stats["total_tables"] = len(tables)
            
            for table in tables:
                table_info = self.get_table_info(table)
                if table_info.get("exists"):
                    row_count = table_info.get("row_count", 0)
                    stats["tables"][table] = {
                        "rows": row_count,
                        "columns": len(table_info.get("columns", []))
                    }
                    stats["total_records"] += row_count
            
            return stats
            
        except Exception as e:
            log_error("Erro ao obter estatísticas do banco", str(e))
            return {"error": str(e)}


# Instância global do loader
data_loader = DataLoader()


# Função de conveniência para manter compatibilidade com código original
def load_data(dataframes: Dict[str, pd.DataFrame], engine: sqlalchemy.engine.Engine = None):
    """
    Função original adaptada para usar a nova classe
    Carrega os DataFrames transformados para o banco de dados.
    """
    try:
        log_info("Iniciando carga dos dados no Data Warehouse...")
        
        if engine:
            # Usar engine fornecido (compatibilidade)
            with engine.connect() as connection:
                for table_name, df in dataframes.items():
                    log_info(f"Carregando tabela '{table_name}'...")
                    df.to_sql(table_name, connection, if_exists='replace', index=False)
                    log_info(f"Tabela '{table_name}' carregada com {len(df)} linhas.")
        else:
            # Usar loader global
            data_loader.load_multiple_dataframes(dataframes)
        
        log_success("Carga de dados concluída com sucesso.")
        
    except Exception as e:
        log_error("Erro durante a carga dos dados", str(e))
        raise

