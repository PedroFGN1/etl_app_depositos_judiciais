"""
Interface Eel para comunicação entre Frontend e Backend
Expõe funções Python para o frontend via Eel.
"""

import eel
import os
import shutil
from pathlib import Path
from typing import Dict, Any
import tempfile
import traceback

from .config import config
from .logger import etl_logger, log_info, log_error, log_success, log_warning
from .etl_pipeline import etl_pipeline


class EelInterface:
    """Classe que gerencia a interface Eel"""
    
    def __init__(self):
        self.temp_dir = None
        self.setup_temp_directory()
    
    def setup_temp_directory(self):
        """Cria diretório temporário para uploads"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="etl_uploads_"))
        log_info(f"Diretório temporário criado: {self.temp_dir}")
    
    def cleanup_temp_directory(self):
        """Remove diretório temporário"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            log_info("Diretório temporário removido")


# Instância global da interface
eel_interface = EelInterface()


# Funções expostas para o frontend
@eel.expose
def start_etl_process(saldos_filename: str, resgates_filename: str) -> Dict[str, Any]:
    """
    Inicia o processamento ETL com os arquivos fornecidos
    """
    try:
        log_info("Recebida solicitação de processamento ETL")
        log_info(f"Arquivo de saldos: {saldos_filename}")
        log_info(f"Arquivo de resgates: {resgates_filename}")
        
        # Verificar se os arquivos existem no diretório de uploads
        saldos_path = config.UPLOAD_FOLDER / saldos_filename
        resgates_path = config.UPLOAD_FOLDER / resgates_filename
        
        if not saldos_path.exists():
            error_msg = f"Arquivo de saldos não encontrado: {saldos_filename}"
            log_error(error_msg)
            return {"success": False, "error": error_msg}
        
        if not resgates_path.exists():
            error_msg = f"Arquivo de resgates não encontrado: {resgates_filename}"
            log_error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Executar pipeline ETL
        result = etl_pipeline.run_pipeline(str(saldos_path), str(resgates_path))
        
        return result
        
    except Exception as e:
        error_msg = f"Erro no processamento ETL: {str(e)}"
        log_error(error_msg, traceback.format_exc())
        return {
            "success": False,
            "error": error_msg,
            "traceback": traceback.format_exc()
        }


@eel.expose
def upload_file(filename: str, file_data: str) -> Dict[str, Any]:
    """
    Recebe arquivo do frontend e salva no diretório de uploads
    """
    try:
        import base64
        
        log_info(f"Recebendo upload do arquivo: {filename}")
        
        # Decodificar dados do arquivo
        file_bytes = base64.b64decode(file_data)
        
        # Salvar arquivo
        file_path = config.UPLOAD_FOLDER / filename
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        file_size = len(file_bytes)
        log_success(f"Arquivo salvo: {filename} ({file_size} bytes)")
        
        return {
            "success": True,
            "filename": filename,
            "size": file_size,
            "path": str(file_path)
        }
        
    except Exception as e:
        error_msg = f"Erro no upload do arquivo {filename}: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_pipeline_status() -> Dict[str, Any]:
    """
    Retorna o status atual do pipeline ETL
    """
    try:
        return etl_pipeline.get_pipeline_status()
    except Exception as e:
        log_error(f"Erro ao obter status do pipeline: {str(e)}")
        return {"error": str(e)}


@eel.expose
def reset_pipeline() -> Dict[str, Any]:
    """
    Reseta o pipeline ETL
    """
    try:
        etl_pipeline.reset_pipeline()
        return {"success": True, "message": "Pipeline resetado"}
    except Exception as e:
        error_msg = f"Erro ao resetar pipeline: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_logs() -> Dict[str, Any]:
    """
    Retorna todos os logs do sistema
    """
    try:
        return {
            "success": True,
            "logs": etl_logger.get_logs()
        }
    except Exception as e:
        error_msg = f"Erro ao obter logs: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def clear_logs() -> Dict[str, Any]:
    """
    Limpa todos os logs do sistema
    """
    try:
        etl_logger.clear_logs()
        return {"success": True, "message": "Logs limpos"}
    except Exception as e:
        error_msg = f"Erro ao limpar logs: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def update_database_config(db_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Atualiza a configuração do banco de dados
    """
    try:
        log_info("Atualizando configuração do banco de dados")
        
        db_type = db_config.get('type', 'sqlite')
        config.set_database_config(db_type, **{k: v for k, v in db_config.items() if k != 'type'})
        
        # Testar conexão
        from .loader import DataLoader
        test_loader = DataLoader(config.database)
        
        if test_loader.test_connection():
            log_success(f"Configuração de banco atualizada: {db_type}")
            return {"success": True, "message": "Configuração atualizada e testada com sucesso"}
        else:
            return {"success": False, "error": "Falha no teste de conexão"}
            
    except Exception as e:
        error_msg = f"Erro ao atualizar configuração do banco: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_database_config() -> Dict[str, Any]:
    """
    Retorna a configuração atual do banco de dados
    """
    try:
        return {
            "success": True,
            "config": {
                "type": config.database.db_type,
                **config.database.config
            }
        }
    except Exception as e:
        error_msg = f"Erro ao obter configuração do banco: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_database_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do banco de dados
    """
    try:
        from .loader import data_loader
        stats = data_loader.get_database_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        error_msg = f"Erro ao obter estatísticas do banco: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def list_uploaded_files() -> Dict[str, Any]:
    """
    Lista arquivos no diretório de uploads
    """
    try:
        files = []
        upload_folder = config.UPLOAD_FOLDER
        
        if upload_folder.exists():
            for file_path in upload_folder.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "extension": file_path.suffix.lower()
                    })
        
        return {"success": True, "files": files}
        
    except Exception as e:
        error_msg = f"Erro ao listar arquivos: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def delete_uploaded_file(filename: str) -> Dict[str, Any]:
    """
    Remove um arquivo do diretório de uploads
    """
    try:
        file_path = config.UPLOAD_FOLDER / filename
        
        if file_path.exists():
            file_path.unlink()
            log_success(f"Arquivo removido: {filename}")
            return {"success": True, "message": f"Arquivo {filename} removido"}
        else:
            return {"success": False, "error": "Arquivo não encontrado"}
            
    except Exception as e:
        error_msg = f"Erro ao remover arquivo {filename}: {str(e)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_system_info() -> Dict[str, Any]:
    """
    Retorna informações do sistema
    """
    try:
        import platform
        import psutil
        
        return {
            "success": True,
            "info": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('.').free
            }
        }
    except Exception as e:
        # psutil pode não estar disponível
        return {
            "success": True,
            "info": {
                "platform": "Unknown",
                "python_version": "Unknown",
                "note": "Informações detalhadas não disponíveis"
            }
        }


def start_eel_app():
    """
    Inicia a aplicação Eel
    """
    try:
        # Configurar Eel
        frontend_path = str(config.FRONTEND_PATH)
        
        log_info(f"Iniciando aplicação Eel...")
        log_info(f"Frontend path: {frontend_path}")
        log_info(f"Host: {config.EEL_HOST}:{config.EEL_PORT}")
        
        # Inicializar Eel
        eel.init(frontend_path)
        
        # Configurações da janela/servidor
        eel_options = {
            'host': config.EEL_HOST,
            'port': config.EEL_PORT,
            'mode': 'default',  # Usar navegador padrão
            'close_callback': cleanup_on_exit
        }
        
        log_success("Aplicação ETL iniciada com sucesso!")
        log_info(f"Acesse: http://{config.EEL_HOST}:{config.EEL_PORT}")
        
        # Iniciar aplicação
        eel.start('index.html', **eel_options)
        
    except Exception as e:
        log_error(f"Erro ao iniciar aplicação Eel: {str(e)}")
        raise


def cleanup_on_exit(route, websockets):
    """
    Função chamada quando a aplicação é fechada
    """
    log_info("Encerrando aplicação...")
    eel_interface.cleanup_temp_directory()
    log_info("Aplicação encerrada")


if __name__ == "__main__":
    start_eel_app()

