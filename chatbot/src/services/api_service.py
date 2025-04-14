#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serviço para comunicação com APIs externas.
Gerencia chamadas para Hugging Face e Groq.
"""

import asyncio
import httpx
import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple, BinaryIO

from src.core.config import get_settings
from src.utils.prompt.optimizers import optimize_token_usage, process_in_chunks

logger = logging.getLogger(__name__)
settings = get_settings()


class APIClient:
    """
    Cliente para APIs externas com retry e circuit breaker.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        """
        Inicializa o cliente de API.
        
        Args:
            base_url: URL base da API
            api_key: Chave de API
            timeout: Timeout em segundos
            max_retries: Número máximo de tentativas
            backoff_factor: Fator para backoff exponencial
        """
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Estado do circuit breaker
        self._failure_count = 0
        self._circuit_open = False
        self._last_failure_time = 0
        self._circuit_reset_time = 30  # segundos
    
    async def _request(
        self, 
        method: str, 
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Realiza uma requisição para a API com retry e circuit breaker.
        
        Args:
            method: Método HTTP (GET, POST, etc)
            endpoint: Endpoint da API
            data: Dados para enviar no corpo da requisição
            
        Returns:
            Resposta da API como dicionário
            
        Raises:
            Exception: Se a requisição falhar após todas as tentativas
        """
        # Verifica se o circuit breaker está aberto
        if self._circuit_open:
            # Verifica se já passou o tempo de reset
            if time.time() - self._last_failure_time > self._circuit_reset_time:
                logger.info(f"Tentando resetar circuit breaker para {self.base_url}")
                self._circuit_open = False
                self._failure_count = 0
            else:
                logger.warning(f"Circuit breaker aberto para {self.base_url}")
                raise Exception(f"Serviço temporariamente indisponível (circuit breaker)")
        
        url = f"{self.base_url}/{endpoint}"
        retry_count = 0
        
        # Loop de retry
        while retry_count < self.max_retries:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(f"Requisição {method} para {url}")
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data,
                        headers=self.headers,
                    )
                    
                    # Verifica se a resposta é um sucesso
                    response.raise_for_status()
                    
                    # Reset contador de falhas em caso de sucesso
                    self._failure_count = 0
                    
                    # Retorna os dados da resposta
                    return response.json()
                    
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                retry_count += 1
                self._failure_count += 1
                
                logger.warning(
                    f"Falha na requisição para {url}: {str(e)}. "
                    f"Tentativa {retry_count}/{self.max_retries}"
                )
                
                # Verifica se o circuit breaker deve ser aberto
                if self._failure_count >= 5:
                    logger.error(f"Abrindo circuit breaker para {self.base_url}")
                    self._circuit_open = True
                    self._last_failure_time = time.time()
                    raise Exception(f"Serviço indisponível após múltiplas falhas: {str(e)}")
                
                # Calcula tempo de espera para backoff exponencial
                backoff_time = self.backoff_factor * (2 ** (retry_count - 1))
                logger.info(f"Aguardando {backoff_time:.2f}s antes da próxima tentativa")
                await asyncio.sleep(backoff_time)
        
        # Se chegou aqui, todas as tentativas falharam
        logger.error(f"Todas as tentativas falharam para {url}")
        raise Exception(f"Falha ao comunicar com a API após {self.max_retries} tentativas")


class HuggingFaceService:
    """Serviço para interação com a API da Hugging Face."""
    
    def __init__(self):
        """Inicializa o serviço da Hugging Face."""
        self.api_key = settings.hugging_face_api_key
        self.client = APIClient(
            base_url="https://api-inference.huggingface.co/models",
            api_key=self.api_key,
            timeout=settings.request_timeout,
            max_retries=settings.max_retries,
            backoff_factor=settings.backoff_factor,
        )
    
    async def generate_text(
        self, 
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 500,
        optimize_tokens: bool = True,
        use_chunking: bool = True,
    ) -> str:
        """
        Gera texto usando a API da Hugging Face.
        Aplica otimização de tokens e processamento em chunks quando necessário.
        
        Args:
            messages: Lista de mensagens no formato {"role": "...", "content": "..."}
            model: Nome do modelo a ser usado
            max_tokens: Número máximo de tokens na resposta
            optimize_tokens: Se deve aplicar otimização de tokens
            use_chunking: Se deve processar em chunks quando necessário
            
        Returns:
            Texto gerado pelo modelo
        """
        if not model:
            model = settings.default_huggingface_model
            
        logger.info(f"Gerando texto com modelo {model}")
        
        # Otimiza as mensagens para reduzir o uso de tokens, se habilitado
        if optimize_tokens:
            # Obtem versão otimizada das mensagens e max_tokens recomendado
            optimized_messages, recommended_max_tokens = optimize_token_usage(messages)
            # Usa o max_tokens recomendado, mas respeita o limite do usuário
            messages = optimized_messages
            max_tokens = max(min(max_tokens, 1500), recommended_max_tokens)  # entre 500-1500
            logger.debug(f"Usando max_tokens ajustado: {max_tokens}")
        
        # Extrai o último conteúdo do usuário (para processamento em chunks)
        last_user_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        # Se a mensagem for muito longa e chunking estiver habilitado, processa por chunks
        if last_user_message and use_chunking and len(last_user_message) > 3000:  # ~750 tokens
            logger.info(f"Mensagem longa detectada: {len(last_user_message)} caracteres, processando em chunks")
            
            # Define função de processamento para cada chunk
            async def process_chunk(chunk_content, **kwargs):
                # Substitui a última mensagem do usuário pelo chunk
                chunk_messages = messages.copy()
                for i in range(len(chunk_messages) - 1, -1, -1):
                    if chunk_messages[i]["role"] == "user":
                        chunk_messages[i]["content"] = chunk_content
                        break
                
                # Converte mensagens para o formato esperado pela API
                content = " ".join(msg["content"] for msg in chunk_messages)
                
                # Define os dados da requisição
                data = {
                    "inputs": content,
                    "parameters": {
                        "max_new_tokens": kwargs.get("max_tokens", max_tokens),
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "do_sample": True,
                    },
                }
                
                # Faz a requisição para a API
                result = await self.client._request("POST", model, data)
                
                # Extrai o texto da resposta
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return "" 
            
            # Processa em chunks e retorna o resultado combinado
            return await process_in_chunks(last_user_message, process_chunk)
        
        # Processamento normal (sem chunks)
        # Converte mensagens para o formato esperado pela API
        content = " ".join(msg["content"] for msg in messages)
        
        # Define os dados da requisição
        data = {
            "inputs": content,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.95,
                "do_sample": True,
            },
        }
        
        try:
            # Faz a requisição para a API
            result = await self.client._request("POST", model, data)
            
            # Extrai o texto da resposta
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                return generated_text
            else:
                logger.error(f"Formato inesperado de resposta: {result}")
                return "Não foi possível gerar uma resposta. Tente novamente."
                
        except Exception as e:
            logger.error(f"Erro ao gerar texto: {str(e)}", exc_info=True)
            raise Exception(f"Falha na geração de texto: {str(e)}")
            
    async def transcribe_audio(
        self,
        audio_file: BinaryIO,
        model: str = "openai/whisper-large-v3",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcreve áudio usando a API Whisper via Hugging Face.
        
        Args:
            audio_file: Arquivo de áudio aberto em modo binário
            model: ID do modelo Whisper na Hugging Face
            
        Returns:
            Dicionário com a transcrição
        """
        logger.info(f"Transcrevendo áudio com modelo HuggingFace {model}")
        
        try:
            # Prepara a URL para o modelo específico
            url = f"https://router.huggingface.co/hf-inference/models/{model}"
            
            # Prepara o arquivo para upload
            files = {"file": ("audio.mp3", audio_file)}
            
            # Prepara os parâmetros para a API
            params = {}
            if language:
                params["language"] = language
            
            # Cria um cliente HTTP com o timeout configurado
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                # Prepara os headers (incluindo a chave de API)
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # Faz a requisição POST com o arquivo
                response = await client.post(
                    url=url,
                    files=files,
                    headers=headers,
                    params=params
                )
                
                # Verifica se houve erro
                response.raise_for_status()
                
                # Retorna o resultado como JSON
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP na transcrição HF: {e.response.status_code} {e.response.text}")
            raise Exception(f"Falha na transcrição: código {e.response.status_code}")
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio com HuggingFace: {str(e)}", exc_info=True)
            raise Exception(f"Falha na transcrição de áudio: {str(e)}")


class GroqService:
    """Serviço para interação com a API da Groq."""
    
    def __init__(self):
        """Inicializa o serviço da Groq."""
        self.api_key = settings.groq_api_key
        self.client = APIClient(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key,
            timeout=settings.request_timeout,
            max_retries=settings.max_retries,
            backoff_factor=settings.backoff_factor,
        )
    
    async def generate_text(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 500,
        optimize_tokens: bool = True,
        use_chunking: bool = True,
    ) -> str:
        """
        Gera texto usando a API da Groq.
        Aplica otimização de tokens e processamento em chunks quando necessário.
        
        Args:
            messages: Lista de mensagens no formato {"role": "...", "content": "..."}
            model: Nome do modelo a ser usado
            max_tokens: Número máximo de tokens na resposta
            optimize_tokens: Se deve aplicar otimização de tokens
            use_chunking: Se deve processar em chunks quando necessário
            
        Returns:
            Texto gerado pelo modelo
        """
        if not model:
            model = settings.default_groq_model
            
        logger.info(f"Gerando texto com modelo Groq {model}")
        
        # Otimiza as mensagens para reduzir o uso de tokens, se habilitado
        if optimize_tokens:
            # Obtem versão otimizada das mensagens e max_tokens recomendado
            optimized_messages, recommended_max_tokens = optimize_token_usage(messages)
            # Usa o max_tokens recomendado, mas respeita o limite do usuário
            messages = optimized_messages
            max_tokens = max(min(max_tokens, 1500), recommended_max_tokens)  # entre 500-1500
            logger.debug(f"Usando max_tokens ajustado: {max_tokens}")
        
        # Extrai o último conteúdo do usuário (para processamento em chunks)
        last_user_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        # Se a mensagem for muito longa e chunking estiver habilitado, processa por chunks
        if last_user_message and use_chunking and len(last_user_message) > 3000:  # ~750 tokens
            logger.info(f"Mensagem longa detectada: {len(last_user_message)} caracteres, processando em chunks")
            
            # Define função de processamento para cada chunk
            async def process_chunk(chunk_content, **kwargs):
                # Substitui a última mensagem do usuário pelo chunk
                chunk_messages = messages.copy()
                for i in range(len(chunk_messages) - 1, -1, -1):
                    if chunk_messages[i]["role"] == "user":
                        chunk_messages[i]["content"] = chunk_content
                        break
                
                # Define os dados da requisição para o chunk
                data = {
                    "model": model,
                    "messages": chunk_messages,
                    "max_tokens": kwargs.get("max_tokens", max_tokens),
                    "temperature": 0.7,
                    "top_p": 0.95,
                }
                
                # Faz a requisição para a API
                result = await self.client._request("POST", "chat/completions", data)
                
                # Extrai o texto da resposta
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0].get("message", {}).get("content", "")
                return ""
            
            # Processa em chunks e retorna o resultado combinado
            return await process_in_chunks(last_user_message, process_chunk)
        
        # Processamento normal (sem chunks)
        # Define os dados da requisição
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.95,
        }
        
        try:
            # Faz a requisição para a API
            result = await self.client._request("POST", "chat/completions", data)
            
            # Extrai o texto da resposta
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                return content
            else:
                logger.error(f"Formato inesperado de resposta: {result}")
                return "Não foi possível gerar uma resposta. Tente novamente."
                
        except Exception as e:
            logger.error(f"Erro ao gerar texto com Groq: {str(e)}", exc_info=True)
            raise Exception(f"Falha na geração de texto com Groq: {str(e)}")
            
    async def transcribe_audio(
        self,
        audio_file: BinaryIO,
        model: str = "whisper-large-v3",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Transcreve áudio usando a API Whisper da Groq.
        
        Args:
            audio_file: Arquivo de áudio aberto em modo binário
            model: ID do modelo (Whisper)
            language: Código de idioma ISO-639-1 opcional (ex: 'pt', 'en')
            prompt: Texto opcional para guiar a transcrição
            response_format: Formato da resposta ('json', 'text', 'verbose_json')
            
        Returns:
            Dicionário com a transcrição
        """
        logger.info(f"Transcrevendo áudio com modelo Groq {model}")
        
        # Prepara os dados da requisição
        files = {
            "file": ("audio.mp3", audio_file),
        }
        
        data = {
            "model": model,
            "response_format": response_format,
        }
        
        # Adiciona parâmetros opcionais
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        
        try:
            # URL específica para transcrição
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            
            # Cria um cliente HTTP para a requisição
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                # Prepara os headers (incluindo a chave de API)
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                # Faz a requisição POST com multipart/form-data
                response = await client.post(
                    url=url,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                # Verifica se houve erro
                response.raise_for_status()
                
                # Retorna o resultado como JSON
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP na transcrição Groq: {e.response.status_code} {e.response.text}")
            raise Exception(f"Falha na transcrição: código {e.response.status_code}")
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio com Groq: {str(e)}", exc_info=True)
            raise Exception(f"Falha na transcrição de áudio: {str(e)}")


class FireworksAIService:
    """Serviço para interação com a API da Fireworks AI via Hugging Face."""
    
    def __init__(self):
        """Inicializa o serviço da Fireworks AI."""
        self.api_key = settings.hugging_face_api_key
        self.client = APIClient(
            base_url="https://router.huggingface.co/fireworks-ai/inference/v1",
            api_key=self.api_key,
            timeout=settings.request_timeout,
            max_retries=settings.max_retries,
            backoff_factor=settings.backoff_factor,
        )
    
    async def generate_text(
        self, 
        messages: List[Dict[str, str]],
        model: str = "accounts/perplexity/models/r1-1776",
        max_tokens: int = 500,
        optimize_tokens: bool = True,
        use_chunking: bool = True,
    ) -> str:
        """
        Gera texto usando a API da Fireworks AI via Hugging Face.
        Aplica otimização de tokens e processamento em chunks quando necessário.
        
        Args:
            messages: Lista de mensagens no formato {"role": "...", "content": "..."}
            model: Nome do modelo a ser usado
            max_tokens: Número máximo de tokens na resposta
            optimize_tokens: Se deve aplicar otimização de tokens
            use_chunking: Se deve processar em chunks quando necessário
            
        Returns:
            Texto gerado pelo modelo
        """
        logger.info(f"Gerando texto com modelo Fireworks AI {model}")
        
        # Otimiza as mensagens para reduzir o uso de tokens, se habilitado
        if optimize_tokens:
            # Obtem versão otimizada das mensagens e max_tokens recomendado
            optimized_messages, recommended_max_tokens = optimize_token_usage(messages)
            # Usa o max_tokens recomendado, mas respeita o limite do usuário
            messages = optimized_messages
            max_tokens = max(min(max_tokens, 1500), recommended_max_tokens)  # entre 500-1500
            logger.debug(f"Usando max_tokens ajustado: {max_tokens}")
        
        # Extrai o último conteúdo do usuário (para processamento em chunks)
        last_user_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        # Se a mensagem for muito longa e chunking estiver habilitado, processa por chunks
        if last_user_message and use_chunking and len(last_user_message) > 3000:  # ~750 tokens
            logger.info(f"Mensagem longa detectada: {len(last_user_message)} caracteres, processando em chunks")
            
            # Define função de processamento para cada chunk
            async def process_chunk(chunk_content, **kwargs):
                # Substitui a última mensagem do usuário pelo chunk
                chunk_messages = messages.copy()
                for i in range(len(chunk_messages) - 1, -1, -1):
                    if chunk_messages[i]["role"] == "user":
                        chunk_messages[i]["content"] = chunk_content
                        break
                
                # Define os dados da requisição para o chunk
                data = {
                    "messages": chunk_messages,
                    "max_tokens": kwargs.get("max_tokens", max_tokens),
                    "model": model,
                    "temperature": 0.7,
                    "top_p": 0.95,
                }
                
                # Faz a requisição para a API
                result = await self.client._request("POST", "chat/completions", data)
                
                # Extrai o texto da resposta
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0].get("message", {}).get("content", "")
                return ""
            
            # Processa em chunks e retorna o resultado combinado
            return await process_in_chunks(last_user_message, process_chunk)
        
        # Processamento normal (sem chunks)
        # Define os dados da requisição
        data = {
            "messages": messages,
            "max_tokens": max_tokens,
            "model": model,
            "temperature": 0.7,
            "top_p": 0.95,
        }
        
        try:
            # Faz a requisição para a API
            result = await self.client._request("POST", "chat/completions", data)
            
            # Extrai o texto da resposta
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                return content
            else:
                logger.error(f"Formato inesperado de resposta: {result}")
                return "Não foi possível gerar uma resposta. Tente novamente."
                
        except Exception as e:
            logger.error(f"Erro ao gerar texto com Fireworks AI: {str(e)}", exc_info=True)
            raise Exception(f"Falha na geração de texto com Fireworks AI: {str(e)}")
