#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Servidor MCP para processamento de áudio e mídia.
Implementa funções de transcrição e extração de áudio.
"""

import os
import tempfile
import logging
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Any, Union, Optional
import argparse
import sys

from mcp.server.fastmcp import FastMCP, Context
from .helpers import (
    sanitize_audio_file,
    get_audio_info,
    convert_audio,
    ALLOWED_AUDIO_FORMATS,
    FORMATS_TO_CONVERT
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("mcp-server-media")

# Criar o servidor MCP
mcp = FastMCP(name="Media Server")

# Diretório temporário para arquivos de áudio
TEMP_DIR = Path(tempfile.gettempdir()) / "mcp_media_server"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Configurações padrão (podem ser alteradas via argumentos CLI)
DEFAULT_CONFIG = {
    "max_audio_size": 50 * 1024 * 1024,  # 50MB
    "max_audio_duration": 600,  # 10 minutos
    "whisper_model": "whisper-large-v3",
    "whisper_language": "pt",
    "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
    "huggingface_api_key": os.environ.get("HUGGING_FACE_API_KEY", ""),
}

# Configuração global que será alterada pelos argumentos CLI
config = DEFAULT_CONFIG.copy()


@mcp.tool()
async def transcribe_audio(file_uri: str, ctx: Context) -> Dict[str, Any]:
    """
    Transcreve um arquivo de áudio usando Whisper via API.
    
    Args:
        file_uri: URI do arquivo de áudio (file://path/to/audio.mp3)
        
    Returns:
        Dicionário com a transcrição e metadados do áudio
    """
    try:
        # Verificar se o URI é válido
        if not file_uri.startswith("file://"):
            raise ValueError(f"URI inválido. Deve começar com 'file://': {file_uri}")
        
        # Extrair caminho do arquivo
        file_path = file_uri[7:]  # Remove "file://"
        path = Path(file_path)
        
        ctx.info(f"Processando áudio: {path.name}")
        
        # Verificar se o arquivo existe
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        
        # Sanitizar e converter se necessário
        ctx.info("Sanitizando arquivo de áudio...")
        clean_path = await sanitize_audio_file(
            path, TEMP_DIR, config["max_audio_size"]
        )
        
        # Informar se houve conversão
        converted_msg = ""
        if clean_path.name.startswith("converted_"):
            converted_msg = f" (convertido de {path.suffix} para {clean_path.suffix})"
            ctx.info(f"Arquivo convertido: {path.suffix} -> {clean_path.suffix}")
        
        # Obter informações do áudio
        ctx.info("Obtendo informações do áudio...")
        audio_info = await get_audio_info(clean_path)
        
        # Verificar duração máxima
        if audio_info["duration"] > config["max_audio_duration"]:
            raise ValueError(
                f"Áudio muito longo: {audio_info['duration']:.2f} segundos "
                f"(máximo: {config['max_audio_duration']} segundos)"
            )
        
        # Transcrever o áudio
        ctx.info("Iniciando transcrição do áudio...")
        transcription = await _transcribe_audio(clean_path, ctx)
        
        # Montar resultado
        result = {
            "type": "audio",
            "filename": path.name + converted_msg,
            "duration": audio_info["duration"],
            "transcription": transcription,
            "sample_rate": audio_info["sample_rate"],
            "channels": audio_info["channels"],
            "format": audio_info["format"],
            "was_converted": converted_msg != ""
        }
        
        # Limpar arquivo temporário se necessário
        if clean_path != path and clean_path.exists():
            clean_path.unlink()
            ctx.info(f"Arquivo temporário removido: {clean_path}")
        
        ctx.info(f"Áudio processado com sucesso: {path.name}")
        return result
        
    except Exception as e:
        ctx.error(f"Erro ao processar áudio: {str(e)}")
        
        # Assegurar limpeza em caso de erro
        try:
            if 'clean_path' in locals() and clean_path != path and clean_path.exists():
                clean_path.unlink()
                ctx.info(f"Arquivo temporário removido após erro: {clean_path}")
        except Exception:
            pass
            
        raise ValueError(f"Falha ao processar áudio: {str(e)}")


@mcp.tool()
async def extract_audio_uri(video_uri: str, output_format: str = "mp3", ctx: Context) -> str:
    """
    Extrai o áudio de um arquivo de vídeo e retorna o URI do arquivo de áudio.
    
    Args:
        video_uri: URI do arquivo de vídeo (file://path/to/video.mp4)
        output_format: Formato do áudio de saída (mp3, wav, etc.)
        
    Returns:
        URI do arquivo de áudio extraído
    """
    try:
        # Verificar se o URI é válido
        if not video_uri.startswith("file://"):
            raise ValueError(f"URI inválido. Deve começar com 'file://': {video_uri}")
        
        # Extrair caminho do arquivo
        video_path = video_uri[7:]  # Remove "file://"
        path = Path(video_path)
        
        ctx.info(f"Extraindo áudio do vídeo: {path.name}")
        
        # Verificar se o arquivo existe
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        
        # Definir caminho para o arquivo de áudio extraído
        output_filename = f"audio_{path.stem}.{output_format}"
        output_path = TEMP_DIR / output_filename
        
        # Extrair áudio do vídeo
        await convert_audio(
            path, 
            output_path,
            target_format=output_format,
            audio_quality="192k",
            sample_rate=44100,
            channels=2
        )
        
        # Verificar se a extração foi bem-sucedida
        if not output_path.exists():
            raise ValueError(f"Falha ao extrair áudio do vídeo: {path}")
        
        # Retornar URI do áudio extraído
        audio_uri = f"file://{output_path}"
        ctx.info(f"Áudio extraído com sucesso: {output_path}")
        
        return audio_uri
        
    except Exception as e:
        ctx.error(f"Erro ao extrair áudio do vídeo: {str(e)}")
        raise ValueError(f"Falha ao extrair áudio: {str(e)}")


async def _transcribe_audio(audio_path: Path, ctx: Context) -> str:
    """
    Transcreve o áudio usando a API Whisper via Groq ou fallback para Hugging Face.
    Implementa um sistema de fallback em cascata.
    
    Args:
        audio_path: Caminho para o arquivo de áudio limpo
        ctx: Contexto do MCP para logging
        
    Returns:
        Texto transcrito do áudio
    """
    ctx.info(f"Iniciando transcrição de áudio: {audio_path.name}")
    
    # Estratégia principal: Groq Whisper API
    if config["groq_api_key"]:
        try:
            ctx.info("Tentando transcrição com Groq...")
            transcription = await _transcribe_with_groq(audio_path, ctx)
            ctx.info("Transcrição de áudio concluída com sucesso (Groq)")
            return transcription
        except Exception as e:
            ctx.warning(f"Falha na transcrição com Groq: {str(e)}")
    else:
        ctx.warning("Chave de API Groq não configurada, pulando tentativa")
    
    # Fallback: Hugging Face Whisper
    if config["huggingface_api_key"]:
        try:
            ctx.info("Tentando transcrição com HuggingFace (fallback)...")
            transcription = await _transcribe_with_huggingface(audio_path, ctx)
            ctx.info("Transcrição de áudio concluída com sucesso (HuggingFace fallback)")
            return transcription
        except Exception as e:
            ctx.error(f"Falha na transcrição com HuggingFace: {str(e)}")
    else:
        ctx.warning("Chave de API HuggingFace não configurada, pulando tentativa")
    
    # Se chegou aqui, todas as tentativas falharam
    ctx.error("Todas as tentativas de transcrição falharam")
    raise ValueError("Não foi possível transcrever o áudio. Serviços indisponíveis.")


async def _transcribe_with_groq(audio_path: Path, ctx: Context) -> str:
    """
    Transcreve áudio usando a API Whisper da Groq.
    
    Args:
        audio_path: Caminho para o arquivo de áudio
        ctx: Contexto do MCP para logging
        
    Returns:
        Texto transcrito
    """
    ctx.info(f"Transcrevendo com Groq: {audio_path}")
    
    try:
        # Prepara os dados da requisição
        files = {
            "file": (audio_path.name, open(audio_path, "rb")),
        }
        
        # Extrai apenas o código de idioma principal (pt de pt-BR)
        language_code = config["whisper_language"].split('-')[0] if '-' in config["whisper_language"] else config["whisper_language"]
        ctx.info(f"Usando código de idioma {language_code} para Groq Whisper")
        
        data = {
            "model": config["whisper_model"],
            "response_format": "json",
            "language": language_code
        }
        
        # URL específica para transcrição Groq
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        
        # Cria um cliente HTTP para a requisição
        async with httpx.AsyncClient(timeout=30) as client:
            # Prepara os headers com a chave de API
            headers = {"Authorization": f"Bearer {config['groq_api_key']}"}
            
            # Faz a requisição POST com multipart/form-data
            response = await client.post(
                url=url,
                files=files,
                data=data,
                headers=headers
            )
            
            # Verifica se houve erro
            response.raise_for_status()
            
            # Extrai o resultado
            result = response.json()
            
        # Fecha o arquivo adequadamente
        files["file"][1].close()
        
        # Extrai o texto da resposta
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        else:
            ctx.warning(f"Formato inesperado na resposta Groq: {result}")
            return "Transcrição indisponível (erro de formato)"
            
    except httpx.HTTPStatusError as e:
        ctx.error(f"Erro HTTP na transcrição Groq: {e.response.status_code} {e.response.text}")
        raise Exception(f"Falha na transcrição Groq: código {e.response.status_code}")
    except Exception as e:
        ctx.error(f"Erro na transcrição Groq: {str(e)}")
        raise


async def _transcribe_with_huggingface(audio_path: Path, ctx: Context) -> str:
    """
    Transcreve áudio usando a API Whisper via Hugging Face (fallback).
    
    Args:
        audio_path: Caminho para o arquivo de áudio
        ctx: Contexto do MCP para logging
        
    Returns:
        Texto transcrito
    """
    ctx.info(f"Transcrevendo com HuggingFace: {audio_path}")
    
    try:
        # Prepara a URL para o modelo Whisper
        model = f"openai/{config['whisper_model']}"
        url = f"https://router.huggingface.co/hf-inference/models/{model}"
        
        # Prepara o arquivo para upload
        files = {"file": (audio_path.name, open(audio_path, "rb"))}
        
        # Prepara os parâmetros para a API
        # Usa apenas o código principal, como "pt" em vez de "pt-BR"
        language = config["whisper_language"].split('-')[0] if '-' in config["whisper_language"] else config["whisper_language"]
        params = {"language": language}
        
        # Cria um cliente HTTP com o timeout configurado
        async with httpx.AsyncClient(timeout=30) as client:
            # Prepara os headers com a chave de API
            headers = {"Authorization": f"Bearer {config['huggingface_api_key']}"}
            
            # Faz a requisição POST com o arquivo
            response = await client.post(
                url=url,
                files=files,
                headers=headers,
                params=params
            )
            
            # Verifica se houve erro
            response.raise_for_status()
            
            # Extrai o resultado
            result = response.json()
        
        # Fecha o arquivo adequadamente
        files["file"][1].close()
        
        # Extrai o texto da resposta
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        else:
            ctx.warning(f"Formato inesperado na resposta HF: {result}")
            return "Transcrição indisponível (erro de formato)"
            
    except httpx.HTTPStatusError as e:
        ctx.error(f"Erro HTTP na transcrição HF: {e.response.status_code} {e.response.text}")
        raise Exception(f"Falha na transcrição HF: código {e.response.status_code}")
    except Exception as e:
        ctx.error(f"Erro na transcrição HuggingFace: {str(e)}")
        raise


def parse_arguments():
    """Parse os argumentos de linha de comando para configurar o servidor."""
    parser = argparse.ArgumentParser(description='Servidor MCP para processamento de mídia')
    
    parser.add_argument('--max-audio-size', type=int, default=DEFAULT_CONFIG["max_audio_size"],
                        help='Tamanho máximo de arquivo de áudio em bytes')
    
    parser.add_argument('--max-audio-duration', type=int, default=DEFAULT_CONFIG["max_audio_duration"],
                        help='Duração máxima de áudio em segundos')
    
    parser.add_argument('--whisper-model', type=str, default=DEFAULT_CONFIG["whisper_model"],
                        help='Modelo Whisper a ser usado (ex: whisper-large-v3)')
    
    parser.add_argument('--whisper-language', type=str, default=DEFAULT_CONFIG["whisper_language"],
                        help='Código de idioma para Whisper (ex: pt, en)')
    
    parser.add_argument('--temp-dir', type=str, default=None,
                        help='Diretório temporário para arquivos de áudio')
    
    return parser.parse_args()


def main():
    """Função principal que configura e inicia o servidor MCP."""
    # Parsear argumentos da linha de comando
    args = parse_arguments()
    
    # Atualizar configuração global
    config.update({
        "max_audio_size": args.max_audio_size,
        "max_audio_duration": args.max_audio_duration,
        "whisper_model": args.whisper_model,
        "whisper_language": args.whisper_language,
    })
    
    # Configurar diretório temporário personalizado se fornecido
    global TEMP_DIR
    if args.temp_dir:
        TEMP_DIR = Path(args.temp_dir)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Usando diretório temporário personalizado: {TEMP_DIR}")
    
    # Log de configurações
    logger.info(f"Iniciando servidor MCP Media com configurações:")
    logger.info(f"  Tamanho máximo de áudio: {config['max_audio_size']/1024/1024:.1f}MB")
    logger.info(f"  Duração máxima de áudio: {config['max_audio_duration']} segundos")
    logger.info(f"  Modelo Whisper: {config['whisper_model']}")
    logger.info(f"  Idioma Whisper: {config['whisper_language']}")
    logger.info(f"  Diretório temporário: {TEMP_DIR}")
    logger.info(f"  API Groq: {'Configurada' if config['groq_api_key'] else 'Não configurada'}")
    logger.info(f"  API HuggingFace: {'Configurada' if config['huggingface_api_key'] else 'Não configurada'}")
    logger.info(f"  Formatos de áudio suportados: {', '.join(ALLOWED_AUDIO_FORMATS + FORMATS_TO_CONVERT)}")
    
    # Iniciar o servidor MCP
    mcp.run()


if __name__ == "__main__":
    main()
