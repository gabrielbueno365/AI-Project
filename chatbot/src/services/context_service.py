#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serviço de gerenciamento de contexto para conversas.
Controla o histórico de conversas e contexto para processamento.
"""

import logging
from typing import Dict, List, Optional, Any

from src.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


class ContextService:
    """
    Serviço para gerenciar o contexto das conversas.
    Controla o histórico e prepara o contexto para o modelo.
    """
    
    def __init__(self, max_history: int = 10):
        """
        Inicializa o serviço de contexto.
        
        Args:
            max_history: Número máximo de mensagens a manter no histórico
        """
        self.max_history = max_history
        logger.info(f"Serviço de contexto inicializado com max_history={max_history}")
    
    def get_context(self, conversation: Conversation) -> List[Dict[str, str]]:
        """
        Obtém o contexto formatado para uma conversa.
        
        Args:
            conversation: A conversa atual
            
        Returns:
            Lista de mensagens formatadas para o contexto
        """
        # Limita o número de mensagens usadas no contexto
        messages = conversation.get_messages(self.max_history)
        
        # Formata para o formato esperado pelas APIs de LLM
        formatted_messages = []
        
        # Adiciona uma mensagem de sistema para orientar o comportamento do bot
        system_message = {
            "role": "system",
            "content": (
                "Assistente útil, preciso, direto. Respostas claras e objetivas. "
                "Não invente informações quando não souber. "
                "Use linguagem conversacional e natural. "
                "Prefira respostas diretas, sem introduções ou conclusões extensas."
            )
        }
        formatted_messages.append(system_message)
        
        # Adiciona as mensagens da conversa
        for message in messages:
            formatted_messages.append({
                "role": message.role,
                "content": message.content
            })
        
        return formatted_messages
    
    def update_context(self, conversation: Conversation) -> None:
        """
        Atualiza o contexto após uma nova interação.
        Pode implementar lógicas como resumo de contexto para conversas longas.
        
        Args:
            conversation: A conversa atualizada
        """
        # Nesta fase 1, apenas verificamos se o histórico excede o limite
        if len(conversation.messages) > self.max_history * 2:
            logger.info(f"Conversa {conversation.id} excedeu limite de histórico, truncando")
            
            # Mantém apenas as mensagens mais recentes (2x max_history)
            conversation.messages = conversation.messages[-(self.max_history * 2):]
