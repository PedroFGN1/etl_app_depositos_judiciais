"""
Módulo de Extração (Extract)
Funções responsáveis por ler os dados das fontes originais.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any
import os

from .logger import log_info, log_error, log_success, log_warning


class DataExtractor:
    """Classe responsável pela extração de dados de diferentes fontes"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls']
    
    def validate_file(self, file_path: Path) -> bool:
        """Valida se o arquivo existe e tem formato suportado"""
        if not file_path.exists():
            log_error(f"Arquivo não encontrado: {file_path}")
            return False
        
        if file_path.suffix.lower() not in self.supported_formats:
            log_error(f"Formato não suportado: {file_path.suffix}. Formatos aceitos: {self.supported_formats}")
            return False
        
        return True
    
    def read_csv_file(self, file_path: Path, delimiter: str = ';', encoding: str = 'utf-8') -> pd.DataFrame:
        """Lê arquivo CSV com configurações flexíveis"""
        try:
            log_info(f"Lendo arquivo CSV: {file_path.name}")
            
            # Tentar diferentes encodings se o padrão falhar
            encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, delimiter=delimiter, encoding=enc)
                    log_success(f"Arquivo CSV lido com sucesso usando encoding {enc}")
                    log_info(f"Dimensões: {df.shape[0]} linhas, {df.shape[1]} colunas")
                    return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    if enc == encodings_to_try[-1]:  # Último encoding
                        raise e
                    continue
            
            raise ValueError("Não foi possível ler o arquivo com nenhum encoding testado")
            
        except Exception as e:
            log_error(f"Erro ao ler arquivo CSV {file_path.name}", str(e))
            raise
    
    def read_excel_file(self, file_path: Path, sheet_name: str = None) -> pd.DataFrame:
        """Lê arquivo Excel (xlsx/xls)"""
        try:
            log_info(f"Lendo arquivo Excel: {file_path.name}")
            
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                log_info(f"Planilha '{sheet_name}' lida")
            else:
                df = pd.read_excel(file_path)
                log_info("Primeira planilha lida")
            
            log_success(f"Arquivo Excel lido com sucesso")
            log_info(f"Dimensões: {df.shape[0]} linhas, {df.shape[1]} colunas")
            return df
            
        except Exception as e:
            log_error(f"Erro ao ler arquivo Excel {file_path.name}", str(e))
            raise
    
    def extract_file(self, file_path: Path, **kwargs) -> pd.DataFrame:
        """Extrai dados de um arquivo baseado na extensão"""
        if not self.validate_file(file_path):
            raise FileNotFoundError(f"Arquivo inválido: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.csv':
            return self.read_csv_file(file_path, **kwargs)
        elif file_extension in ['.xlsx', '.xls']:
            return self.read_excel_file(file_path, **kwargs)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {file_extension}")
    
    def extract_multiple_files(self, file_paths: List[Path], **kwargs) -> Dict[str, pd.DataFrame]:
        """Extrai dados de múltiplos arquivos"""
        log_info(f"Iniciando extração de {len(file_paths)} arquivos")
        
        dataframes = {}
        errors = []
        
        for file_path in file_paths:
            try:
                df = self.extract_file(file_path, **kwargs)
                dataframes[file_path.stem] = df
                log_success(f"Arquivo {file_path.name} extraído com sucesso")
            except Exception as e:
                error_msg = f"Erro ao extrair {file_path.name}: {str(e)}"
                log_error(error_msg)
                errors.append(error_msg)
        
        if errors:
            log_warning(f"Extração concluída com {len(errors)} erros")
        else:
            log_success("Todos os arquivos foram extraídos com sucesso")
        
        return dataframes
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Retorna informações sobre um arquivo"""
        if not file_path.exists():
            return {"error": "Arquivo não encontrado"}
        
        try:
            stat = file_path.stat()
            info = {
                "name": file_path.name,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": stat.st_mtime,
                "extension": file_path.suffix.lower(),
                "supported": file_path.suffix.lower() in self.supported_formats
            }
            
            # Tentar obter informações básicas do conteúdo
            if info["supported"]:
                try:
                    if file_path.suffix.lower() == '.csv':
                        # Ler apenas as primeiras linhas para obter info
                        sample_df = pd.read_csv(file_path, nrows=5, delimiter=';')
                        info["columns"] = list(sample_df.columns)
                        info["sample_data"] = sample_df.head(3).to_dict('records')
                    elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                        sample_df = pd.read_excel(file_path, nrows=5)
                        info["columns"] = list(sample_df.columns)
                        info["sample_data"] = sample_df.head(3).to_dict('records')
                except:
                    info["columns"] = []
                    info["sample_data"] = []
            
            return info
            
        except Exception as e:
            return {"error": str(e)}


# Instância global do extrator
data_extractor = DataExtractor()


# Funções de conveniência para uso direto
def extract_data(saldos_path: Path, resgates_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Função original adaptada para usar a nova classe
    Lê os arquivos CSV de saldos e resgates e os retorna como DataFrames do Pandas.
    """
    try:
        log_info("Iniciando extração dos dados...")
        
        saldos_df = data_extractor.extract_file(saldos_path, delimiter=';')
        resgates_df = data_extractor.extract_file(resgates_path, delimiter=';')
        
        log_success("Extração concluída com sucesso.")
        return saldos_df, resgates_df
        
    except Exception as e:
        log_error("Erro durante a extração dos dados", str(e))
        raise

