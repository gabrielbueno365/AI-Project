#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilidades para processamento de arquivos de áudio.
Fornece funções para validação, conversão e verificação de formatos.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
import asyncio
import filetype
import shutil

import ffmpeg

logger = logging.getLogger(__name__)

# Constantes
ALLOWED_AUDIO_FORMATS = [
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", 
    ".mp4", ".mpeg", ".mpga", ".oga", ".webm"
]

AUDIO_MIME_TYPES = [
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/flac", 
    "audio/x-m4a", "audio/aac", "audio/webm", "video/mp4",
    "audio/mp4", "audio/mpeg", "audio/mpga", "audio/oga"
]

# Formatos que podem necessitar de conversão mesmo quando o MIME type é de áudio
# (formatos menos comuns ou problemáticos)
FORMATS_TO_CONVERT = [
    ".wma", ".aiff", ".aif", ".3gp", ".amr", ".m4b", ".ra", ".rm", ".vox", ".raw",
    ".au", ".dct", ".gsm", ".vox", ".m4p", ".mid", ".midi", ".opus"
]


async def verify_audio_format(file_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Verifica se o arquivo está em um formato de áudio suportado.
    
    Args:
        file_path: Caminho para o arquivo de áudio
        
    Returns:
        Tupla (is_valid, reason) indicando se o formato é válido e o motivo se não for
    """
    path = Path(file_path)
    
    # Verifica extensão
    if path.suffix.lower() in FORMATS_TO_CONVERT:
        return False, f"Formato reconhecido, mas requer conversão: {path.suffix}"
    
    if path.suffix.lower() not in ALLOWED_AUDIO_FORMATS:
        return False, f"Formato de arquivo não suportado: {path.suffix}"
    
    # Verifica MIME type
    try:
        # Use filetype para determinar o MIME type real
        kind = await asyncio.to_thread(filetype.guess, str(path))
        mime_type = kind.mime if kind else None
        if not mime_type or mime_type not in AUDIO_MIME_TYPES:
            return False, f"Tipo MIME não suportado: {mime_type}"
    except Exception as e:
        logger.error(f"Erro ao verificar MIME type: {str(e)}")
        return False, f"Erro ao verificar o tipo de arquivo: {str(e)}"
    
    return True, "Formato válido"


async def convert_audio(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    target_format: str = "mp3",
    audio_quality: str = "192k",  # Taxa de bits para áudio (qualidade)
    sample_rate: int = 44100,     # Taxa de amostragem (Hz)
    channels: int = 2            # Número de canais (2 = estéreo)
) -> Path:
    """
    Converte um arquivo de áudio para o formato especificado usando FFmpeg.
    
    Args:
        input_path: Caminho para o arquivo de áudio original
        output_path: Caminho para o arquivo de saída
        target_format: Formato de saída (mp3, wav, etc.)
        audio_quality: Taxa de bits para codificação de áudio
        sample_rate: Taxa de amostragem em Hz
        channels: Número de canais de áudio
        
    Returns:
        Caminho para o arquivo convertido
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    # Verificar se ffmpeg está instalado no sistema
    if not shutil.which('ffmpeg'):
        logger.error("FFmpeg não encontrado no sistema. Por favor, instale o FFmpeg.")
        raise ValueError("FFmpeg não encontrado no sistema. Necessário para conversão de áudio.")
    
    logger.info(f"Convertendo {input_path} para {target_format} em {output_path}")
    
    try:
        # Verifica se o arquivo de entrada existe
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")
        
        # Garantir que o diretório de saída existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
            
        logger.debug(f"FFmpeg: convertendo {input_path} para {output_path} usando formato {target_format}")
        
        # Configura a conversão com parâmetros otimizados
        # Usamos o método .output para especificar o arquivo de saída
        try:
            await asyncio.to_thread(
                lambda: ffmpeg
                .input(str(input_path))
                .output(
                    str(output_path),
                    acodec='libmp3lame' if target_format == 'mp3' else 'pcm_s16le',  # Codificador apropriado
                    ar=sample_rate,      # Taxa de amostragem
                    ac=channels,         # Número de canais
                    ab=audio_quality,    # Taxa de bits
                    **{'loglevel': 'error'}  # Reduzir logs do FFmpeg
                )
                .overwrite_output()   # Sobrescrever se o arquivo já existir
                .run(capture_stdout=True, capture_stderr=True)  # Executar silenciosamente
            )
        except ffmpeg.Error as fe:
            stderr = fe.stderr.decode() if hasattr(fe, 'stderr') else str(fe)
            logger.error(f"Erro no FFmpeg: {stderr}")
            raise ValueError(f"Erro no FFmpeg: {stderr}")
        except Exception as e:
            logger.error(f"Erro ao executar FFmpeg: {str(e)}")
            raise ValueError(f"Erro ao executar FFmpeg: {str(e)}")
        
        
        # Verifica se o arquivo foi criado corretamente
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ValueError(f"Falha na conversão: arquivo de saída vazio ou inexistente")
        
        logger.info(f"Conversão concluída com sucesso: {output_path}")
        return output_path
        
    except ffmpeg.Error as e:
        # Captura erros específicos do FFmpeg (problema de codec, arquivo corrompido, etc.)
        error_message = f"Erro no FFmpeg: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}"
        logger.error(error_message)
        raise ValueError(f"Falha na conversão de áudio: {error_message}")
        
    except Exception as e:
        # Outros erros inesperados
        logger.error(f"Erro ao converter áudio: {str(e)}")
        raise ValueError(f"Falha na conversão de áudio: {str(e)}")


async def sanitize_audio_file(
    file_path: Union[str, Path], 
    temp_dir: Union[str, Path],
    max_size: int = 50 * 1024 * 1024,  # 50MB
    target_format: str = "mp3"  # Formato de saída padrão
) -> Path:
    """
    Sanitiza um arquivo de áudio, garantindo que é seguro para processamento.
    Converte formatos não suportados para um formato compatível.
    
    Args:
        file_path: Caminho para o arquivo de áudio
        temp_dir: Diretório para arquivos temporários
        max_size: Tamanho máximo permitido em bytes
        target_format: Formato para conversão (se necessário)
        
    Returns:
        Caminho para o arquivo sanitizado/convertido
    """
    path = Path(file_path)
    temp_dir = Path(temp_dir)
    
    # Verifica tamanho
    file_size = path.stat().st_size
    if file_size > max_size:
        raise ValueError(f"Arquivo muito grande: {file_size} bytes (máximo: {max_size} bytes)")
    
    # Verifica formato
    is_valid, reason = await verify_audio_format(path)
    
    # Formatos que sempre devem ser convertidos para MP3 (mesmo que válidos para algumas APIs)
    formats_to_always_convert = [".m4a", ".aac", ".wma", ".aiff", ".ogg"]
    force_convert = path.suffix.lower() in formats_to_always_convert
    
    # Se o formato for válido e não está na lista de conversão forçada, apenas cria uma cópia sanitizada
    if is_valid and not force_convert:
        sanitized_path = temp_dir / f"safe_{path.name}"
        await asyncio.to_thread(shutil.copy2, path, sanitized_path)
        logger.info(f"Arquivo copiado para versão sanitizada: {sanitized_path}")
        return sanitized_path
    
    # Se o formato for válido mas está na lista de conversão forçada
    if is_valid and force_convert:
        logger.info(f"Formato {path.suffix} válido, mas forçando conversão para MP3 para melhor compatibilidade com APIs")
        reason = "Forçando conversão para melhor compatibilidade com APIs"
    
    # Se o formato não for válido, converte para o formato alvo
    logger.info(f"Convertendo formato não suportado: {path.suffix}. Motivo: {reason}")
    
    # Define o caminho para o arquivo convertido
    output_filename = f"converted_{path.stem}.{target_format}"
    output_path = temp_dir / output_filename
    
    # Converte o arquivo usando FFmpeg
    try:
        await convert_audio(path, output_path, target_format)
        logger.info(f"Arquivo convertido com sucesso para: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Falha ao converter arquivo: {str(e)}")
        raise ValueError(f"Não foi possível converter o arquivo: {str(e)}")


async def get_audio_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Obtém informações básicas sobre um arquivo de áudio usando ffprobe.
    Requer FFmpeg instalado no sistema.
    
    Args:
        file_path: Caminho para o arquivo de áudio
        
    Returns:
        Dicionário com informações do áudio
    """
    import ffmpeg
    
    path = Path(file_path)
    
    try:
        # Executa ffprobe em modo assíncrono
        probe = await asyncio.to_thread(lambda: ffmpeg.probe(str(path)))
        
        # Extrai informações relevantes
        format_info = probe.get("format", {})
        duration = float(format_info.get("duration", 0))
        
        # Encontra o stream de áudio
        audio_stream = None
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break
        
        result = {
            "filename": path.name,
            "format": path.suffix.lower()[1:],  # Sem o ponto
            "size_bytes": path.stat().st_size,
            "duration": duration,
            "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
            "channels": int(audio_stream.get("channels", 0)) if audio_stream else 0,
            "codec": audio_stream.get("codec_name", "") if audio_stream else "",
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do áudio: {str(e)}")
        raise ValueError(f"Não foi possível analisar o arquivo de áudio: {str(e)}")
