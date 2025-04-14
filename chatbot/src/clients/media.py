#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cliente para comunicação com o servidor de mídia.
Permite transcrição de áudio e extração de áudio de vídeos.

Implemantação alternativa que não depende diretamente do pacote MCP.
"""

import asyncio
import json
import logging
import os
import shlex
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class MediaClient:
    """
    Cliente para o servidor MCP de mídia.
    
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
        self.command = command
        self._process = None
        self._stdin = None
        self._stdout = None
        self._request_id = 0
    
    @asynccontextmanager
    async def connect(self) -> AsyncIterator['MediaClient']:
        """
        Gerencia a conexão com o servidor.
        
        Yields:
            Instância conectada do cliente
        """
        logger.info("Conectando ao servidor MCP de mídia...")
        
        try:
            # Inicia o processo do servidor
            self._process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self._stdin = self._process.stdin
            self._stdout = self._process.stdout
            
            # Inicializa a conexão
            await self._send_request("initialize", {})
            response = await self._read_response()
            
            if response.get("status") != "success":
                raise RuntimeError(f"Falha ao inicializar servidor: {response}")
                
            logger.info("Conexão estabelecida com o servidor MCP de mídia")
            
            try:
                yield self
            finally:
                # Encerra a conexão
                try:
                    await self._send_request("shutdown", {})
                except:
                    pass
                    
                # Encerra o processo
                if self._process:
                    try:
                        self._process.terminate()
                        await asyncio.wait_for(self._process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self._process.kill()
                    
                self._process = None
                self._stdin = None
                self._stdout = None
                logger.info("Conexão com o servidor MCP de mídia encerrada")
                
        except Exception as e:
            logger.error(f"Erro ao conectar com servidor MCP: {str(e)}")
            
            # Certifica de limpar os recursos em caso de erro
            if self._process:
                try:
                    self._process.terminate()
                except:
                    pass
                    
            self._process = None
            self._stdin = None
            self._stdout = None
            raise
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> None:
        """
        Envia uma requisição para o servidor.
        
        Args:
            method: Método a ser chamado
            params: Parâmetros para o método
        """
        if not self._stdin:
            raise RuntimeError("Cliente não conectado")
            
        self._request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }
        
        request_json = json.dumps(request) + "\n"
        self._stdin.write(request_json.encode())
        await self._stdin.drain()
    
    async def _read_response(self) -> Dict[str, Any]:
        """
        Lê uma resposta do servidor.
        
        Returns:
            Resposta como um dicionário
        """
        if not self._stdout:
            raise RuntimeError("Cliente não conectado")
            
        line = await self._stdout.readline()
        if not line:
            raise RuntimeError("Conexão encerrada pelo servidor")
            
        try:
            response = json.loads(line.decode().strip())
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta: {line.decode()}")
            raise RuntimeError(f"Resposta inválida do servidor: {str(e)}")
    
    async def _ensure_connected(self) -> None:
        """
        Garante que o cliente está conectado ao servidor.
            
        Raises:
            RuntimeError: Se o cliente não estiver conectado
        """
        if not self._process or not self._stdin or not self._stdout:
            raise RuntimeError("Cliente não conectado. Use 'async with client.connect():'")
    
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
        await self._ensure_connected()
        
        # Normaliza o caminho para garantir formato correto
        path = Path(file_path).resolve()
        file_uri = f"file://{path}"
        
        logger.info(f"Solicitando transcrição do áudio: {path.name}")
        
        try:
            # Chama a tool de transcrição
            await self._send_request(
                "call", 
                {
                    "tool": "transcribe_audio",
                    "params": {"file_uri": file_uri}
                }
            )
            
            response = await self._read_response()
            
            # Verifica erros na resposta
            if "error" in response:
                logger.error(f"Erro do servidor: {response['error']}")
                raise ValueError(f"Erro do servidor: {response['error']}")
            
            # Processa o resultado
            if "result" in response and isinstance(response["result"], dict):
                # Se já for um dicionário, retorna como está
                return response["result"]
            elif "result" in response and isinstance(response["result"], str):
                # Se for uma string, tenta fazer parse como JSON
                try:
                    return json.loads(response["result"])
                except json.JSONDecodeError:
                    # Se não for JSON válido, retorna um dict mínimo
                    return {
                        "type": "audio",
                        "filename": path.name,
                        "transcription": response["result"]
                    }
            
            # Fallback para resposta inesperada
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
        await self._ensure_connected()
        
        # Normaliza o caminho para garantir formato correto
        path = Path(video_path).resolve()
        video_uri = f"file://{path}"
        
        logger.info(f"Solicitando extração de áudio do vídeo: {path.name}")
        
        try:
            # Chama a tool de extração
            await self._send_request(
                "call", 
                {
                    "tool": "extract_audio_uri",
                    "params": {
                        "video_uri": video_uri,
                        "output_format": output_format
                    }
                }
            )
            
            response = await self._read_response()
            
            # Verifica erros na resposta
            if "error" in response:
                logger.error(f"Erro do servidor: {response['error']}")
                raise ValueError(f"Erro do servidor: {response['error']}")
            
            # Processa o resultado
            if "result" in response and isinstance(response["result"], str):
                audio_uri = response["result"]
                
                # Remove o prefixo "file://" para retornar apenas o caminho
                if audio_uri.startswith("file://"):
                    return audio_uri[7:]
                
                return audio_uri
            
            # Erro se o formato de resposta for inesperado
            raise ValueError("Formato de resposta inesperado ao extrair áudio")
            
        except Exception as e:
            logger.error(f"Erro ao extrair áudio: {str(e)}")
            raise ValueError(f"Falha na extração de áudio: {str(e)}")
