"""
Testes para o modelo Conversation.
"""

import pytest
import time
from src.models.message import Message
from src.models.conversation import Conversation


def test_conversation_create():
    """Testa a criação básica de uma conversa."""
    conversation = Conversation()
    
    assert conversation.id is not None
    assert conversation.messages == []
    assert isinstance(conversation.created_at, float)
    assert isinstance(conversation.updated_at, float)
    assert conversation.metadata == {}


def test_add_message():
    """Testa a adição de mensagens à conversa."""
    conversation = Conversation()
    
    # Adiciona uma mensagem
    message1 = Message(role="user", content="First message")
    conversation.add_message(message1)
    
    assert len(conversation.messages) == 1
    assert conversation.messages[0].content == "First message"
    
    # Adiciona outra mensagem
    message2 = Message(role="assistant", content="Response to first")
    conversation.add_message(message2)
    
    assert len(conversation.messages) == 2
    assert conversation.messages[1].content == "Response to first"


def test_get_messages():
    """Testa a recuperação de mensagens com limite."""
    conversation = Conversation()
    
    # Adiciona várias mensagens
    for i in range(5):
        message = Message(role="user" if i % 2 == 0 else "assistant", 
                         content=f"Message {i}")
        conversation.add_message(message)
    
    # Testa recuperação sem limite
    all_messages = conversation.get_messages()
    assert len(all_messages) == 5
    
    # Testa recuperação com limite
    limited_messages = conversation.get_messages(max_count=2)
    assert len(limited_messages) == 2
    assert limited_messages[0].content == "Message 3"
    assert limited_messages[1].content == "Message 4"


def test_get_formatted_history():
    """Testa a recuperação do histórico formatado para APIs."""
    conversation = Conversation()
    
    # Adiciona mensagens
    conversation.add_message(Message(role="system", content="You are helpful"))
    conversation.add_message(Message(role="user", content="Hello"))
    conversation.add_message(Message(role="assistant", content="Hi there"))
    
    # Obtém o histórico formatado
    formatted = conversation.get_formatted_history()
    
    assert len(formatted) == 3
    assert formatted[0]["role"] == "system"
    assert formatted[0]["content"] == "You are helpful"
    assert formatted[1]["role"] == "user"
    assert formatted[2]["role"] == "assistant"


def test_conversation_to_dict():
    """Testa a conversão de Conversation para dicionário."""
    conversation = Conversation(id="test-convo")
    conversation.add_message(Message(role="user", content="Test", id="msg1"))
    
    conv_dict = conversation.to_dict()
    
    assert conv_dict["id"] == "test-convo"
    assert len(conv_dict["messages"]) == 1
    assert conv_dict["messages"][0]["id"] == "msg1"
    assert "created_at" in conv_dict
    assert "updated_at" in conv_dict


def test_conversation_from_dict():
    """Testa a criação de Conversation a partir de um dicionário."""
    data = {
        "id": "restored-convo",
        "messages": [
            {"role": "user", "content": "Question 1", "id": "q1"},
            {"role": "assistant", "content": "Answer 1", "id": "a1"}
        ],
        "created_at": 123456.0,
        "updated_at": 123457.0,
        "metadata": {"source": "test"}
    }
    
    conversation = Conversation.from_dict(data)
    
    assert conversation.id == "restored-convo"
    assert len(conversation.messages) == 2
    assert conversation.messages[0].id == "q1"
    assert conversation.messages[0].content == "Question 1"
    assert conversation.messages[1].id == "a1"
    assert conversation.created_at == 123456.0
    assert conversation.metadata == {"source": "test"}


def test_clear_conversation():
    """Testa a limpeza da conversa."""
    conversation = Conversation()
    conversation.add_message(Message(role="user", content="Test"))
    
    assert len(conversation.messages) == 1
    
    conversation.clear()
    
    assert len(conversation.messages) == 0


def test_mcp_compatibility():
    """Testa os métodos de compatibilidade com MCP."""
    # Cria uma conversa com mensagens
    conversation = Conversation(id="mcp-test")
    conversation.add_message(Message(role="user", content="Test for MCP"))
    conversation.add_message(Message(role="assistant", content="MCP Response"))
    
    # Converte para formato MCP
    mcp_format = conversation.to_mcp_format()
    
    # Verifica se tem campos esperados do MCP
    assert mcp_format["id"] == "mcp-test"
    assert len(mcp_format["messages"]) == 2
    
    # Converte de volta para Conversation
    restored_conversation = Conversation.from_mcp_format(mcp_format)
    
    # Verifica se os dados essenciais foram preservados
    assert restored_conversation.id == "mcp-test"
    assert len(restored_conversation.messages) == 2
    assert restored_conversation.messages[0].role == "user"
    assert "Test for MCP" in restored_conversation.messages[0].content
    assert restored_conversation.messages[1].role == "assistant"