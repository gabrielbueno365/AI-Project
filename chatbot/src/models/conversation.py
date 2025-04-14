#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modelo para representação de conversas no chatbot.
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from src.models.message import Message


@dataclass
class Conversation:
    """
    Classe para representar uma conversa completa.
    
    Attributes:
        id: Identificador único da conversa
        messages: Lista de mensagens na conversa
        created_at: Timestamp de criação da conversa
        updated_at: Timestamp da última atualização
        metadata: Metadados adicionais
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """
        Adiciona uma mensagem à conversa.
        
        Args:
            message: A mensagem a ser adicionada
        """
        self.messages.append(message)
        self.updated_at = time.time()
    
    def get_messages(self, max_count: Optional[int] = None) -> List[Message]:
        """
        Retorna as mensagens da conversa, opcionalmente limitadas.
        
        Args:
            max_count: Número máximo de mensagens a retornar (do fim para o início)
            
        Returns:
            Lista de mensagens
        """
        if max_count is None:
            return self.messages
        return self.messages[-max_count:]
    
    def get_formatted_history(self, max_count: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Retorna o histórico formatado para uso em APIs de LLM.
        
        Args:
            max_count: Número máximo de mensagens a incluir
            
        Returns:
            Lista de dicionários no formato esperado pelas APIs
        """
        messages_to_format = self.get_messages(max_count)
        return [{"role": msg.role, "content": msg.content} for msg in messages_to_format]
    
    def clear(self) -> None:
        """Limpa todas as mensagens da conversa."""
        self.messages = []
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a conversa para um dicionário.
        
        Returns:
            Dicionário com os dados da conversa
        """
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        Cria uma conversa a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados da conversa
            
        Returns:
            Nova instância de Conversation
        """
        conversation = cls(
            id=data.get("id", str(uuid.uuid4())),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            metadata=data.get("metadata", {}),
        )
        
        for msg_data in data.get("messages", []):
            message = Message.from_dict(msg_data)
            conversation.add_message(message)
        
        return conversation
        
    def to_mcp_format(self) -> Dict[str, Any]:
        """
        Converte a conversa para o formato compatível com MCP.
        Preparação para a futura integração com servidores MCP.
        
        Returns:
            Dicionário no formato MCP
        """
        return {
            "id": self.id,
            "messages": [msg.to_mcp_message() for msg in self.messages],
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_mcp_format(cls, mcp_data: Dict[str, Any]) -> 'Conversation':
        """
        Cria uma conversa a partir de dados no formato MCP.
        
        Args:
            mcp_data: Dados da conversa no formato MCP
            
        Returns:
            Nova instância de Conversation
        """
        conversation = cls(
            id=mcp_data.get("id", str(uuid.uuid4())),
            metadata=mcp_data.get("metadata", {}),
        )
        
        for msg_data in mcp_data.get("messages", []):
            message = Message.from_mcp_message(msg_data)
            conversation.add_message(message)
        
        return conversation
