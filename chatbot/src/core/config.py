#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo de configurações para o chatbot.
Carrega valores de .env e define padrões.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from functools import lru_cache
from pydantic import validator, Field
from pydantic_settings import BaseSettings

# Carregar variáveis de ambiente de .env
from dotenv import load_dotenv

# Encontra o diretório raiz do projeto (onde está o .env)
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"

# Carrega .env se existir
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Configurações do aplicativo carregadas do .env"""

    # Diretórios
    root_dir: Path = ROOT_DIR
    temp_dir: Path = ROOT_DIR / "temp"
    log_dir: Path = ROOT_DIR / "logs"
    data_dir: Path = ROOT_DIR / "data"
    docs_dir: Path = ROOT_DIR / "docs"

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/chatbot.log")
    log_user_visible: bool = os.getenv("LOG_USER_VISIBLE", "0") == "1"

    # Chaves de API
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    hugging_face_api_key: str = os.getenv("HUGGINGFACE_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Configurações de API
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    backoff_factor: float = float(os.getenv("BACKOFF_FACTOR", "0.5"))

    # Modelos padrão
    default_groq_model: str = os.getenv("DEFAULT_GROQ_MODEL", "llama3-70b-8192")
    default_openai_model: str = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o")
    default_huggingface_model: str = os.getenv("DEFAULT_HUGGINGFACE_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    default_embedding_model: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Configurações de conversação
    max_history_length: int = int(os.getenv("MAX_HISTORY_LENGTH", "10"))
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "8000"))

    # Configurações RAG
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "chatbot_knowledge")

    # Configurações de áudio
    max_audio_size: int = int(os.getenv("MAX_AUDIO_SIZE", str(50 * 1024 * 1024)))  # 50MB
    max_audio_duration: int = int(os.getenv("MAX_AUDIO_DURATION", "600"))  # 10 min
    whisper_model: str = os.getenv("WHISPER_MODEL", "whisper-large-v3")
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "pt-BR")
    allowed_audio_formats: List[str] = [
        ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", 
        ".mp4", ".mpeg", ".mpga", ".oga", ".webm"
    ]

    # MCP Server Commands
    media_server_cmd: str = os.getenv("MEDIA_SERVER_CMD", "")

    @validator("temp_dir", "log_dir", "data_dir", pre=True)
    def create_dirs(cls, v):
        """Cria os diretórios se não existirem"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    class Config:
        env_file = ENV_FILE
        extra = "allow"  # Permitir variáveis extras do .env


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna uma instância de configurações com cache para reutilização.

    Returns:
        Objeto Settings com as configurações
    """
    return Settings()


def setup_logging():
    """Configura o logging da aplicação"""
    settings = get_settings()

    # Cria o diretório de logs se não existir
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configura nível de log baseado na configuração
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configura formato de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configuração básica de logging
    handlers = []

    # Handler para arquivo
    file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    handlers.append(file_handler)

    # Handler para console (opcional)
    if settings.log_user_visible:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(console_handler)

    # Configura o logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
    )

    # Define nível para alguns loggers de bibliotecas verbosas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
