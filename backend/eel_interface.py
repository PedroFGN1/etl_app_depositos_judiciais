"""
Interface Eel para comunicacao entre Frontend e Backend.
Expoe funcoes Python para o frontend via Eel.
"""

from __future__ import annotations

import base64
import shutil
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import eel

from .config import config
from .etl_pipeline import ETLPipeline, create_pipeline
from .logger import etl_logger, log_error, log_info, log_success


class EelInterface:
    """Classe que gerencia uploads temporarios e o pipeline atual."""

    def __init__(self) -> None:
        self.temp_dir: Optional[Path] = None
        self.current_pipeline: Optional[ETLPipeline] = None

    def setup_temp_directory(self) -> Path:
        """Cria um diretorio temporario para uma execucao."""
        self.cleanup_temp_directory()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="etl_extrato_pdf_"))
        log_info(f"Diretorio temporario criado: {self.temp_dir}")
        return self.temp_dir

    def cleanup_temp_directory(self) -> None:
        """Remove o diretorio temporario atual."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            log_info("Diretorio temporario removido")
        self.temp_dir = None

    def resolve_uploaded_file(self, filename: str) -> Path:
        """Retorna o caminho de um arquivo salvo no temporario atual."""
        if not self.temp_dir:
            raise FileNotFoundError("Nenhum diretorio temporario ativo")

        file_path = self.temp_dir / Path(filename).name
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado no temporario: {filename}")
        return file_path


eel_interface = EelInterface()


@eel.expose
def start_etl_process(pdf_filename: str) -> Dict[str, Any]:
    """
    Inicia o processamento ETL com um unico PDF de extrato.
    """
    try:
        log_info("Recebida solicitacao de processamento ETL do extrato")
        log_info(f"Arquivo PDF informado: {pdf_filename}")

        pdf_path = eel_interface.resolve_uploaded_file(pdf_filename)
        eel_interface.current_pipeline = create_pipeline()
        result = eel_interface.current_pipeline.run_pipeline(str(pdf_path))
        return result

    except Exception as exc:
        error_msg = f"Erro no processamento ETL: {str(exc)}"
        log_error(error_msg, traceback.format_exc())
        return {
            "success": False,
            "error": error_msg,
            "traceback": traceback.format_exc(),
        }
    finally:
        eel_interface.cleanup_temp_directory()


@eel.expose
def upload_file(filename: str, file_data: str) -> Dict[str, Any]:
    """
    Recebe um PDF do frontend e salva em diretorio temporario.
    """
    try:
        safe_name = Path(filename).name
        if Path(safe_name).suffix.lower() != ".pdf":
            error_msg = "Formato de arquivo nao suportado. Envie um PDF."
            log_error(error_msg)
            return {"success": False, "error": error_msg}

        temp_dir = eel_interface.setup_temp_directory()
        file_bytes = base64.b64decode(file_data)
        file_path = temp_dir / safe_name

        with open(file_path, "wb") as file_obj:
            file_obj.write(file_bytes)

        log_success(f"Arquivo PDF salvo temporariamente: {safe_name}")
        return {
            "success": True,
            "filename": safe_name,
            "size": len(file_bytes),
            "path": str(file_path),
        }

    except Exception as exc:
        error_msg = f"Erro no upload do arquivo {filename}: {str(exc)}"
        log_error(error_msg)
        eel_interface.cleanup_temp_directory()
        return {"success": False, "error": error_msg}


@eel.expose
def get_pipeline_status() -> Dict[str, Any]:
    """
    Retorna o status atual do pipeline ETL.
    """
    try:
        if eel_interface.current_pipeline is None:
            return {
                "current_step": None,
                "progress": 0,
                "total_steps": 0,
                "progress_percentage": 0,
                "results": {},
            }
        return eel_interface.current_pipeline.get_pipeline_status()
    except Exception as exc:
        log_error(f"Erro ao obter status do pipeline: {str(exc)}")
        return {"error": str(exc)}


@eel.expose
def reset_pipeline() -> Dict[str, Any]:
    """
    Reseta o pipeline atual e limpa o diretorio temporario.
    """
    try:
        if eel_interface.current_pipeline is not None:
            eel_interface.current_pipeline.reset_pipeline()
        eel_interface.current_pipeline = None
        eel_interface.cleanup_temp_directory()
        return {"success": True, "message": "Pipeline resetado"}
    except Exception as exc:
        error_msg = f"Erro ao resetar pipeline: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_logs() -> Dict[str, Any]:
    """
    Retorna todos os logs do sistema.
    """
    try:
        return {"success": True, "logs": etl_logger.get_logs()}
    except Exception as exc:
        error_msg = f"Erro ao obter logs: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def clear_logs() -> Dict[str, Any]:
    """
    Limpa todos os logs do sistema.
    """
    try:
        etl_logger.clear_logs()
        return {"success": True, "message": "Logs limpos"}
    except Exception as exc:
        error_msg = f"Erro ao limpar logs: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def update_database_config(db_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Atualiza a configuracao do banco de dados.
    """
    try:
        log_info("Atualizando configuracao do banco de dados")

        db_type = db_config.get("type", "sqlite")
        config.set_database_config(db_type, **{k: v for k, v in db_config.items() if k != "type"})

        from .loader import DataLoader

        test_loader = DataLoader(config.database)
        if test_loader.test_connection():
            log_success(f"Configuracao de banco atualizada: {db_type}")
            return {"success": True, "message": "Configuracao atualizada e testada com sucesso"}
        return {"success": False, "error": "Falha no teste de conexao"}

    except Exception as exc:
        error_msg = f"Erro ao atualizar configuracao do banco: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_database_config() -> Dict[str, Any]:
    """
    Retorna a configuracao atual do banco de dados.
    """
    try:
        return {
            "success": True,
            "config": {"type": config.database.db_type, **config.database.config},
        }
    except Exception as exc:
        error_msg = f"Erro ao obter configuracao do banco: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_database_stats() -> Dict[str, Any]:
    """
    Retorna estatisticas do banco de dados.
    """
    try:
        from .loader import data_loader

        stats = data_loader.get_database_stats()
        return {"success": True, "stats": stats}
    except Exception as exc:
        error_msg = f"Erro ao obter estatisticas do banco: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def list_uploaded_files() -> Dict[str, Any]:
    """
    Lista arquivos no diretorio temporario atual.
    """
    try:
        files = []
        if eel_interface.temp_dir and eel_interface.temp_dir.exists():
            for file_path in eel_interface.temp_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append(
                        {
                            "name": file_path.name,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "extension": file_path.suffix.lower(),
                        }
                    )
        return {"success": True, "files": files}
    except Exception as exc:
        error_msg = f"Erro ao listar arquivos: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def delete_uploaded_file(filename: str) -> Dict[str, Any]:
    """
    Remove um arquivo do diretorio temporario atual.
    """
    try:
        file_path = eel_interface.resolve_uploaded_file(filename)
        file_path.unlink()
        log_success(f"Arquivo removido: {filename}")
        return {"success": True, "message": f"Arquivo {filename} removido"}
    except Exception as exc:
        error_msg = f"Erro ao remover arquivo {filename}: {str(exc)}"
        log_error(error_msg)
        return {"success": False, "error": error_msg}


@eel.expose
def get_system_info() -> Dict[str, Any]:
    """
    Retorna informacoes do sistema.
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
                "disk_usage": psutil.disk_usage(".").free,
            },
        }
    except Exception:
        return {
            "success": True,
            "info": {
                "platform": "Unknown",
                "python_version": "Unknown",
                "note": "Informacoes detalhadas nao disponiveis",
            },
        }


def start_eel_app() -> None:
    """
    Inicia a aplicacao Eel.
    """
    try:
        frontend_path = str(config.FRONTEND_PATH)

        log_info("Iniciando aplicacao Eel...")
        log_info(f"Frontend path: {frontend_path}")
        log_info(f"Host: {config.EEL_HOST}:{config.EEL_PORT}")

        eel.init(frontend_path)

        eel_options = {
            "host": config.EEL_HOST,
            "port": config.EEL_PORT,
            "mode": "default",
            "close_callback": cleanup_on_exit,
        }

        log_success("Aplicacao ETL iniciada com sucesso!")
        log_info(f"Acesse: http://{config.EEL_HOST}:{config.EEL_PORT}")
        eel.start("index.html", **eel_options)

    except Exception as exc:
        log_error(f"Erro ao iniciar aplicacao Eel: {str(exc)}")
        raise


def cleanup_on_exit(route, websockets) -> None:
    """
    Funcao chamada quando a aplicacao e fechada.
    """
    log_info("Encerrando aplicacao...")
    eel_interface.cleanup_temp_directory()
    log_info("Aplicacao encerrada")
