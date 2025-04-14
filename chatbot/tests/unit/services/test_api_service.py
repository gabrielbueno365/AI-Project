"""
Testes para o serviço de API.
"""

import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.api_service import APIClient, GroqService


@pytest.fixture
def mock_httpx_client():
    """Fixture para mockar o cliente httpx."""
    with patch("httpx.AsyncClient") as mock_client:
        # Configura o mock para ser usado em um contexto assíncrono
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        mock_instance.__aenter__.return_value = mock_instance
        
        # Mock para o método request
        mock_instance.request = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"result": "success"})
        mock_instance.request.return_value = mock_response
        
        yield mock_instance


@pytest.mark.asyncio
async def test_api_client_request_success(mock_httpx_client):
    """Testa uma requisição bem-sucedida via APIClient."""
    # Configura o cliente de API
    client = APIClient(
        base_url="https://api.example.com",
        api_key="test-key",
        timeout=10,
        max_retries=3,
        backoff_factor=0.1,
    )
    
    # Realiza uma requisição
    result = await client._request("GET", "endpoint")
    
    # Verifica se o mock foi chamado corretamente
    mock_httpx_client.request.assert_called_once_with(
        method="GET",
        url="https://api.example.com/endpoint",
        json=None,
        headers={"Authorization": "Bearer test-key"},
    )
    
    # Verifica se o resultado está correto
    assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_api_client_retry_on_failure(mock_httpx_client):
    """Testa o mecanismo de retry do APIClient em caso de falha."""
    # Configura o cliente de API
    client = APIClient(
        base_url="https://api.example.com",
        api_key="test-key",
        timeout=10,
        max_retries=3,
        backoff_factor=0.1,
    )
    
    # Configura o mock para falhar na primeira chamada e suceder na segunda
    http_error = httpx.HTTPStatusError(
        message="Error",
        request=MagicMock(),
        response=MagicMock()
    )
    
    # Primeira chamada falha, segunda tem sucesso
    mock_httpx_client.request.side_effect = [
        http_error,
        mock_httpx_client.request.return_value
    ]
    
    # Realiza uma requisição
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await client._request("GET", "endpoint")
    
    # Verifica se o retry ocorreu (sleep foi chamado)
    mock_sleep.assert_called_once()
    
    # Verifica se o método foi chamado duas vezes
    assert mock_httpx_client.request.call_count == 2
    
    # Verifica se o resultado da segunda chamada foi retornado
    assert result == {"result": "success"}


@pytest.mark.asyncio
async def test_groq_service_generate_text():
    """Testa a geração de texto via GroqService."""
    # Mock para o APIClient
    with patch("src.services.api_service.APIClient") as MockAPIClient:
        # Configura o mock do cliente
        mock_client = AsyncMock()
        MockAPIClient.return_value = mock_client
        
        # Configura a resposta do _request
        mock_client._request.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Generated response"
                    }
                }
            ]
        }
        
        # Cria o serviço Groq
        service = GroqService()
        
        # Mensagens para o teste
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        # Chama o método para gerar texto
        result = await service.generate_text(messages=messages, model="test-model")
        
        # Verifica se a chamada foi correta
        mock_client._request.assert_called_once_with(
            "POST",
            "chat/completions",
            {
                "model": "test-model",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.95,
            }
        )
        
        # Verifica o resultado
        assert result == "Generated response"