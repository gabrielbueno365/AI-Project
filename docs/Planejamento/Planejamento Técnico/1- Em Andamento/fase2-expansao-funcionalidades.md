```markdown
# Fase 2: Expansão de Funcionalidades Essenciais via Servidores MCP - Especificação Técnica Revisada

## 1. Visão Geral

Esta fase expande significativamente as capacidades do chatbot, implementando processamento de multimídia, leitura de documentos, RAG e busca web como **Servidores MCP dedicados**. A arquitetura evolui para um modelo Host-Servidor, onde o Chatbot Core (Controlador Principal) atua como o **MCP Host**, orquestrando chamadas para servidores especializados via **MCP Clients internos**, utilizando predominantemente o transporte **stdio**. Isso estabelece a modularidade e prepara para futuras integrações e otimizações.

## 2. Arquitetura (Com Servidores MCP Implementados)

### 2.1 Diagrama de Alto Nível (Fase 2 - Implementação MCP)
```

┌─────────────────────────────────────────────────────────────┐
│ Interface Terminal (main.py) │
└───────────────────────────────┬─────────────────────────────┘
│
┌───────────────────────────────▼─────────────────────────────┐
│ Controlador Principal / **MCP Host** │
│ (core/app.py - ChatbotApp - Async) │
│ ┌───────────────────────────┐ ┌─────────────────────────┐ │
│ │ **MCP Clients Internos** │ │ Gestor Estado/Contexto │ │
│ │ (clients/filesystem.py...)│ │ (core/app.py ou serviço)│ │
│ └───────────▲─────────────┘ └───────────┬─────────────┘ │
└───────────────│───────────────────────────│───────────────┘
│ (Chamadas MCP via stdio) │ (Acesso Interno)
┌───────────────┼───────────────────────────┤
│ │ │
│ ┌───────────▼───────────┐ ┌───────────▼───────────┐ .......... (Outros Servidores)
│ │**mcp-server-filesystem**│ │ **mcp-server-rag** │
│ │ (Python, FastMCP) │ │ (Python, FastMCP) │
│ │ - Lê/Parseia Arquivos │ │ - Indexa/Busca Vetor │
│ │ - Usa: DOCLING, │ │ - Usa: Qdrant Client,│
│ │ python-magic │ │ HF Embeddings │
│ └───────────┬───────────┘ └───────────┬───────────┘
│ │ (stdout/stdin) │ (stdout/stdin)
└───────────────┴───────────────────────────┘

````
*Nota: Servidores de Mídia, Embeddings e Web Search/Scraping serão adicionados similarmente.*

### 2.2 Componentes Principais (Atualizado)

1.  **Controlador Principal (Host)**: `core/app.py` - Orquestra o fluxo, instancia e gerencia os **MCP Clients**, lida com a lógica da conversa de alto nível.
2.  **Interface Terminal**: `main.py` - Mantida.
3.  **MCP Clients Internos**: `src/clients/*.py` - Classes Python que encapsulam a comunicação (via `mcp` library) com cada servidor MCP específico (Filesystem, RAG, Mídia, Embeddings, Web).
4.  **Servidor MCP: `mcp-server-filesystem` (Novo/Detalhado)**
    *   **Tecnologia:** Python, `FastMCP`, `docling`, `python-magic`.
    *   **Interface MCP:**
        *   *Tools:* `get_file_info(path: str)`, `read_text_file(path: str)`, `read_binary_file(path: str)`, `list_directory(path: str, pattern: str = '*')`, `parse_document(path: str) -> dict` (retorna texto e metadados extraídos pelo DOCLING).
        *   *Resources:* `file://{absolute_path}` (expostos dinamicamente ou via `list_directory`).
5.  **Servidor MCP: `mcp-server-rag` (Novo/Detalhado)**
    *   **Tecnologia:** Python, `FastMCP`, `qdrant-client`, `langchain-huggingface`.
    *   **Interface MCP:**
        *   *Tools:* `index_text(text: str, metadata: dict)`, `index_uri(uri: str)` (chama internamente o filesystem server), `semantic_search(query_text: str, k: int = 3) -> list[dict]` (gera embedding internamente ou chama outro server), `check_indexed(uri: str) -> bool`.
6.  **Servidor MCP: `mcp-server-embeddings` (Novo/Detalhado)**
    *   **Tecnologia:** Python, `FastMCP`, `langchain-huggingface` (para `HuggingFaceEmbeddings`, ex: `sentence-transformers/all-MiniLM-L6-v2`).
    *   **Interface MCP:**
        *   *Tools:* `generate_embedding(text: str) -> list[float]`, `generate_batch_embeddings(texts: list[str]) -> list[list[float]]`.
7.  **Servidor MCP: `mcp-server-media` (Novo/Detalhado)**
    *   **Tecnologia:** Python, `FastMCP`, `ffmpeg-python`, `httpx` (para API Whisper).
    *   **Interface MCP:**
        *   *Tools:* `transcribe_audio(file_uri: str) -> str` (lê via filesystem server, chama API Whisper HF), `extract_audio_uri(video_uri: str) -> str` (lê via filesystem, usa ffmpeg, salva temp, retorna nova URI `file://`).
        *   *(Fase futura): `analyze_image(file_uri: str)` (usaria CLIP)*
8.  **Servidor MCP: `mcp-server-fetch` (Novo - Usar Oficial)**
    *   **Tecnologia:** Usar o servidor oficial `@modelcontextprotocol/server-fetch` via npx.
    *   **Interface MCP:**
        *   *Tools:* `fetch(url: str, max_length: int = 5000, raw: bool = False)` (retorna conteúdo da página, idealmente como Markdown).

### 2.3 Fluxo de Dados Revisado (Busca Web)

1.  Usuário pergunta: "Quais as últimas notícias sobre IA?"
2.  **Host (`ChatbotApp`)** recebe a pergunta.
3.  Host (via client `web_client`) chama `tool: fetch` no **`mcp-server-fetch`** com `url="https://news.google.com/search?q=AI"` (exemplo).
4.  `mcp-server-fetch` busca a página, extrai o conteúdo principal como Markdown e retorna ao Host.
5.  Host pode (opcionalmente) chamar `tool: generate_response` no `nlp_service` (que usa Groq via `api_service`) com o contexto do Markdown para sumarizar ou responder.
6.  Host envia a resposta final para a Interface Terminal.

## 3. Especificações Técnicas

### 3.1 Estrutura do Projeto (Conforme Revisão Fase 1)

-   Adicionar diretórios em `/mcp_servers/` para cada novo servidor (`rag_server`, `media_server`, `embeddings_server`). O `fetch_server` é externo (npx).
-   Adicionar arquivos de cliente em `/src/clients/` (`rag.py`, `media.py`, `embeddings.py`, `web.py`).

### 3.2 Stack Tecnológico (Detalhado por Componente)

-   **Host Principal**: Python 3.11+, Asyncio, Poetry.
-   **Servidores MCP**: Cada servidor MCP terá seu próprio ambiente Poetry com `pyproject.toml` individualizado.
-   **`mcp-server-filesystem`**: Python, `FastMCP`, `docling`, `python-magic`.
-   **`mcp-server-rag`**: Python, `FastMCP`, `qdrant-client`, `langchain-huggingface`.
-   **`mcp-server-media`**: Python, `FastMCP`, `ffmpeg-python`, `httpx`.
-   **`mcp-server-embeddings`**: Python, `FastMCP`, `langchain-huggingface`.
-   **`mcp-server-fetch`**: Node.js (via `npx`).
-   **Banco Vetorial**: Qdrant (local, via Docker ou binário).

**Nota**: Para detalhes sobre como usar o Poetry no projeto, consulte o guia em `chatbot/docs/architecture/poetry_guide.md`.

### 3.3 Implementação dos Servidores e Clientes

#### Servidores (`/mcp_servers/.../src/server.py`)

-   Usar `FastMCP` para definir a interface.
-   Implementar a lógica dentro de funções decoradas com `@mcp.tool()` ou `@mcp.resource()`.
-   Manter servidores focados em sua tarefa específica.
-   Configurar via variáveis de ambiente ou argumentos CLI (ex: path do Qdrant, API keys se necessário internamente).

**Exemplo: Esqueleto `mcp-server-rag/src/server.py`**

```python
from mcp.server.fastmcp import FastMCP, Context
from qdrant_client import QdrantClient, models
from langchain_huggingface import HuggingFaceEmbeddings # Ou outro cliente
from typing import List, Dict, Any

# --- Configuração (Ex: via env vars ou args) ---
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "chatbot_knowledge"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# -------------------------------------------------

# Inicializa o cliente Qdrant e o modelo de embedding
qdrant_client = QdrantClient(url=QDRANT_URL)
embeddings_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
# Garante que a coleção exista (pode ser feito no lifespan)
qdrant_client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=models.VectorParams(size=embeddings_model.client.get_sentence_embedding_dimension(), distance=models.Distance.COSINE)
)

mcp = FastMCP(name="RAG Server")

@mcp.tool()
async def index_text(text: str, metadata: Dict[str, Any], ctx: Context) -> bool:
    """Indexa um texto e seus metadados no Qdrant."""
    try:
        # Gerar embedding (poderia chamar mcp-server-embeddings via context)
        # Para simplicidade aqui, fazemos direto:
        vectors = embeddings_model.embed_documents([text])
        if not vectors: return False

        # Criar ponto para Qdrant
        doc_id = metadata.get("source_uri", str(hash(text))) # Usar URI ou hash
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=doc_id,
                    vector=vectors[0],
                    payload={"text": text, **metadata}
                )
            ],
            wait=True
        )
        ctx.info(f"Texto indexado com ID: {doc_id}")
        return True
    except Exception as e:
        ctx.error(f"Erro ao indexar: {e}")
        return False

@mcp.tool()
async def semantic_search(query_text: str, k: int = 3, ctx: Context) -> List[Dict[str, Any]]:
    """Realiza busca semântica no Qdrant."""
    try:
        query_vector = embeddings_model.embed_query(query_text)
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=k,
            with_payload=True # Para retornar o texto e metadados
        )
        # Formatar resultado
        results = [
            {"id": hit.id, "score": hit.score, **hit.payload}
            for hit in search_result
        ]
        ctx.info(f"Busca por '{query_text}' retornou {len(results)} resultados.")
        return results
    except Exception as e:
        ctx.error(f"Erro na busca semântica: {e}")
        return []

# Adicionar outras tools como check_indexed, index_uri (que chamaria o Filesystem Server)

# Lifespan para garantir conexão/desconexão Qdrant pode ser útil
````

#### Clientes (`/src/clients/*.py`)

- Criar classes que herdam de `BaseClient` (ou similar).
- Cada classe gerencia a conexão `stdio` com seu servidor MCP específico usando `mcp.client.stdio.stdio_client` e `mcp.ClientSession`.
- Expor métodos Python (ex: `async def read_file(self, path: str)`) que internamente fazem as chamadas `session.call_tool(...)` ou `session.read_resource(...)`.

**Exemplo: Esqueleto `src/clients/filesystem.py`**

```python
import asyncio
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic import AnyUrl
from typing import AsyncIterator, List, Dict, Any

class FilesystemClient:
    def __init__(self, command: List[str]):
        # Ex: command = ["uv", "run", "--package", "mcp-server-filesystem"]
        # Ou command = ["python", "path/to/server.py"]
        self.server_params = StdioServerParameters(command=command[0], args=command[1:])
        self._session: ClientSession | None = None
        self._connection_context = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator['FilesystemClient']:
        """Gerencia a conexão com o servidor."""
        async with stdio_client(self.server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                self._session = session
                try:
                    yield self
                finally:
                    self._session = None

    async def _ensure_connected(self) -> ClientSession:
        if not self._session:
            raise RuntimeError("Cliente não conectado. Use 'async with client.connect():'")
        return self._session

    async def parse_document(self, path: str) -> Dict[str, Any]:
        session = await self._ensure_connected()
        result = await session.call_tool("parse_document", {"path": path})
        # Supondo que parse_document retorne um dict no primeiro item do content
        if result.content and isinstance(result.content[0], types.TextContent):
             try:
                 return json.loads(result.content[0].text)
             except json.JSONDecodeError:
                 # Ou retorna o texto direto se não for JSON
                 return {"text": result.content[0].text}
        return {"error": "Falha ao parsear"}

    async def read_text_file(self, path: str) -> str:
        session = await self._ensure_connected()
        # Aqui usamos read_resource, não call_tool
        file_uri = AnyUrl(f"file://{path}") # Cuidado com paths absolutos/relativos
        result = await session.read_resource(file_uri)
        if result.contents and isinstance(result.contents[0], types.TextResourceContents):
            return result.contents[0].text
        return "" # Ou levantar erro

    # ... outros métodos para list_directory, write_file etc ...

# Exemplo de uso no ChatbotApp
# async with filesystem_client.connect():
#     content = await filesystem_client.parse_document("/path/doc.pdf")
```

### 3.4 Integração no Host (`core/app.py` - Refatorado)

- `ChatbotApp.__init__`: Instancia os clientes (`FilesystemClient`, `RAGClient`, etc.) com os comandos corretos para iniciar os servidores.
- `ChatbotApp.initialize` (Novo/Opcional): Poderia iniciar as conexões dos clientes em background se necessário, ou conectar/desconectar por chamada. Usar `async with client.connect():` dentro dos métodos que precisam do cliente é mais robusto.
- `ChatbotApp.process_input`: Orquestra as chamadas aos métodos dos _clientes_.

```python
# Exemplo de parte de core/app.py
from clients.filesystem import FilesystemClient
from clients.rag import RAGClient
# ... import outros clientes
from core.config import settings

class ChatbotApp:
    def __init__(self):
        self.filesystem_client = FilesystemClient(settings.FILESYSTEM_SERVER_CMD)
        self.rag_client = RAGClient(settings.RAG_SERVER_CMD)
        # ... inicializa outros clientes
        self.context_service = ContextService() # Mantido internamente por enquanto

    async def process_input(self, user_input: str) -> str:
        # ... (lógica para detectar intenção: indexar, perguntar, transcrever...)

        if user_input.startswith("/index "):
            file_path = user_input.split(" ", 1)[1]
            return await self.index_file(file_path)
        elif user_input.startswith("/ask "):
            query = user_input.split(" ", 1)[1]
            return await self.answer_query(query)
        # ... outros comandos
        else:
             # Conversa normal (pode envolver RAG ou só LLM)
             return await self.handle_conversation(user_input)


    async def index_file(self, file_path: str) -> str:
        try:
            async with self.filesystem_client.connect() as fs_client, \
                       self.rag_client.connect() as rag_client:
                # Idealmente, parse_document retornaria texto e metadados
                parsed_data = await fs_client.parse_document(file_path)
                text_content = parsed_data.get("text", "")
                metadata = parsed_data.get("metadata", {})
                metadata["source_uri"] = f"file://{file_path}" # Adiciona URI original

                if text_content:
                    success = await rag_client.index_text(text_content, metadata)
                    return "Indexado com sucesso." if success else "Falha ao indexar."
                else:
                    return "Não foi possível extrair texto do arquivo."
        except Exception as e:
            logger.error(f"Erro ao indexar {file_path}: {e}")
            return f"Erro durante indexação: {e}"

    async def answer_query(self, query: str) -> str:
        try:
            async with self.rag_client.connect() as rag_client:
                 # Cliente RAG lida com embedding + busca Qdrant
                search_results = await rag_client.semantic_search(query, k=3)
                if not search_results:
                    return "Não encontrei informações relevantes nos documentos."

                # Formatar contexto e chamar LLM (via api_service ou nlp_service)
                context = "\n\n".join([res.get("text", "") for res in search_results])
                prompt = f"Contexto:\n{context}\n\nPergunta: {query}\n\nResposta:"
                # ... (chamar LLM - ex: self.nlp_service.generate_response(prompt)) ...
                final_response = f"Com base nos documentos: [resposta do LLM aqui a partir de {context}]"
                return final_response
        except Exception as e:
            logger.error(f"Erro ao responder consulta RAG '{query}': {e}")
            return f"Erro durante a busca: {e}"

    # ... handle_conversation, process_audio, etc ...

```

### 3.5 Configurações de Ambiente (`.env`)

Adicionar caminhos/comandos para os servidores MCP.

```dotenv
# ... (Chaves de API mantidas) ...

# MCP Server Commands usando Poetry para isolar dependências
FILESYSTEM_SERVER_CMD='cd C:\AI\chatbot\mcp_servers\filesystem_server && poetry run python src\server.py --allowed-dir C:\AI\docs'
RAG_SERVER_CMD='cd C:\AI\chatbot\mcp_servers\rag_server && poetry run python src\server.py --qdrant-url http://localhost:6333'
MEDIA_SERVER_CMD='cd C:\AI\chatbot\mcp_servers\media_server && poetry run python src\server.py'
EMBEDDINGS_SERVER_CMD='cd C:\AI\chatbot\mcp_servers\embeddings_server && poetry run python src\server.py'

# Configurações específicas dos servers (se não passadas via args)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=chatbot_knowledge_fase2
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

### 3.6 Gerenciamento de Dependências com Poetry para Servidores MCP

Para gerenciar as dependências de cada servidor MCP de forma isolada e eficiente, serão utilizados arquivos `pyproject.toml` individuais em cada servidor, aproveitando o gerenciamento automático de ambientes virtuais do Poetry:

```bash
# Estrutura de diretórios para servidores MCP com Poetry
/mcp_servers/
  /filesystem_server/
    pyproject.toml  # Dependências específicas deste servidor
    /src/
      server.py
  /embeddings_server/
    pyproject.toml  # Dependências específicas deste servidor
    /src/
      server.py
  # ... outros servidores
```

**Exemplo: `pyproject.toml` para o servidor filesystem:**

```toml
[tool.poetry]
name = "mcp-server-filesystem"
version = "0.1.0"
description = "MCP Server for Filesystem Operations using Docling"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
mcp = { extras = ["server"], version = "^1.5.0" }
docling = "^0.1.0"
python-magic = "^0.4.27"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Vantagens desta abordagem:**

1. Cada servidor MCP tem seu ambiente virtual isolado gerenciado pelo Poetry
2. As dependências são declaradas e resolvidas localmente para cada servidor
3. Não há necessidade de criar manualmente múltiplos ambientes `.venv`
4. Evita conflitos de dependências entre servidores e com o host principal
5. Facilita a manutenção e atualização de dependências

**Para utilizar os servidores:**

```bash
# Instalar dependências para um servidor específico
cd mcp_servers/filesystem_server
poetry install

# Executar o servidor usando o ambiente Poetry
poetry run python src/server.py --allowed-dir C:\AI\docs
```

Os comandos nos arquivos `.env` devem ser ajustados para usar o Poetry para execução dos servidores:

### 3.7 Testando a Configuração MCP

Antes de desenvolver os servidores MCP reais, é recomendado criar um servidor MCP de teste para verificar que a configuração está funcionando corretamente:

1. Primeiro, crie a estrutura de diretórios e o arquivo `pyproject.toml` para o servidor de teste:

```bash
mkdir -p mcp_servers/test_server/src
cd mcp_servers/test_server
```

```toml
# mcp_servers/test_server/pyproject.toml
[tool.poetry]
name = "mcp-server-test"
version = "0.1.0"
description = "Servidor MCP de teste"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
mcp = { extras = ["server"], version = "^1.5.0" }

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

2. Crie um servidor MCP simples para teste:

```python
# mcp_servers/test_server/src/server.py
from mcp.server.fastmcp import FastMCP, Context

# Cria uma instância do servidor
mcp = FastMCP(name="Test Server")

@mcp.tool()
async def hello_world(name: str, ctx: Context) -> str:
    """Retorna uma mensagem de saudação."""
    ctx.info(f"Recebida chamada para hello_world com nome: {name}")
    return f"Olá, {name}! Seu primeiro servidor MCP está funcionando!"

if __name__ == "__main__":
    mcp.run()  # Inicia o servidor via stdio
```

3. Instale as dependências usando Poetry:

```bash
cd mcp_servers/test_server
poetry install
```

4. Crie um script para testar o servidor:

```python
# scripts/test_mcp.py
import asyncio
import sys
import subprocess
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    # Comando para iniciar o servidor
    cmd = ["poetry", "run", "python", "mcp_servers/test_server/src/server.py"]
    
    # Configurar parâmetros do servidor
    server_params = StdioServerParameters(command=cmd[0], args=cmd[1:])
    
    print("Iniciando servidor MCP...")
    
    # Conectar ao servidor
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                # Inicializar a sessão
                await session.initialize()
                
                print("Servidor MCP iniciado!")
                
                # Chamar o tool hello_world
                result = await session.call_tool("hello_world", {"name": "Desenvolvedor"})
                
                # Extrair e mostrar o resultado
                if result.content and isinstance(result.content[0], types.TextContent):
                    print(f"Resposta do servidor: {result.content[0].text}")
                else:
                    print("Formato de resposta inesperado.")
    except Exception as e:
        print(f"Erro ao conectar com o servidor MCP: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

5. Execute o teste a partir da raiz do projeto:

```bash
python scripts/test_mcp.py
```

Se tudo estiver funcionando corretamente, você verá a mensagem "Olá, Desenvolvedor! Seu primeiro servidor MCP está funcionando!".

Este teste simples confirma que a instalação do MCP está correta e que a comunicação entre cliente e servidor MCP via stdio está funcionando, antes de implementar os servidores complexos da aplicação.

## 4. Plano de Implementação (Revisado)

### 4.1 Etapas de Desenvolvimento

1.  **Refatoração da Estrutura:** (1-2 dias) Criar diretórios `/mcp_servers` e `/src/clients`. Mover lógicas relevantes.
2.  **Implementar `mcp-server-filesystem`:** (3-5 dias) Integrar DOCLING, criar tools `read`, `list`, `parse_document`. Testar isoladamente.
3.  **Implementar `mcp-server-embeddings`:** (2-3 dias) Integrar `langchain-huggingface`, criar tool `generate_embedding`. Testar.
4.  **Implementar `mcp-server-rag`:** (4-6 dias) Integrar Qdrant, criar tools `index_*`, `semantic_search` (que chama o embedding server). Testar.
5.  **Implementar `mcp-server-media`:** (3-4 dias) Integrar FFmpeg, API Whisper HF, criar tools `transcribe_audio`, `extract_audio_uri`. Testar.
6.  **Configurar `mcp-server-fetch`:** (1 dia) Adicionar ao config do Host para ser iniciado via `npx`.
7.  **Implementar Clientes MCP:** (2-3 dias) Criar classes em `/src/clients` para interagir com cada servidor via stdio.
8.  **Integrar Clientes no Host:** (3-4 dias) Refatorar `ChatbotApp` para usar os clientes MCP em vez de chamadas diretas a serviços. Implementar os fluxos RAG, Mídia, Web Search.
9.  **Testes de Integração Fim-a-Fim:** (2-3 dias) Testar fluxos completos (usuário -> host -> server(s) -> host -> usuário).

### 4.2 Timeline Revisado

- **Total**: ~21 - 31 dias de trabalho (pode ser um pouco mais longo que o original devido à sobrecarga inicial do MCP, mas resulta em arquitetura mais robusta).
- **Início**: Após conclusão da Fase 1.
- **Milestone**: Funcionalidades RAG, Mídia e Web Search operacionais através de servidores MCP dedicados.

## 5. Riscos e Mitigações (Atualizado)

| Risco                                       | Probabilidade | Impacto | Mitigação                                                                      |
| :------------------------------------------ | :------------ | :------ | :----------------------------------------------------------------------------- |
| Complexidade da Comunicação Inter-Processos | Média         | Médio   | Usar a biblioteca `mcp` para gerenciar stdio; Logging robusto em cada server.  |
| Gerenciamento de Múltiplos Servidores       | Média         | Médio   | Scripts para iniciar/parar todos os servers; Considerar Docker Compose futuro. |
| Dependência de DOCLING/FFmpeg               | Média         | Alto    | Isolar no servidor MCP; Testes de instalação robustos; Alternativas (Tika).    |
| Performance do Qdrant Local                 | Baixa/Média   | Médio   | Benchmarking inicial; Otimização de índices; Hardware adequado.                |
| Conflito de Dependências em Python        | Baixa         | Médio    | **Usar Poetry com `pyproject.toml` separados para cada servidor MCP;** Ver guia de uso. |

## 6. Conclusão Revisada

A Fase 2 transforma a arquitetura do chatbot, introduzindo servidores MCP dedicados para as funcionalidades essenciais de Filesystem (com Docling), RAG (com Qdrant e HF Embeddings), Mídia (com FFmpeg e Whisper) e Web Fetch (usando o servidor oficial). O Controlador Principal evolui para um Host MCP, orquestrando a comunicação via stdio. Embora represente um esforço inicial maior de refatoração, esta abordagem estabelece uma base modular, segura e escalável, alinhada com as melhores práticas e facilitando enormemente as fases futuras e a integração com o frontend.
