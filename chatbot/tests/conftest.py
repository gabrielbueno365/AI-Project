"""
Configurações e fixtures comuns para testes.
"""

import os
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

# Define uma fixture para suprimir logs nos testes
@pytest.fixture(autouse=True)
def suppress_logs():
    """Suprime logs durante os testes para limpar a saída."""
    with patch("logging.Logger.debug"), \
         patch("logging.Logger.info"), \
         patch("logging.Logger.warning"), \
         patch("logging.Logger.error"), \
         patch("logging.Logger.critical"):
        yield


# Define uma fixture para mockar as configurações
@pytest.fixture
def mock_settings():
    """Mock para as configurações da aplicação."""
    with patch("src.core.config.get_settings") as mock_get_settings:
        mock_settings = mock_get_settings.return_value
        
        # Define valores padrão para testes
        mock_settings.hugging_face_api_key = "test-hf-key"
        mock_settings.groq_api_key = "test-groq-key"
        mock_settings.max_history_length = 5
        mock_settings.default_model = "test-model"
        mock_settings.default_groq_model = "test-groq-model"
        mock_settings.default_huggingface_model = "test-hf-model"
        mock_settings.request_timeout = 5
        mock_settings.max_retries = 2
        mock_settings.backoff_factor = 0.1
        mock_settings.allowed_audio_formats = [".mp3", ".wav"]
        
        yield mock_settings


# Fixture para mockar o NLPService
@pytest.fixture
def mock_nlp_service():
    """Mock para o serviço NLP."""
    with patch("src.services.nlp_service.NLPService") as MockNLPService:
        mock_service = AsyncMock()
        MockNLPService.return_value = mock_service
        
        # Define comportamentos padrão
        mock_service.process_text.return_value = "Processed text response"
        
        yield mock_service


# Fixture para mockar o ContextService
@pytest.fixture
def mock_context_service():
    """Mock para o serviço de contexto."""
    with patch("src.services.context_service.ContextService") as MockContextService:
        mock_service = AsyncMock()
        MockContextService.return_value = mock_service
        
        # Define comportamentos padrão
        mock_service.get_context.return_value = []
        
        yield mock_service


# Fixture para mockar dotenv
@pytest.fixture(autouse=True)
def mock_dotenv():
    """Mock para impedir que dotenv realmente carregue arquivos durante testes."""
    with patch("dotenv.load_dotenv"):
        yield