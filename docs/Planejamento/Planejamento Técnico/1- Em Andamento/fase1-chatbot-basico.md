```markdown
# Fase 1: Chatbot Básico (Terminal) - Especificação Técnica (Revisada com Preparação MCP)

## 1. Visão Geral

Esta fase estabelece a base técnica para todo o projeto, implementando uma versão funcional do chatbot via terminal com arquitetura assíncrona. O foco estará em construir uma fundação robusta, **com interfaces modulares que facilitam uma futura refatoração para o Model Context Protocol (MCP)**, suportando as funcionalidades avançadas das fases subsequentes.

## 2. Arquitetura

### 2.1 Diagrama de Alto Nível (com Mapeamento MCP Conceitual)
```

┌─────────────────────────────────────────────────────────────┐
│ Interface Terminal │
│ (main.py - prompt_toolkit, rich) │
└───────────────────────────────┬─────────────────────────────┘
│
┌───────────────────────────────▼─────────────────────────────┐
│ Controlador Principal (core/app.py - ChatbotApp) │
│ **(Futuro MCP Host)** │
│ (Async Event Loop) │
└───┬───────────────┬────────────────────┬──────────────┬─────┘
│ (Chamada Método)│ (Chamada Método) │ (Chamada Método) │ (Chamada Método)
┌───▼───┐ ┌────▼────┐ ┌────▼─────┐ ┌────▼────┐
│ Gestor │ │ Processa│ │ Gestor │ │ Cliente │
│ de │ │ dor NLP│ │ de │ │ API │
│ Estado │ │(**Server**)| │ Contexto │ │ (**Server**)|
│(**Server**)│ │(**MCP Futuro**)| │(**MCP Futuro**)| │(**MCP Futuro**)|
│(Simples)│ │(services/nlp) │ │(services/ctx)| │(services/api)|
└───────┘ └─────────┘ └──────────┘ └─────────┘

```
*Nesta fase, a comunicação entre o Controlador e os Serviços é feita via chamadas de método Python assíncronas, mas as interfaces são projetadas para serem facilmente substituídas por chamadas MCP (`tool`/`resource`) no futuro.*

### 2.2 Componentes Principais

1.  **Interface Terminal**: Camada de interação com o usuário (`main.py`, usando `prompt_toolkit`, `rich`).
2.  **Controlador Principal**: Orquestrador assíncrono central (`core/app.py`). **Atua como o futuro MCP Host conceitual.**
3.  **Gestor de Estado**: Mantém o estado básico da aplicação (ex: modo de operação, se houver). Implementado como parte de `core/app.py` inicialmente. **Pode evoluir para um futuro `mcp-server-state`.**
4.  **Processador de NLP**: Módulo inicial (`services/nlp_service.py`) para análise e geração de texto, interagindo com `api_service`. **Potencial futuro `mcp-server-nlp`.**
5.  **Gestor de Contexto**: Rastreia o contexto da conversa atual (`services/context_service.py`). **Potencial futuro `mcp-server-memory` (muito básico nesta fase).**
6.  **Cliente API**: Interface para APIs externas (`services/api_service.py`, usando `httpx`), inicialmente para Hugging Face e Groq. **Potencial futuro `mcp-server-api-gateway` ou servidores específicos.**

### 2.3 Fluxo de Dados

1.  Usuário insere texto no terminal (`main.py`).
2.  O controlador principal (`core/app.py`) recebe a entrada assincronamente.
3.  O controlador chama `nlp_service.process_text(text)` (método Python).
4.  `nlp_service` pode chamar `api_service.query_model(...)` para consultar modelos externos (HF/Groq).
5.  `api_service` usa `httpx` para fazer a chamada de API real.
6.  A resposta retorna ao `nlp_service` e depois ao controlador.
7.  O controlador chama `context_service.add_interaction(...)` para salvar a troca.
8.  A resposta final é formatada pelo controlador e enviada para a Interface Terminal (`rich`).

## 3. Especificações Técnicas

### 3.1 Estrutura do Projeto (Detalhada)

```

/chatbot
├── /src
│ ├── /core
│ │ ├── **init**.py
│ │ ├── app.py # Aplicação principal (ChatbotApp - Futuro Host)
│ │ ├── config.py # Configurações (lê .env)
│ │ └── logging.py # Configuração de logging
│ ├── /models # Modelos Pydantic
│ │ ├── **init**.py
│ │ ├── message.py # Modelo para mensagens (Alinhar com MCP Message se possível)
│ │ └── conversation.py # Modelo para conversas/contexto
│ ├── /services # **Módulos com Interfaces estilo MCP**
│ │ ├── **init**.py
│ │ ├── nlp_service.py # Lógica NLP, chama api_service
│ │ ├── context_service.py # Gestão de memória simples in-memory
│ │ └── api_service.py # Cliente HTTP para HF/Groq com retry/circuit breaker
│ ├── /utils
│ │ ├── **init**.py
│ │ ├── async_helpers.py # Funções utilitárias async
│ │ └── error_handlers.py # Classes/funções para tratamento de erro
│ └── main.py # Ponto de entrada, loop de terminal
├── /tests
│ ├── **init**.py
│ ├── conftest.py
│ ├── /unit # Testes para cada service, util, model
│ │ ├── /core
│ │ ├── /services
│ │ └── /utils
│ └── /integration # Testes para core/app.py (mockando services)
├── /docs
│ ├── architecture.md # **Incluir diagrama e explicação da visão MCP**
│ └── development.md
├── .gitignore
├── pyproject.toml # Configuração Poetry
├── .pre-commit-config.yaml # Hooks de pre-commit
└── README.md

````

### 3.2 Stack Tecnológico (Completo)

-   **Core**: Python 3.11+, Poetry, Asyncio.
-   **Interface Terminal**: `rich`, `prompt_toolkit`.
-   **Comunicação API**: `httpx` (cliente async).
-   **NLP Inicial**: Bibliotecas cliente `huggingface_hub` (opcional, se não usar só `httpx`) e `groq` (para interagir com as respectivas APIs via `api_service`).
-   **Validação**: `Pydantic` (para os modelos em `/models`).
-   **Configuração**: `python-dotenv` (para carregar `.env`).
-   **Testes**: `pytest`, `pytest-asyncio`, `coverage`, `unittest.mock`.
-   **Qualidade**: `black`, `flake8`, `mypy`, `pre-commit`.
-   **MCP**: **`mcp[cli]`** (instalado para preparar o ambiente, mesmo que não usado diretamente pelo chatbot nesta fase).

### 3.3 Autenticação e Segurança

-   Chaves de API (HF, Groq) lidas exclusivamente de variáveis de ambiente.
-   Uso do arquivo `.env` (adicionado ao `.gitignore`) para facilitar o desenvolvimento local.
-   Logging configurado para **não** registrar chaves de API ou dados sensíveis.

### 3.4 Gerenciamento de Erros

-   Classe `APIClient` (`api_service.py`) implementará retries com backoff exponencial e um circuit breaker simples.
-   Captura de exceções no loop principal (`main.py`) para evitar que o chatbot quebre completamente.
-   Logging detalhado de erros, incluindo stack traces quando em modo DEBUG.

## 4. Interfaces e APIs

### 4.1 Interface de Linha de Comando (Conforme Original)

O código em `main.py` permanece como no plano original, utilizando `prompt_toolkit` para entrada e `rich` para saída, gerenciado por um loop `asyncio`.

```python
# main.py (exemplo mantido)
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from core.app import ChatbotApp # Assumindo que ChatbotApp está em core/app.py

console = Console()

async def main():
    session = PromptSession()
    app = ChatbotApp() # Instancia a lógica principal

    console.print("[bold blue]Chatbot Iniciado[/bold blue]")
    console.print("Digite 'sair' para encerrar\n")

    while True:
        with patch_stdout():
            try:
                user_input = await session.prompt_async("Você > ")
            except (EOFError, KeyboardInterrupt):
                break

        if user_input.lower() in ('sair', 'exit', 'quit'):
            break

        try:
            # O processamento agora é orquestrado pelo ChatbotApp
            with console.status("[bold green]Processando..."):
                response = await app.process_input(user_input)

            # Usar rich para formatar a saída
            console.print(f"\nChatbot > [bold green]{response}[/bold green]\n")
        except Exception as e:
            console.print(f"[bold red]Erro Inesperado: {str(e)}[/bold red]")
            # Logar o erro completo para debug
            logger.exception("Erro não tratado no loop principal") # Supondo logger configurado

    console.print("[bold blue]Chatbot Encerrado[/bold blue]")

if __name__ == "__main__":
    # Configurar logging antes de rodar
    from core.logging import setup_logging
    setup_logging()
    logger = logging.getLogger(__name__) # Pegar logger após setup
    asyncio.run(main())

````

### 4.2 Interface com APIs Externas (Cliente API - Conforme Original)

A classe `APIClient` em `services/api_service.py` encapsula as chamadas `httpx` com retry e circuit breaker.

```python
# services/api_service.py (resumo, conforme original)
import httpx
import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 10):
        self.base_url = base_url
        # Adicionar lógica para diferentes métodos de auth (Bearer, etc.)
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.timeout = timeout
        # Instanciar o cliente httpx aqui, mas abri-lo/fechá-lo com async with
        # self.client = httpx.AsyncClient(timeout=timeout) # Melhor gerenciar no __aenter__/__aexit__
        self._failure_count = 0
        self._circuit_open_until: Optional[float] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def _request(self, method: str, endpoint: str,
                      data: Optional[Dict[str, Any]] = None,
                      max_retries: int = 3) -> Dict[str, Any]:

        current_time = asyncio.get_event_loop().time()
        if self._circuit_open_until and current_time < self._circuit_open_until:
            logger.warning(f"Circuit open for {self.base_url}, skipping request")
            raise Exception("Service temporarily unavailable (circuit open)")
        elif self._circuit_open_until and current_time >= self._circuit_open_until:
            logger.info(f"Circuit breaker reset for {self.base_url}")
            self._circuit_open_until = None # Fechar circuito
            self._failure_count = 0

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = await self.client.request(
                    method,
                    url,
                    json=data,
                    headers=self.headers
                )
                response.raise_for_status() # Levanta exceção para 4xx/5xx

                # Resetar contador em sucesso
                if self._failure_count > 0:
                    logger.info(f"Request successful, resetting failure count for {self.base_url}")
                    self._failure_count = 0
                return response.json()

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                retry_count += 1
                self._failure_count += 1
                logger.warning(f"Request failed ({retry_count}/{max_retries}): {e}")

                if self._failure_count >= 5: # Limite para abrir o circuito
                    open_duration = 30 # Segundos
                    self._circuit_open_until = asyncio.get_event_loop().time() + open_duration
                    logger.error(f"Opening circuit for {self.base_url} for {open_duration}s after {self._failure_count} failures")
                    raise Exception(f"Service unavailable: {str(e)} (circuit open)")

                if retry_count < max_retries:
                    backoff = 0.1 * (2 ** retry_count)
                    logger.info(f"Retrying in {backoff:.2f}s...")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Request failed after {max_retries} retries.")
                    raise Exception(f"Failed after {max_retries} retries: {str(e)}") # Re-levanta a exceção final

        # Se sair do loop sem sucesso (não deve acontecer devido ao raise acima)
        raise Exception(f"Request failed definitively for {url}")

    # Método exemplo para chamar um modelo (adaptar à API real)
    async def query_model(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Query an LLM model. Adapte o endpoint e payload à API real."""
        # Este é um exemplo genérico, adapte para Groq ou HF
        endpoint = "chat/completions" # Exemplo API OpenAI/Groq
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs # Passa outros parâmetros como temperature, max_tokens
        }
        # Pode precisar adaptar o payload para a API específica do HF
        return await self._request("POST", endpoint, data=data)

```

## 5. Implementação do NLP Básico

### 5.1 Integração Inicial com Hugging Face e Groq (Via `api_service`)

O `nlp_service.py` usará a instância do `APIClient` para se comunicar com as APIs.

```python
# services/nlp_service.py (exemplo, mantendo a lógica original)
import logging
from .api_service import APIClient
from core.config import settings # Assumindo que settings está em core.config

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        # Criar instâncias do APIClient para cada serviço
        # Tratar caso as chaves não estejam definidas
        self.hf_client = None
        if settings.HUGGING_FACE_API_KEY:
             self.hf_client = APIClient(
                 base_url="https://api-inference.huggingface.co/models",
                 api_key=settings.HUGGING_FACE_API_KEY
             )
        else:
            logger.warning("HUGGINGFACE_API_KEY não definida. Funcionalidades HF desabilitadas.")

        self.groq_client = None
        if settings.GROQ_API_KEY:
            self.groq_client = APIClient(
                base_url="https://api.groq.com/openai/v1", # Endpoint estilo OpenAI
                api_key=settings.GROQ_API_KEY
            )
        else:
            logger.warning("GROQ_API_KEY não definida. Funcionalidades Groq desabilitadas.")

    async def process_text(self, text: str) -> str:
        """Processa o texto, decidindo qual API usar."""
        # Lógica simples: usar Groq se disponível, senão HF.
        # Pode ser mais sofisticada (custo, velocidade, tipo de tarefa).
        if self.groq_client:
            try:
                async with self.groq_client as client:
                    # Adapte 'model' e 'kwargs' conforme necessário
                    response = await client.query_model(
                        prompt=text,
                        model=settings.GROQ_MODEL_ID # Ex: "llama3-8b-8192"
                        # Passe outros parâmetros se necessário
                    )
                    # Extraia o texto da resposta do Groq (pode variar)
                    return response['choices'][0]['message']['content']
            except Exception as e:
                logger.error(f"Erro ao chamar Groq: {e}. Tentando Hugging Face.")
                # Fallback para Hugging Face se Groq falhar (opcional)

        if self.hf_client:
             try:
                async with self.hf_client as client:
                    # Adapte 'model' e 'kwargs' para a API de inferência HF
                    response = await client.query_model(
                        prompt=text, # A API HF pode usar 'inputs' em vez de 'prompt'
                        model=settings.DEFAULT_HF_MODEL # Ex: "google/flan-t5-base"
                        # Passe outros parâmetros HF se necessário
                    )
                     # Extraia o texto da resposta do HF (pode variar)
                    # Ex: Pode ser uma lista, pegar o primeiro elemento e a chave correta
                    if isinstance(response, list) and len(response) > 0:
                        return response[0].get('generated_text', "Erro ao extrair resposta HF.")
                    return str(response) # Fallback
             except Exception as e:
                logger.error(f"Erro ao chamar Hugging Face: {e}")
                return "Desculpe, não consegui processar sua solicitação via Hugging Face."
        else:
            logger.error("Nenhum cliente de API (Groq ou HF) está configurado.")
            return "Desculpe, nenhum serviço de IA está configurado no momento."

    # Outros métodos como analyze, generate_response podem chamar process_text
    # ou ter lógicas mais específicas para usar HF ou Groq dependendo da tarefa.
    async def analyze(self, text: str) -> dict:
        # Exemplo: Poderia usar um modelo de classificação HF aqui
        # ou extrair intenção via Groq
        logger.info(f"Analisando (simulado): {text}")
        return {"intent": "desconhecida", "entities": []}

    async def generate_response(self, prompt: str) -> str:
        # Usa a lógica principal de process_text para gerar
        return await self.process_text(prompt)

```

## 6. Testes (Manter Foco Técnico)

### 6.1 Testes Unitários (Conforme Original)

Testar cada classe (`APIClient`, `NLPService`, `ContextService`) isoladamente, usando `unittest.mock.AsyncMock` para simular chamadas externas (`httpx`, APIs).

```python
# Exemplo: tests/unit/services/test_nlp_service.py
import pytest
from unittest.mock import AsyncMock, patch
from services.nlp_service import NLPService
from core.config import settings # Para mockar as chaves

# Mock settings antes de importar NLPService se necessário
settings.GROQ_API_KEY = "fake_groq_key"
settings.HUGGING_FACE_API_KEY = "fake_hf_key"
settings.GROQ_MODEL_ID = "mock_groq_model"
settings.DEFAULT_HF_MODEL = "mock_hf_model"

@pytest.fixture
def mock_api_client():
    # Mock para a classe APIClient
    mock = AsyncMock()
    mock.query_model = AsyncMock()
    # Configurar __aenter__ e __aexit__ para o 'async with'
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = None
    return mock

@pytest.fixture
def nlp_service_with_mocks(mock_api_client):
    # Patch a __init__ para injetar mocks ou use DI
    with patch('services.nlp_service.APIClient', return_value=mock_api_client):
        service = NLPService()
        # Atribuir mocks diferentes para HF e Groq se necessário
        service.groq_client = mock_api_client
        service.hf_client = mock_api_client # Usar o mesmo mock para simplicidade aqui
        return service, mock_api_client

@pytest.mark.asyncio
async def test_process_text_uses_groq_first(nlp_service_with_mocks):
    service, mock_client = nlp_service_with_mocks
    mock_response = {"choices": [{"message": {"content": "Resposta Groq"}}]}
    mock_client.query_model.return_value = mock_response

    result = await service.process_text("Uma pergunta qualquer")

    assert result == "Resposta Groq"
    mock_client.query_model.assert_called_once_with(
        prompt="Uma pergunta qualquer", model=settings.GROQ_MODEL_ID
    )

# Adicionar mais testes para fallback, erros, etc.
```

### 6.2 Testes de Integração (Conforme Original)

Testar o fluxo completo em `ChatbotApp`, mockando as respostas no nível dos `services` (ex: mockar `nlp_service.process_text`).

```python
# Exemplo: tests/integration/test_app.py
import pytest
from unittest.mock import AsyncMock, patch
from core.app import ChatbotApp

@pytest.fixture
def app_with_mocks():
    with patch('core.app.NLPService') as MockNLP, \
         patch('core.app.ContextService') as MockContext:
        # Configurar mocks
        mock_nlp_instance = MockNLP.return_value
        mock_nlp_instance.process_text = AsyncMock(return_value="Resposta NLP Mock")
        mock_nlp_instance.analyze = AsyncMock(return_value={}) # Adicionar mocks para outros métodos

        mock_context_instance = MockContext.return_value
        mock_context_instance.get_history = AsyncMock(return_value=[])
        mock_context_instance.add_interaction = AsyncMock()

        # Instanciar app (agora usará mocks)
        app = ChatbotApp()
        return app, mock_nlp_instance, mock_context_instance

@pytest.mark.asyncio
async def test_app_process_input_flow(app_with_mocks):
    app, mock_nlp, mock_context = app_with_mocks

    response = await app.process_input("Pergunta teste")

    assert response == "Resposta NLP Mock"
    # Verificar se os métodos dos serviços mockados foram chamados
    mock_nlp.analyze.assert_called_once_with("Pergunta teste")
    mock_context.get_history.assert_called_once()
    # A chamada exata para generate_response depende da lógica interna de process_input
    mock_nlp.generate_response.assert_called_once()
    mock_context.add_interaction.assert_any_call("user", "Pergunta teste")
    mock_context.add_interaction.assert_any_call("assistant", "Resposta NLP Mock")
```

## 7. Configuração do Ambiente

### 7.1 Poetry Configuration (`pyproject.toml` - Atualizado)

```toml
[tool.poetry]
name = "chatbot-inteligente"
version = "0.1.0"
description = "Um chatbot inteligente com capacidades avançadas"
authors = ["Seu Nome <seu.email@exemplo.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
rich = "^13.4.2"
prompt-toolkit = "^3.0.38"
httpx = "^0.24.1"
# transformers = "^4.30.2" # Se for usar pipelines locais diretamente (adiado)
groq = "^0.9.0" # SDK Oficial Groq
huggingface-hub = "^0.23.0" # Para interagir com HF Hub se necessário
python-dotenv = "^1.0.0"
pydantic = "^2.7.1"
langchain-groq = "^0.1.6" # Dependências adicionadas na fase 1
langchain-huggingface = "^0.0.3"
langchain = "^0.2.5"
langchain-community = "^0.2.5"
mcp = { extras = ["cli"], version = "^1.5.0" } # **MCP Adicionado**


[tool.poetry.group.dev.dependencies]
pytest = "^7.3.1"
pytest-asyncio = "^0.21.0"
black = "^23.3.0"
flake8 = "^6.0.0"
mypy = "^1.3.0"
pre-commit = "^3.3.3"
coverage = "^7.2.7"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 7.2 Environment Variables (`.env` - Conforme Original)

```
# API Keys
HUGGING_FACE_API_KEY=your_hugging_face_key_here
GROQ_API_KEY=your_groq_key_here

# Logging
LOG_LEVEL=INFO

# Application Settings
MAX_HISTORY_LENGTH=10
DEFAULT_HF_MODEL="google/flan-t5-base" # Exemplo modelo HF
GROQ_MODEL_ID="llama3-8b-8192" # Exemplo modelo Groq
```

## 8. Plano de Implementação (Mantido Conforme Revisado)

- **Total**: ~9-14 dias de trabalho.

## 9. Riscos e Mitigações (Mantido Conforme Revisado)

- Foco na mitigação da **Sobrecarga conceitual com MCP cedo** através do design de interfaces e adiamento da implementação completa.

## 10. Próximos Passos Imediatos (Mantido Conforme Revisado)

- Foco na configuração do ambiente **incluindo `mcp[cli]`** e no design das interfaces dos _services_.

## 11. Conclusão (Mantida Conforme Revisada)

Esta Fase 1 revisada equilibra a necessidade de entregar um chatbot básico funcional com a visão de longo prazo de uma arquitetura modular baseada em MCP. Mantemos os detalhes técnicos essenciais do plano original, mas estruturamos o código e as interfaces de forma a facilitar a transição para servidores MCP nas próximas fases.
