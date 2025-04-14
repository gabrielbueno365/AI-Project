#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo principal da aplicação do chatbot.
Gerencia o fluxo de processamento e orquestra os diversos componentes.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from src.core.config import get_settings
from src.models.conversation import Conversation, Message
from src.services.nlp_service import NLPService
from src.services.context_service import ContextService
from src.services.audio_service import AudioService
from src.clients.media import MediaClient

logger = logging.getLogger(__name__)
settings = get_settings()


class ChatbotApp:
    """Classe principal da aplicação do chatbot."""
    
    def __init__(self):
        """Inicializa a aplicação com seus componentes necessários."""
        logger.info("Inicializando aplicação do chatbot")
        self.nlp_service = NLPService()
        self.context_service = ContextService(max_history=settings.max_history_length)
        self.audio_service = AudioService()
        
        # Configura o cliente MCP para o servidor de mídia
        if settings.media_server_cmd:
            logger.info(f"Configurando cliente MCP para servidor de mídia: {settings.media_server_cmd}")
            self.media_client = MediaClient(settings.media_server_cmd.split())
        else:
            logger.warning("Variável MEDIA_SERVER_CMD não configurada. Cliente MCP de mídia não será utilizado.")
            self.media_client = None
            
        self.conversation = Conversation()
    
    async def process_input(self, text: str, file_path: Optional[Path] = None, skip_analysis: bool = False) -> str:
        """
        Processa a entrada do usuário e retorna uma resposta.
        
        Args:
            text: O texto de entrada do usuário
            file_path: Caminho opcional para um arquivo (opcional)
            
        Returns:
            Uma string contendo a resposta do chatbot
        """
        logger.info(f"Processando input do usuário: {text[:50]}...")
        
        # Cria uma nova mensagem de usuário
        user_message = Message(role="user", content=text)
        self.conversation.add_message(user_message)
        
        try:
            # Verifica se há um arquivo para processar
            if file_path is not None:
                response_text = await self._process_file(file_path, text, skip_analysis)
            else:
                # Fluxo normal para processamento de texto
                context = self.context_service.get_context(self.conversation)
                response_text = await self.nlp_service.process_text(text, context)
            
            # Adiciona a resposta do bot à conversa
            bot_message = Message(role="assistant", content=response_text)
            self.conversation.add_message(bot_message)
            
            # Atualiza o contexto com a nova interação
            self.context_service.update_context(self.conversation)
            
            logger.info(f"Resposta gerada: {response_text[:50]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}", exc_info=True)
            # Retorna uma mensagem amigável em caso de erro
            return f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
            
    async def _process_file(self, file_path: Path, text: str, skip_analysis: bool = False) -> str:
        """
        Processa um arquivo com base em seu tipo.
        
        Args:
            file_path: Caminho para o arquivo
            text: Texto de contexto fornecido pelo usuário
            
        Returns:
            Resposta processada
        """
        file_path = Path(file_path)
        
        # Verifica o tipo de arquivo pela extensão
        if file_path.suffix.lower() in settings.allowed_audio_formats:
            return await self._process_audio_file(file_path, text, skip_analysis)
        else:
            return f"Desculpe, o formato de arquivo {file_path.suffix} não é suportado no momento."
    
    async def _process_audio_file(self, file_path: Path, text: str, skip_analysis: bool = False) -> str:
        """
        Processa um arquivo de áudio usando o servidor MCP ou o serviço legado.
        
        Args:
            file_path: Caminho para o arquivo de áudio
            text: Texto de contexto fornecido pelo usuário
            skip_analysis: Se True, pula a análise do conteúdo com LLM
            
        Returns:
            Resposta com a transcrição e análise
        """
        try:
            # Verifica se deve usar o cliente MCP ou o serviço legado
            if self.media_client is not None:
                logger.info(f"Usando cliente MCP para processar áudio: {file_path}")
                try:
                    # Usa o cliente MCP para transcrever o áudio
                    async with self.media_client.connect():
                        result = await self.media_client.transcribe_audio(file_path)
                        logger.info(f"Transcrição via MCP concluída: {len(result['transcription'])} caracteres")
                except Exception as mcp_error:
                    logger.error(f"Erro ao usar cliente MCP: {str(mcp_error)}", exc_info=True)
                    logger.warning("Tentando fallback para serviço legado")
                    result = await self.audio_service.process_audio(file_path)
            else:
                logger.info(f"Usando serviço legado para processar áudio: {file_path}")
                result = await self.audio_service.process_audio(file_path)
            
            # Formata a resposta básica
            response = f"\nÁudio processado: {result.get('filename', file_path.name)}\n"
            response += f"Duração: {result.get('duration', 0):.2f} segundos\n"
            response += f"Formato: {result.get('format', file_path.suffix[1:])}\n\n"
            response += f"**Transcrição**:\n{result['transcription']}\n\n"
            
            # Se houver um texto de contexto e não devemos pular análise, gera uma resposta baseada na transcrição
            if not skip_analysis and text and text.strip() and text.lower() not in ["transcreva", "transcrever", "transcrição"]:
                # Cria um novo prompt com a transcrição e o texto do usuário
                context = self.context_service.get_context(self.conversation)
                prompt = f"Transcrição de áudio: '{result['transcription']}'\n\nComando do usuário: {text}"
                
                # Processa o texto com o serviço de NLP
                analysis = await self.nlp_service.process_text(prompt, context)
                response += f"**Resposta**:\n{analysis}"
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao processar áudio: {str(e)}", exc_info=True)
            return f"Ocorreu um erro ao processar o arquivo de áudio: {str(e)}"
