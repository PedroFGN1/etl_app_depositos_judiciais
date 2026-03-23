"""
Módulo Principal do Pipeline ETL
Orquestra a execução do pipeline ETL completo.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import traceback

from .config import config
from .logger import log_info, log_error, log_success, log_warning, log_critical, etl_logger
from .extractor import data_extractor, extract_data
from .transformer import data_transformer
from .loader import data_loader


class ETLPipeline:
    """Classe principal que orquestra o pipeline ETL"""
    
    def __init__(self):
        self.config = config
        self.extractor = data_extractor
        self.transformer = data_transformer
        self.loader = data_loader
        self.logger = etl_logger
        
        # Estado do pipeline
        self.current_step = None
        self.progress = 0
        self.total_steps = 7
        self.results = {}
    
    def update_progress(self, step: str, progress: int):
        """Atualiza o progresso do pipeline"""
        self.current_step = step
        self.progress = progress
        log_info(f"Progresso: {progress}/{self.total_steps} - {step}")
    
    def validate_input_files(self, saldos_path: str, resgates_path: str) -> bool:
        """Valida os arquivos de entrada"""
        try:
            log_info("Validando arquivos de entrada...")
            
            saldos_file = Path(saldos_path)
            resgates_file = Path(resgates_path)
            
            # Verificar se os arquivos existem
            if not saldos_file.exists():
                log_error(f"Arquivo de saldos não encontrado: {saldos_path}")
                return False
            
            if not resgates_file.exists():
                log_error(f"Arquivo de resgates não encontrado: {resgates_path}")
                return False
            
            # Verificar formatos
            if not self.extractor.validate_file(saldos_file):
                return False
            
            if not self.extractor.validate_file(resgates_file):
                return False
            
            log_success("Validação dos arquivos concluída")
            return True
            
        except Exception as e:
            log_error("Erro na validação dos arquivos", str(e))
            return False
    
    def extract_phase(self, saldos_path: str, resgates_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fase de extração dos dados"""
        try:
            self.update_progress("Extraindo dados dos arquivos", 1)
            
            saldos_df, resgates_df = extract_data(Path(saldos_path), Path(resgates_path))
            
            # Armazenar informações sobre os dados extraídos
            self.results['extraction'] = {
                'saldos_rows': len(saldos_df),
                'saldos_cols': len(saldos_df.columns),
                'resgates_rows': len(resgates_df),
                'resgates_cols': len(resgates_df.columns)
            }
            
            log_success(f"Extração concluída - Saldos: {len(saldos_df)} linhas, Resgates: {len(resgates_df)} linhas")
            return saldos_df, resgates_df
            
        except Exception as e:
            log_error("Erro na fase de extração", str(e))
            raise
    
    def transform_phase(self, saldos_df: pd.DataFrame, resgates_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Fase de transformação dos dados"""
        try:
            self.update_progress("Transformando dados de saldos", 2)
            saldos_transformed = self.transformer.transform_saldos(saldos_df)
            
            self.update_progress("Transformando dados de resgates", 3)
            resgates_transformed = self.transformer.transform_resgates(resgates_df)
            
            self.update_progress("Criando dimensão de contas", 4)
            dim_contas = self.transformer.create_dimension_contas(saldos_transformed, resgates_transformed)
            
            self.update_progress("Adicionando chaves estrangeiras", 5)
            fact_saldos = self.transformer.add_foreign_keys(saldos_transformed, dim_contas)
            fact_resgates = self.transformer.add_foreign_keys(resgates_transformed, dim_contas)
            
            # Armazenar informações sobre os dados transformados
            self.results['transformation'] = {
                'dim_contas_rows': len(dim_contas),
                'fact_saldos_rows': len(fact_saldos),
                'fact_resgates_rows': len(fact_resgates)
            }
            
            transformed_data = {
                self.config.TABLE_CONTAS: dim_contas,
                self.config.TABLE_SALDOS: fact_saldos,
                self.config.TABLE_RESGATES: fact_resgates
            }
            
            log_success("Transformação concluída para todas as tabelas")
            return transformed_data
            
        except Exception as e:
            log_error("Erro na fase de transformação", str(e))
            raise
    
    def load_phase(self, transformed_data: Dict[str, pd.DataFrame]) -> bool:
        """Fase de carga dos dados"""
        try:
            self.update_progress("Carregando dados no banco", 6)
            
            # Testar conexão antes de carregar
            if not self.loader.test_connection():
                log_error("Falha na conexão com banco de dados")
                return False
            
            # Carregar dados
            load_results = self.loader.load_multiple_dataframes(transformed_data)
            
            # Verificar resultados
            success_count = sum(1 for success in load_results.values() if success)
            total_count = len(load_results)
            
            if success_count == total_count:
                log_success("Todos os dados foram carregados com sucesso")
                
                # Obter estatísticas finais
                stats = self.loader.get_database_stats()
                self.results['load'] = {
                    'tables_loaded': success_count,
                    'total_records': stats.get('total_records', 0),
                    'database_stats': stats
                }
                return True
            else:
                log_error(f"Falha na carga: {success_count}/{total_count} tabelas carregadas")
                return False
                
        except Exception as e:
            log_error("Erro na fase de carga", str(e))
            return False
    
    def run_pipeline(self, saldos_path: str, resgates_path: str) -> Dict[str, Any]:
        """Executa o pipeline ETL completo"""
        try:
            log_info("=== INICIANDO PIPELINE ETL ===")
            self.logger.clear_logs()  # Limpar logs anteriores
            
            # Validar arquivos de entrada
            if not self.validate_input_files(saldos_path, resgates_path):
                return {"success": False, "error": "Validação de arquivos falhou"}
            
            # Fase 1: Extração
            saldos_df, resgates_df = self.extract_phase(saldos_path, resgates_path)
            
            # Fase 2: Transformação
            transformed_data = self.transform_phase(saldos_df, resgates_df)
            
            # Fase 3: Carga
            load_success = self.load_phase(transformed_data)
            
            if not load_success:
                return {"success": False, "error": "Falha na carga dos dados"}
            
            # Finalização
            self.update_progress("Pipeline concluído", 7)
            log_success("=== PIPELINE ETL CONCLUÍDO COM SUCESSO ===")
            
            # Preparar resultado final
            result = {
                "success": True,
                "database_path": self.config.get_database_engine_url(),
                "results": self.results,
                "logs": self.logger.get_logs()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Erro no pipeline ETL: {str(e)}"
            log_critical(error_msg, traceback.format_exc())
            
            return {
                "success": False,
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "logs": self.logger.get_logs()
            }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Retorna o status atual do pipeline"""
        return {
            "current_step": self.current_step,
            "progress": self.progress,
            "total_steps": self.total_steps,
            "progress_percentage": round((self.progress / self.total_steps) * 100, 1),
            "results": self.results
        }
    
    def reset_pipeline(self):
        """Reseta o estado do pipeline"""
        self.current_step = None
        self.progress = 0
        self.results = {}
        self.logger.clear_logs()
        log_info("Pipeline resetado")


# Instância global do pipeline
etl_pipeline = ETLPipeline()


# Função principal para manter compatibilidade
def main(saldos_path: str = None, resgates_path: str = None):
    """
    Função principal adaptada do código original
    """
    if not saldos_path or not resgates_path:
        # Usar caminhos padrão se não fornecidos
        saldos_path = str(config.PROJECT_ROOT / "data_samples" / "base_operacional.csv")
        resgates_path = str(config.PROJECT_ROOT / "data_samples" / "base_resgates.csv")
    
    result = etl_pipeline.run_pipeline(saldos_path, resgates_path)
    
    if result["success"]:
        print(f"Pipeline concluído com sucesso!")
        print(f"Banco de dados: {result['database_path']}")
    else:
        print(f"Pipeline falhou: {result['error']}")
    
    return result


if __name__ == "__main__":
    main()

