#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modelo para representação de mensagens no chatbot.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union

# Preparação para futura compatibilidade com MCP
# MCP será instalado na Fase 2
MCP_AVAILABLE = False

# Classes fictícias para compatibilidade
class TextContent:
    def __init__(self, text):
        self.text = text


@dataclass
class Message:
    """
    Classe para representar uma mensagem na conversa.
    
    Attributes:
        role: O papel do emissor ('user', 'assistant', 'system')
        content: O conteúdo da mensagem
        id: Identificador único da mensagem
        timestamp: Timestamp de criação da mensagem
        metadata: Metadados adicionais da mensagem
    """
    
    role: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a mensagem para um dicionário.
        
        Returns:
            Dicionário com os dados da mensagem
        """
        return {
            "role": self.role,
            "content": self.content,
            "id": self.id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Cria uma mensagem a partir de um dicionário.
        
        Args:
            data: Dicionário com os dados da mensagem
            
        Returns:
            Nova instância de Message
        """
        return cls(
            role=data["role"],
            content=data["content"],
            id=data.get("id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def system_message(cls, content: str) -> 'Message':
        """
        Cria uma mensagem do sistema.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            Nova mensagem do sistema
        """
        return cls(role="system", content=content)
    
    @classmethod
    def user_message(cls, content: str) -> 'Message':
        """
        Cria uma mensagem do usuário.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            Nova mensagem do usuário
        """
        return cls(role="user", content=content)
    
    @classmethod
    def assistant_message(cls, content: str) -> 'Message':
        """
        Cria uma mensagem do assistente.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            Nova mensagem do assistente
        """
        return cls(role="assistant", content=content)
        
    def to_mcp_message(self) -> Dict[str, Any]:
        """
        Converte a mensagem para o formato MCP para integração futura.
        
        Returns:
            Mensagem no formato compatível com MCP
        """
        if not MCP_AVAILABLE:
            return self.to_dict()
            
        # Formato básico para futura integração MCP
        return {
            "role": self.role,
            "content": [TextContent(text=self.content)],
            "metadata": self.metadata,
        }
        
    @classmethod
    def from_mcp_message(cls, mcp_message: Dict[str, Any]) -> 'Message':
        """
        Cria uma mensagem a partir do formato MCP.
        
        Args:
            mcp_message: Mensagem no formato MCP
            
        Returns:
            Nova instância de Message
        """
        if not MCP_AVAILABLE:
            return cls.from_dict(mcp_message)
            
        # Extrai o conteúdo como texto
        content = ""
        if "content" in mcp_message and isinstance(mcp_message["content"], list):
            for item in mcp_message["content"]:
                if hasattr(item, "text"):
                    content += item.text
        
        return cls(
            role=mcp_message.get("role", "user"),
            content=content,
            id=mcp_message.get("id", str(uuid.uuid4())),
            timestamp=time.time(),
            metadata=mcp_message.get("metadata", {}),
        )
