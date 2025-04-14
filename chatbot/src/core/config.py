#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuração centralizada da aplicação.
Gerencia carregamento de variáveis de ambiente e settings.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache
from pathlib import Path
from dataclasses import dataclass, field
import dotenv
from src.core.logging import setup_logging


# Carrega variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

# Configura o logger usando o sistema centralizado
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/chatbot.log"),
    console=True,
    json_format=os.getenv("LOG_JSON", "0") == "1",
    user_visible=os.getenv("LOG_USER_VISIBLE", "0") == "1",  # Por padrão, não mostrar logs para o usuário
)

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Classe para armazenar as configurações da aplicação."""
    
    # API keys
    hugging_face_api_key: str
    groq_api_key: str
    
    # Configurações da aplicação
    max_history_length: int = 10
    default_model: str = "google/flan-t5-base"
    default_groq_model: str = "llama3-70b-8192"
    default_huggingface_model: str = "accounts/perplexity/models/r1-1776"
    
    # Processamento de Mídia
    max_audio_size: int = 50 * 1024 * 1024  # 50MB
    max_audio_duration: int = 300  # 5 minutos
    allowed_audio_formats: List[str] = None  # Definido no __post_init__
    whisper_model: str = "whisper-large-v3-turbo"  # Modelo "turbo" da Whisper (mais leve e otimizado)
    whisper_language: str = "pt-BR"  # Português do Brasil como padrão
    
    # Ajustes de performance
    request_timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.5
    
    def __post_init__(self):
        # Inicializa listas e configurações padrão
        if self.allowed_audio_formats is None:
            self.allowed_audio_formats = [
                ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", 
                ".mp4", ".mpeg", ".mpga", ".oga", ".webm"
            ]


@lru_cache()
def get_settings() -> Settings:
    """
    Cria e retorna as configurações da aplicação.
    Utiliza cache para evitar leituras repetidas.
    
    Returns:
        Um objeto Settings com as configurações
    """
    logger.info("Carregando configurações da aplicação")
    
    # Verifica se todas as variáveis necessárias estão definidas
    hugging_face_key = os.getenv("HUGGINGFACE_TOKEN")
    if not hugging_face_key:
        logger.warning("Chave da API Hugging Face não encontrada!")
    
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        logger.warning("Chave da API Groq não encontrada!")
    
    # Cria as configurações
    settings = Settings(
        hugging_face_api_key=hugging_face_key or "",
        groq_api_key=groq_key or "",
        max_history_length=int(os.getenv("MAX_HISTORY_LENGTH", "10")),
        default_model=os.getenv("DEFAULT_MODEL", "google/flan-t5-base"),
        default_groq_model=os.getenv("DEFAULT_GROQ_MODEL", "llama2-70b-4096"),
        default_huggingface_model=os.getenv("DEFAULT_HUGGINGFACE_MODEL", "google/flan-t5-base"),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        backoff_factor=float(os.getenv("BACKOFF_FACTOR", "0.5")),
    )
    
    return settings
