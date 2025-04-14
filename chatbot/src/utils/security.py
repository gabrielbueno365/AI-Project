#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilitários de segurança para validação de arquivos e entradas.
Protege contra uploads maliciosos e outras ameaças comuns.
Suporta conversão automática de formatos compatíveis.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Union, List, Tuple, Optional
import mimetypes

logger = logging.getLogger(__name__)

# Lista de tipos MIME permitidos por categoria
ALLOWED_MIME_TYPES = {
    "audio": [
        # Formatos de áudio padrão
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/flac", 
        "audio/x-m4a", "audio/aac", "audio/webm", "video/mp4",
        "audio/mp4", "audio/mpeg", "audio/mpga", "audio/oga",
        # Formatos adicionais que podem ser convertidos
        "audio/x-wav", "audio/wave", "audio/x-pn-wav", "audio/vnd.wave", 
        "audio/x-ms-wma", "audio/x-aiff", "audio/aiff", "audio/3gpp", 
        "audio/amr", "audio/x-hx-aac-adts", "audio/x-midi", "audio/midi",
        "audio/x-mid", "audio/mid", "audio/opus", "audio/vorbis",
        "audio/x-realaudio", "audio/basic", "audio/x-gsm"
    ],
    "video": [
        "video/mp4", "video/webm", "video/ogg", "video/x-msvideo", 
        "video/quicktime", "video/x-matroska", "video/mpeg", "video/avi",
        "video/x-ms-wmv", "video/3gpp", "video/x-flv", "video/x-ms-asf"
    ],
    "document": [
        "application/pdf", "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain", "text/csv", "text/markdown"
    ],
    "image": [
        "image/jpeg", "image/png", "image/gif", "image/webp", 
        "image/svg+xml", "image/bmp", "image/tiff"
    ]
}

# Tamanhos máximos por tipo (em bytes)
MAX_SIZES = {
    "audio": 50 * 1024 * 1024,  # 50MB
    "video": 100 * 1024 * 1024,  # 100MB
    "document": 10 * 1024 * 1024,  # 10MB
    "image": 5 * 1024 * 1024    # 5MB
}

# Extensões de arquivo permitidas por categoria
ALLOWED_EXTENSIONS = {
    "audio": [
        # Formatos padrão
        ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", 
        ".mp4", ".mpeg", ".mpga", ".oga", ".webm",
        # Formatos convertíveis
        ".wma", ".aiff", ".aif", ".3gp", ".amr", ".m4b", ".ra", ".rm", 
        ".vox", ".raw", ".au", ".dct", ".gsm", ".m4p", ".mid", ".midi", ".opus"
    ],
    "video": [
        ".mp4", ".webm", ".ogg", ".avi", ".mov", ".mkv", ".wmv", ".flv",
        ".3gp", ".mpeg", ".mpg", ".m4v", ".ts", ".asf"
    ],
    "document": [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv", ".md", 
        ".rtf", ".odt", ".ods"
    ],
    "image": [
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".tif"
    ]
}


async def validate_file_safety(
    file_path: Union[str, Path], 
    file_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Verifica se um arquivo é seguro para processamento.
    Para áudio e vídeo, permite formatos que podem ser convertidos automaticamente.
    
    Args:
        file_path: Caminho para o arquivo
        file_type: Tipo do arquivo ('audio', 'video', 'document', 'image')
        
    Returns:
        Tupla (is_safe, reason) indicando se o arquivo é seguro e o motivo se não for
    """
    path = Path(file_path)
    
    # Verifica se o arquivo existe
    if not path.exists():
        return False, f"Arquivo não encontrado: {path}"
    
    # Verifica o tamanho
    file_size = path.stat().st_size
    max_size = MAX_SIZES.get(file_type, 1 * 1024 * 1024)  # 1MB padrão
    if file_size > max_size:
        return False, f"Arquivo muito grande: {file_size} bytes (máximo: {max_size} bytes)"
    
    # Verifica a extensão do arquivo
    file_extension = path.suffix.lower()
    allowed_extensions = ALLOWED_EXTENSIONS.get(file_type, [])
    
    if file_extension not in allowed_extensions:
        # Podemos aceitar se for áudio ou vídeo (porque implementamos conversão automática)
        if file_type in ["audio", "video"]:
            logger.warning(f"Extensão não padrão detectada: {file_extension}. Tentaremos converter.")
        else:
            return False, f"Extensão de arquivo não permitida: {file_extension}"
    
    # Verifica o tipo MIME usando mimetypes em vez de python-magic
    try:
        mime_type, _ = mimetypes.guess_type(str(path))
        
        # Se não conseguir detectar, baseia-se na extensão
        if mime_type is None:
            # Faz uma conversão básica de extensão para mime type
            if file_extension in [".mp3"]:
                mime_type = "audio/mpeg"
            elif file_extension in [".wav"]:
                mime_type = "audio/wav"
            elif file_extension in [".ogg"]:
                mime_type = "audio/ogg"
            elif file_extension in [".m4a"]:
                mime_type = "audio/x-m4a"
            elif file_extension in [".mp4"]:
                mime_type = "video/mp4"
            elif file_extension in [".avi"]:
                mime_type = "video/x-msvideo"
            elif file_extension in [".mov"]:
                mime_type = "video/quicktime"
            elif file_extension in [".mkv"]:
                mime_type = "video/x-matroska"
            else:
                # Se não conseguir mapear, assume com base no tipo solicitado
                mime_type = f"{file_type}/unknown"
        
        allowed_types = ALLOWED_MIME_TYPES.get(file_type, [])
        
        # Para áudio e vídeo, somos mais permissivos devido à conversão automática
        if mime_type not in allowed_types:
            # Verificação mais flexível para áudio e vídeo
            if file_type == "audio" and (mime_type.startswith("audio/") or 
                                         mime_type in ["application/octet-stream"]):
                logger.warning(f"MIME type não padrão detectado: {mime_type}. Tentaremos converter.")
            elif file_type == "video" and (mime_type.startswith("video/") or 
                                          mime_type in ["application/octet-stream"]):
                logger.warning(f"MIME type não padrão detectado: {mime_type}. Tentaremos converter.")
            else:
                return False, f"Tipo MIME não permitido: {mime_type}"
    except Exception as e:
        logger.error(f"Erro ao verificar MIME type: {str(e)}")
        # No caso de erro, confiar na extensão se for permitida
        if file_extension in allowed_extensions:
            logger.warning(f"Erro na verificação de MIME type, mas extensão é permitida: {file_extension}")
        else:
            return False, f"Erro ao verificar o tipo de arquivo: {str(e)}"
    
    # Validação de segurança de path
    try:
        # Obtém o caminho absoluto real
        real_path = await asyncio.to_thread(os.path.realpath, str(path))
        
        # Verifica se não está fora de diretórios permitidos (simplificado)
        # Numa implementação real, você teria uma lista de diretórios permitidos
        if "../" in str(path) or "..\\" in str(path):
            return False, "Path traversal detectado no caminho do arquivo"
    except Exception as e:
        logger.error(f"Erro na validação de path: {str(e)}")
        return False, f"Erro na validação de segurança: {str(e)}"
    
    return True, None


async def sanitize_filename(filename: str) -> str:
    """
    Sanitiza um nome de arquivo para evitar injeção de path e caracteres inválidos.
    
    Args:
        filename: Nome do arquivo original
        
    Returns:
        Nome de arquivo sanitizado
    """
    # Remove caracteres perigosos e limita o tamanho
    import re
    
    # Remove path traversal e caracteres especiais
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    sanitized = os.path.basename(sanitized)
    
    # Limita tamanho
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized
