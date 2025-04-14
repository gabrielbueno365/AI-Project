#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cliente MCP para comunicação com o servidor de mídia.
Permite transcrição de áudio e extração de áudio de vídeos.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Dict, Any, List, Optional, Union

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MediaClient:
    """
    Cliente para o servidor MCP de mídia (mcp-server-media).
    
    Este cliente permite:
    - Transcrever arquivos de áudio usando Whisper
    - Extrair áudio de arquivos de vídeo
    """
    
    def __init__(self, command: List[str]):
        """
        Inicializa o cliente de mídia.
        
        Args:
            command: Comando para iniciar o servidor MCP (ex: ["poetry", "run", "python", "path/to/server.py"])
        """
        self.server_params = StdioServerParameters(command=command[0], args=command[1:])
        self._session: Optional[ClientSession] = None
    
    @asynccontextmanager
    async def connect(self) -> AsyncIterator['MediaClient']:
        """
        Gerencia a conexão com o servidor.
        
        Yields:
            Instância conectada do cliente
        """
        logger.info("Conectando ao servidor MCP de mídia...")
        async with stdio_client(self.server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                logger.info("Conexão estabelecida com o servidor MCP de mídia")
                self._session = session
                try:
                    yield self
                finally:
                    self._session = None
                    logger.info("Conexão com o servidor MCP de mídia encerrada")
    
    async def _ensure_connected(self) -> ClientSession:
        """
        Garante que o cliente está conectado ao servidor.
        
        Returns:
            Sessão do cliente
            
        Raises:
            RuntimeError: Se o cliente não estiver conectado
        """
        if not self._session:
            raise RuntimeError("Cliente não conectado. Use 'async with client.connect():'")
        return self._session
    
    async def transcribe_audio(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Transcreve um arquivo de áudio usando APIs Whisper.
        
        O servidor usa Groq como primeira opção, com fallback para HuggingFace.
        
        Args:
            file_path: Caminho para o arquivo de áudio
            
        Returns:
            Dicionário com a transcrição e metadados do áudio:
            {
                "type": "audio",
                "filename": str,
                "duration": float,
                "transcription": str,
                "sample_rate": int,
                "channels": int,
                "format": str,
                "was_converted": bool
            }
            
        Raises:
            ValueError: Se houver erro no processamento
        """
        session = await self._ensure_connected()
        
        # Normaliza o caminho para garantir formato correto
        path = Path(file_path).resolve()
        file_uri = f"file://{path}"
        
        logger.info(f"Solicitando transcrição do áudio: {path.name}")
        
        try:
            # Chama a tool de transcrição
            result = await session.call_tool(
                "transcribe_audio", 
                {"file_uri": file_uri}
            )
            
            # Processa o resultado
            if result.content and isinstance(result.content[0], types.TextContent):
                import json
                try:
                    # Tenta converter o resultado de texto para dict
                    return json.loads(result.content[0].text)
                except json.JSONDecodeError:
                    # Caso não seja JSON válido, retorna um dict mínimo
                    return {
                        "type": "audio",
                        "filename": path.name,
                        "transcription": result.content[0].text
                    }
            
            # Fallback se o formato de resposta for inesperado
            return {
                "type": "audio",
                "filename": path.name,
                "transcription": "Erro ao processar transcrição",
                "error": "Formato de resposta inesperado"
            }
            
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio: {str(e)}")
            raise ValueError(f"Falha na transcrição: {str(e)}")
    
    async def extract_audio(
        self, 
        video_path: Union[str, Path], 
        output_format: str = "mp3"
    ) -> str:
        """
        Extrai a trilha de áudio de um arquivo de vídeo.
        
        Args:
            video_path: Caminho para o arquivo de vídeo
            output_format: Formato do áudio de saída (mp3, wav, etc.)
            
        Returns:
            Caminho para o arquivo de áudio extraído
            
        Raises:
            ValueError: Se houver erro na extração
        """
        session = await self._ensure_connected()
        
        # Normaliza o caminho para garantir formato correto
        path = Path(video_path).resolve()
        video_uri = f"file://{path}"
        
        logger.info(f"Solicitando extração de áudio do vídeo: {path.name}")
        
        try:
            # Chama a tool de extração
            result = await session.call_tool(
                "extract_audio_uri", 
                {
                    "video_uri": video_uri,
                    "output_format": output_format
                }
            )
            
            # Processa o resultado
            if result.content and isinstance(result.content[0], types.TextContent):
                audio_uri = result.content[0].text
                
                # Remove o prefixo "file://" para retornar apenas o caminho
                if audio_uri.startswith("file://"):
                    return audio_uri[7:]
                
                return audio_uri
            
            # Erro se o formato de resposta for inesperado
            raise ValueError("Formato de resposta inesperado ao extrair áudio")
            
        except Exception as e:
            logger.error(f"Erro ao extrair áudio: {str(e)}")
            raise ValueError(f"Falha na extração de áudio: {str(e)}")


# Exemplo de uso
async def _example_usage():
    from src.core.config import get_settings
    settings = get_settings()
    
    # Comando para iniciar o servidor MCP de mídia
    command = settings.media_server_cmd.split()
    
    # Cria o cliente
    client = MediaClient(command)
    
    # Usa o cliente
    async with client.connect():
        # Transcreve um áudio
        result = await client.transcribe_audio("/path/to/audio.mp3")
        print(f"Transcrição: {result['transcription']}")
        
        # Extrai áudio de um vídeo
        audio_path = await client.extract_audio("/path/to/video.mp4")
        print(f"Áudio extraído: {audio_path}")
