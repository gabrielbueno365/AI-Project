"""
Testes para o modelo Message.
"""

import pytest
import time
from src.models.message import Message


def test_message_create():
    """Testa a criação básica de uma mensagem."""
    message = Message(role="user", content="Test message")
    
    assert message.role == "user"
    assert message.content == "Test message"
    assert message.id is not None
    assert isinstance(message.timestamp, float)
    assert message.metadata == {}


def test_message_to_dict():
    """Testa a conversão de Message para dicionário."""
    message = Message(role="user", content="Test message", id="test-id", timestamp=123456.0)
    
    message_dict = message.to_dict()
    assert message_dict["role"] == "user"
    assert message_dict["content"] == "Test message"
    assert message_dict["id"] == "test-id"
    assert message_dict["timestamp"] == 123456.0
    assert "metadata" in message_dict


def test_message_from_dict():
    """Testa a criação de Message a partir de um dicionário."""
    data = {
        "role": "assistant",
        "content": "Test response",
        "id": "test-id-2",
        "timestamp": 123457.0,
        "metadata": {"source": "test"}
    }
    
    message = Message.from_dict(data)
    
    assert message.role == "assistant"
    assert message.content == "Test response"
    assert message.id == "test-id-2"
    assert message.timestamp == 123457.0
    assert message.metadata == {"source": "test"}


def test_message_helper_methods():
    """Testa os métodos auxiliares de criação de mensagens."""
    system_msg = Message.system_message("System instruction")
    assert system_msg.role == "system"
    assert system_msg.content == "System instruction"
    
    user_msg = Message.user_message("User query")
    assert user_msg.role == "user"
    assert user_msg.content == "User query"
    
    assistant_msg = Message.assistant_message("Assistant response")
    assert assistant_msg.role == "assistant"
    assert assistant_msg.content == "Assistant response"


def test_message_mcp_compatibility():
    """Testa os métodos de compatibilidade com MCP."""
    # Cria uma mensagem normal
    message = Message(role="user", content="Test message for MCP", id="test-mcp-id")
    
    # Converte para formato MCP
    mcp_format = message.to_mcp_message()
    
    # Verifica se tem campos esperados do MCP
    assert "role" in mcp_format
    assert mcp_format["role"] == "user"
    
    # Converte de volta para Message
    restored_message = Message.from_mcp_message(mcp_format)
    
    # Verifica se os dados essenciais foram preservados
    assert restored_message.role == "user"
    assert "Test message for MCP" in restored_message.content