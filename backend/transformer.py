"""
Módulo de Transformação (Transform)
Funções para limpeza, padronização e modelagem dos dados.
"""

import pandas as pd
import re
from typing import Dict, List, Any
from datetime import datetime

from .logger import log_info, log_error, log_success, log_warning, log_debug


class DataTransformer:
    """Classe responsável pelas transformações de dados"""
    
    def __init__(self):
        self.month_map = {
            'JAN': '01', 'JANEIRO': '01',
            'FEV': '02', 'FEVEREIRO': '02',
            'MAR': '03', 'MARÇO': '03', 'MARCO': '03',
            'ABR': '04', 'ABRIL': '04',
            'MAI': '05', 'MAIO': '05',
            'JUN': '06', 'JUNHO': '06',
            'JUL': '07', 'JULHO': '07',
            'AGO': '08', 'AGOSTO': '08',
            'SET': '09', 'SETEMBRO': '09',
            'OUT': '10', 'OUTUBRO': '10',
            'NOV': '11', 'NOVEMBRO': '11',
            'DEZ': '12', 'DEZEMBRO': '12'
        }
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove espaços em branco e caracteres especiais dos nomes das colunas"""
        log_debug("Limpando nomes das colunas")
        original_columns = df.columns.tolist()
        df.columns = df.columns.str.strip()
        
        cleaned_count = sum(1 for orig, clean in zip(original_columns, df.columns) if orig != clean)
        if cleaned_count > 0:
            log_info(f"Limpeza de colunas: {cleaned_count} colunas foram ajustadas")
        
        return df
    
    def clean_monetary_values(self, series: pd.Series) -> pd.Series:
        """Converte uma coluna de string monetária (ex: 'R$ 1.234,56') para float"""
        if series.dtype == 'object':
            log_debug(f"Convertendo valores monetários da coluna: {series.name}")
            
            # Contar valores não nulos antes da conversão
            non_null_before = series.notna().sum()
            
            cleaned_series = (
                series.str.replace("R$", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.strip()
                .replace('', None)  # Substituir strings vazias por None
            )
            
            # Converter para float
            converted_series = pd.to_numeric(cleaned_series, errors='coerce')
            
            # Contar valores não nulos após a conversão
            non_null_after = converted_series.notna().sum()
            
            if non_null_before != non_null_after:
                lost_values = non_null_before - non_null_after
                log_warning(f"Conversão monetária: {lost_values} valores não puderam ser convertidos")
            
            return converted_series
        
        return series
    
    def parse_saldo_date(self, col_name: str) -> str:
        """Extrai e formata a data do nome da coluna de saldo (ex: 'Saldo MARÇO23')"""
        log_debug(f"Parseando data da coluna: {col_name}")
        
        # Padrões mais flexíveis para capturar datas
        patterns = [
            r'(\w+)(\d{2})',  # MARÇO23
            r'(\w+)\s+(\d{2})',  # MARÇO 23
            r'(\w+)/(\d{2})',  # MARÇO/23
            r'(\w+)-(\d{2})',  # MARÇO-23
        ]
        
        col_upper = col_name.upper()
        
        for pattern in patterns:
            match = re.search(pattern, col_upper)
            if match:
                month_str, year_str = match.groups()
                
                # Buscar o mês no mapeamento
                month = None
                for key, value in self.month_map.items():
                    if key in month_str:
                        month = value
                        break
                
                if month:
                    # Assumir que anos de 2 dígitos são 20XX
                    if len(year_str) == 2:
                        year = f"20{year_str}"
                    else:
                        year = year_str
                    
                    date_str = f"{year}-{month}-01"
                    log_debug(f"Data parseada: {col_name} -> {date_str}")
                    return date_str
        
        log_warning(f"Não foi possível parsear a data da coluna: {col_name}")
        return None
    
    def transform_saldos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica todas as transformações na base de saldos"""
        log_info("Iniciando transformação da base de saldos...")
        
        try:
            # Limpeza inicial
            df = self.clean_column_names(df)
            log_info(f"Dados originais: {df.shape[0]} linhas, {df.shape[1]} colunas")
            
            # Identificar colunas de identificação e valor
            id_vars = []
            value_vars = []
            
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['conta', 'parcela']):
                    id_vars.append(col)
                elif any(keyword in col_lower for keyword in ['saldo', 'valor']):
                    value_vars.append(col)
            
            log_info(f"Colunas de identificação: {id_vars}")
            log_info(f"Colunas de valor: {value_vars}")
            
            if not id_vars:
                log_warning("Nenhuma coluna de identificação encontrada, usando todas as colunas não-valor")
                id_vars = [col for col in df.columns if col not in value_vars]
            
            if not value_vars:
                log_error("Nenhuma coluna de valor encontrada")
                raise ValueError("Não foi possível identificar colunas de saldo/valor")
            
            # Transformar de wide para long format
            log_info("Convertendo dados para formato longo (melt)")
            df_melted = df.melt(
                id_vars=id_vars, 
                value_vars=value_vars, 
                var_name='dt_referencia', 
                value_name='vl_saldo_final_mes'
            )
            
            # Remover valores nulos
            rows_before = len(df_melted)
            df_melted.dropna(subset=['vl_saldo_final_mes'], inplace=True)
            rows_after = len(df_melted)
            
            if rows_before != rows_after:
                log_info(f"Removidos {rows_before - rows_after} registros com valores nulos")
            
            # Limpar valores monetários
            df_melted['vl_saldo_final_mes'] = self.clean_monetary_values(df_melted['vl_saldo_final_mes'])
            
            # Parsear datas das colunas
            log_info("Parseando datas das colunas de referência")
            df_melted['dt_referencia'] = df_melted['dt_referencia'].apply(self.parse_saldo_date)
            df_melted['dt_referencia'] = pd.to_datetime(df_melted['dt_referencia'], errors='coerce')
            
            # Remover registros com datas inválidas
            valid_dates = df_melted['dt_referencia'].notna()
            if not valid_dates.all():
                invalid_count = (~valid_dates).sum()
                log_warning(f"Removidos {invalid_count} registros com datas inválidas")
                df_melted = df_melted[valid_dates]
            
            # Padronizar nomes das colunas
            column_mapping = {}
            for col in df_melted.columns:
                col_lower = col.lower()
                if 'conta' in col_lower and 'judicial' in col_lower:
                    column_mapping[col] = 'nr_conta_judicial'
                elif 'parcela' in col_lower:
                    column_mapping[col] = 'nr_parcela'
            
            if column_mapping:
                df_melted.rename(columns=column_mapping, inplace=True)
                log_info(f"Colunas renomeadas: {column_mapping}")
            
            log_success(f"Transformação de saldos concluída: {len(df_melted)} registros finais")
            return df_melted
            
        except Exception as e:
            log_error("Erro durante transformação de saldos", str(e))
            raise
    
    def transform_resgates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica todas as transformações na base de resgates"""
        log_info("Iniciando transformação da base de resgates...")
        
        try:
            # Limpeza inicial
            df = self.clean_column_names(df)
            log_info(f"Dados originais: {df.shape[0]} linhas, {df.shape[1]} colunas")
            
            # Identificar e limpar colunas monetárias
            monetary_patterns = [
                'saldo', 'valor', 'vl_', 'repassado', 'resgatado', 
                'cptl', 'jur', 'cm', 'total'
            ]
            
            monetary_cols = []
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in monetary_patterns):
                    monetary_cols.append(col)
            
            log_info(f"Colunas monetárias identificadas: {monetary_cols}")
            
            for col in monetary_cols:
                if col in df.columns:
                    df[col] = self.clean_monetary_values(df[col])
            
            # Identificar e converter colunas de data
            date_patterns = ['dt_', 'data', 'competencia']
            date_cols = []
            
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in date_patterns):
                    date_cols.append(col)
            
            log_info(f"Colunas de data identificadas: {date_cols}")
            
            for col in date_cols:
                if col in df.columns:
                    log_debug(f"Convertendo coluna de data: {col}")
                    
                    # Tentar diferentes formatos de data
                    if 'competencia' in col.lower():
                        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                    else:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    # Contar conversões bem-sucedidas
                    valid_dates = df[col].notna().sum()
                    total_rows = len(df)
                    log_info(f"Coluna {col}: {valid_dates}/{total_rows} datas válidas")
            
            # Padronizar nomes das colunas principais
            column_mapping = {
                'Número da Conta Judicial': 'nr_conta_judicial',
                'Número da Parcela': 'nr_parcela',
                'Número do Convênio de Repasse': 'cd_convenio_repasse'
            }
            
            # Buscar colunas similares caso os nomes exatos não existam
            for old_name, new_name in column_mapping.copy().items():
                if old_name not in df.columns:
                    # Buscar coluna similar
                    for col in df.columns:
                        col_lower = col.lower()
                        old_lower = old_name.lower()
                        
                        if 'conta' in old_lower and 'judicial' in old_lower:
                            if 'conta' in col_lower and 'judicial' in col_lower:
                                column_mapping[col] = new_name
                                del column_mapping[old_name]
                                break
                        elif 'parcela' in old_lower:
                            if 'parcela' in col_lower:
                                column_mapping[col] = new_name
                                del column_mapping[old_name]
                                break
                        elif 'convenio' in old_lower:
                            if 'convenio' in col_lower or 'repasse' in col_lower:
                                column_mapping[col] = new_name
                                del column_mapping[old_name]
                                break
            
            # Aplicar renomeação
            existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
            if existing_mappings:
                df.rename(columns=existing_mappings, inplace=True)
                log_info(f"Colunas renomeadas: {existing_mappings}")
            
            log_success(f"Transformação de resgates concluída: {len(df)} registros")
            return df
            
        except Exception as e:
            log_error("Erro durante transformação de resgates", str(e))
            raise
    
    def create_dimension_contas(self, saldos_df: pd.DataFrame, resgates_df: pd.DataFrame) -> pd.DataFrame:
        """Cria a tabela de dimensão 'Contas' a partir das duas bases"""
        log_info("Criando dimensão 'Contas'...")
        
        try:
            # Identificar colunas de conta e parcela em ambos os DataFrames
            conta_cols = ['nr_conta_judicial']
            parcela_cols = ['nr_parcela']
            convenio_cols = ['cd_convenio_repasse']
            
            # Extrair contas únicas dos saldos
            saldos_cols = [col for col in conta_cols + parcela_cols if col in saldos_df.columns]
            if saldos_cols:
                contas_saldos = saldos_df[saldos_cols].drop_duplicates()
                log_info(f"Contas únicas dos saldos: {len(contas_saldos)}")
            else:
                log_warning("Nenhuma coluna de conta/parcela encontrada nos saldos")
                contas_saldos = pd.DataFrame()
            
            # Extrair contas únicas dos resgates
            resgates_cols = [col for col in conta_cols + parcela_cols + convenio_cols if col in resgates_df.columns]
            if resgates_cols:
                contas_resgates = resgates_df[resgates_cols].drop_duplicates()
                log_info(f"Contas únicas dos resgates: {len(contas_resgates)}")
            else:
                log_warning("Nenhuma coluna de conta/parcela encontrada nos resgates")
                contas_resgates = pd.DataFrame()
            
            # Fazer merge das contas
            if not contas_saldos.empty and not contas_resgates.empty:
                merge_cols = [col for col in conta_cols + parcela_cols if col in contas_saldos.columns and col in contas_resgates.columns]
                if merge_cols:
                    dim_contas = pd.merge(contas_saldos, contas_resgates, on=merge_cols, how='outer')
                else:
                    # Se não há colunas em comum, concatenar
                    dim_contas = pd.concat([contas_saldos, contas_resgates], ignore_index=True).drop_duplicates()
            elif not contas_saldos.empty:
                dim_contas = contas_saldos
            elif not contas_resgates.empty:
                dim_contas = contas_resgates
            else:
                log_error("Não foi possível criar dimensão de contas - nenhum dado válido encontrado")
                raise ValueError("Dados insuficientes para criar dimensão de contas")
            
            # Adicionar ID sequencial
            dim_contas.reset_index(drop=True, inplace=True)
            dim_contas.insert(0, 'id_conta', range(1, len(dim_contas) + 1))
            
            log_success(f"Dimensão 'Contas' criada com {len(dim_contas)} registros únicos")
            return dim_contas
            
        except Exception as e:
            log_error("Erro ao criar dimensão de contas", str(e))
            raise
    
    def add_foreign_keys(self, fact_df: pd.DataFrame, dim_contas: pd.DataFrame) -> pd.DataFrame:
        """Adiciona chaves estrangeiras às tabelas de fatos"""
        try:
            # Identificar colunas de junção
            join_cols = []
            for col in ['nr_conta_judicial', 'nr_parcela']:
                if col in fact_df.columns and col in dim_contas.columns:
                    join_cols.append(col)
            
            if not join_cols:
                log_warning("Nenhuma coluna de junção encontrada para adicionar chaves estrangeiras")
                return fact_df
            
            log_info(f"Adicionando chaves estrangeiras usando colunas: {join_cols}")
            
            # Fazer merge para adicionar id_conta
            result_df = pd.merge(fact_df, dim_contas[join_cols + ['id_conta']], on=join_cols, how='left')
            
            # Verificar se todas as linhas receberam id_conta
            missing_ids = result_df['id_conta'].isna().sum()
            if missing_ids > 0:
                log_warning(f"{missing_ids} registros não puderam ser associados a uma conta")
            
            return result_df
            
        except Exception as e:
            log_error("Erro ao adicionar chaves estrangeiras", str(e))
            raise


# Instância global do transformador
data_transformer = DataTransformer()


# Funções de conveniência para manter compatibilidade com código original
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    return data_transformer.clean_column_names(df)

def clean_monetary_values(series: pd.Series) -> pd.Series:
    return data_transformer.clean_monetary_values(series)

def parse_saldo_date(col_name: str) -> str:
    return data_transformer.parse_saldo_date(col_name)

def transform_saldos(df: pd.DataFrame) -> pd.DataFrame:
    return data_transformer.transform_saldos(df)

def transform_resgates(df: pd.DataFrame) -> pd.DataFrame:
    return data_transformer.transform_resgates(df)

def create_dimension_contas(saldos_df: pd.DataFrame, resgates_df: pd.DataFrame) -> pd.DataFrame:
    return data_transformer.create_dimension_contas(saldos_df, resgates_df)

