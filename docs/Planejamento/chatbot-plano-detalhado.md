---
---

# Plano Estratégico para Desenvolvimento de Chatbot Inteligente (v.MCP)

## Sumário Executivo

Este documento apresenta um plano de desenvolvimento estruturado e otimizado para a criação de um chatbot inteligente, evoluindo de uma interface de terminal básica para um serviço de backend robusto via API, pronto para integração com frontend. O plano adota uma **arquitetura modular baseada no Model Context Protocol (MCP)**, onde funcionalidades distintas (acesso a arquivos, RAG, processamento NLP local, memória, etc.) são encapsuladas em **Servidores MCP dedicados**. O sistema central (inicialmente terminal, depois API FastAPI) atua como um **Host MCP**, orquestrando a comunicação com esses servidores. Esta abordagem maximiza a reusabilidade, manutenibilidade, segurança e flexibilidade, priorizando o uso eficiente de recursos (APIs pagas vs. processamento local via Ollama) e garantindo interoperabilidade futura.

## Princípios Norteadores

1.  **Arquitetura MCP-First**: Utilizar MCP como a espinha dorsal para comunicação entre componentes, garantindo modularidade e desacoplamento.
2.  **Otimização Híbrida (Local/API)**: Priorizar processamento local via Ollama (NLP, Embeddings) para eficiência e custo, recorrendo a APIs (Groq, HF) para tarefas complexas, gerenciado por um roteador inteligente no Host.
3.  **Componentização Extrema**: Cada funcionalidade chave (filesystem, RAG, memória, NLP local, etc.) reside em seu próprio Servidor MCP.
4.  **Desenvolvimento Iterativo e Validado**: Construir e testar cada Servidor MCP e a integração com o Host em fases bem definidas.
5.  **Controle de Versão e Qualidade**: Git/GitHub com branches por feature/server, testes unitários/integração para Host e Servidores, linting/formatação.
6.  **Preparação para Frontend**: A API final (FastAPI como Host MCP) abstrairá a complexidade da rede de servidores MCP, oferecendo endpoints claros para integração web.

## Visão Geral das Fases (com Foco MCP)

| Fase | Descrição                                   | Foco Principal (MCP)                                                                     | Duração Estimada |
| :--- | :------------------------------------------ | :--------------------------------------------------------------------------------------- | :--------------- |
| 1    | Base Estrutural e Conversacional (Terminal) | Arquitetura modular _preparada_ para MCP, interfaces internas bem definidas.             | 2-3 semanas      |
| 2    | Servidores MCP Essenciais (RAG, Mídia, Web) | Implementação dos primeiros Servidores MCP (`filesystem`, `rag`, `media`, `fetch`).      | 4-6 semanas      |
| 3    | Inteligência Híbrida e Memória MCP          | Servidores MCP para `ollama` (NLP local) e `memory` (persistente). Router no Host.       | 5-7 semanas      |
| 4    | Agentes MCP e Inteligência Avançada         | Framework de Agentes (Host) usando Tools MCP. Servidores `metacognition`, `personality`. | 6-8 semanas      |
| 5    | API Host MCP (FastAPI) e Otimização         | FastAPI como Host MCP orquestrando Servidores. Otimizações (cache, compressão).          | 4-6 semanas      |

## Fase 1: Chatbot Básico (Terminal - Preparação MCP)

### Objetivo

Desenvolver a versão inicial via terminal com arquitetura assíncrona e **interfaces internas modulares** que espelhem futuras interações MCP.

### Arquitetura e Tecnologias

- **Linguagem/Core**: Python 3.11+, Asyncio, Poetry.
- **Interface**: Rich, Prompt_toolkit.
- **APIs Iniciais**: Groq SDK, `httpx` (para HF Whisper/CLIP se necessário), `python-dotenv`.
- **Estrutura**: Conforme definido, com `core/app.py` (Futuro Host) e `services/*.py` (Futuros Servers). As chamadas entre `app.py` e `services` são métodos Python, mas com assinaturas pensadas como futuras `tools` MCP.
- **MCP**: Biblioteca `mcp[cli]` instalada via Poetry para preparar o ambiente.

### Componentes Principais

1.  **Interface Terminal**: `main.py`.
2.  **Controlador (`core/app.py`)**: Gerencia o fluxo, chama os _services_.
3.  **Serviços (`services/*.py`)**:
    - `nlp_service.py`: Lógica inicial de interação com LLM (via `api_service`).
    - `context_service.py`: Gerenciamento de contexto _em memória_ para a sessão atual.
    - `api_service.py`: Cliente `httpx` robusto (retry, circuit breaker) para Groq/HF.
4.  **Modelos (`models/*.py`)**: Pydantic para mensagens/conversa.

### Entregáveis

- Chatbot terminal funcional para conversas simples.
- Estrutura de projeto modular com interfaces bem definidas entre `core` e `services`.
- Testes unitários para os serviços.
- Ambiente configurado com `mcp` instalado.

## Fase 2: Expansão com Servidores MCP Essenciais

### Objetivo

Implementar funcionalidades de RAG, acesso a arquivos/web e processamento de mídia como **Servidores MCP dedicados**, refatorando o Host para usar **Clientes MCP**.

### Tecnologias Principais

- **MCP**: `mcp` SDK Python (para Clientes no Host e `FastMCP` nos Servers).
- **Filesystem/Docs**: `mcp-server-filesystem` (usando `docling`, `python-magic`).
- **RAG**: `mcp-server-rag` (usando `qdrant-client`) + `mcp-server-embeddings` (usando `langchain-huggingface` localmente).
- **Mídia**: `mcp-server-media` (usando `ffmpeg-python`, `httpx` para Whisper HF).
- **Web**: Utilizar o servidor oficial `@modelcontextprotocol/server-fetch` via `npx` (configurado no Host).
- **Banco Vetorial**: Qdrant (instância local).

### Componentes a Desenvolver

1.  **Servidores MCP**: Implementar `filesystem_server`, `rag_server`, `embeddings_server`, `media_server` usando `FastMCP`, cada um em seu próprio diretório/projeto Poetry (ou subdiretório gerenciado).
2.  **Clientes MCP (`src/clients/*.py`)**: Implementar classes cliente no Host para comunicar via `stdio` com cada servidor MCP local.
3.  **Host (`core/app.py`)**: Refatorar para remover lógica movida para os servidores e usar os Clientes MCP para chamar as `tools`/`resources` dos servidores.

### Segurança e Validação

- Validação de paths e tipos de arquivo **dentro** do `mcp-server-filesystem`.
- Qdrant e outros servidores locais rodam com permissões mínimas necessárias.

### Entregáveis

- Host interagindo com Servidores MCP via stdio para:
  - Ler/parsear documentos (DOCLING via `filesystem_server`).
  - Indexar e buscar em RAG (Qdrant/HF via `rag_server` e `embeddings_server`).
  - Transcrever áudio (Whisper via `media_server`).
  - Buscar na web (via `fetch_server`).
- Testes de integração Host <-> Servidor MCP.

## Fase 3: Inteligência Híbrida e Memória MCP

### Objetivo

Implementar processamento NLP local (Ollama) e memória persistente (SQLite/Qdrant) como **Servidores MCP**, e adicionar um **Router Inteligente** no Host MCP.

### Tecnologias Principais

- **NLP Local**: `mcp-server-ollama` (usando cliente `ollama` para modelos BERT/RoBERTa).
- **Embeddings Locais**: `mcp-server-embeddings` refatorado para usar `nomic-embed-text` via Ollama.
- **Memória**: `mcp-server-memory` (usando `aiosqlite` e `qdrant-client`).
- **Roteamento**: Lógica Python no Host (`core/router.py`).

### Componentes a Desenvolver

1.  **Servidor MCP: `mcp-server-ollama`**: Expõe `tools` para `classify_intent`, `analyze_sentiment`, `extract_entities` usando modelos Ollama locais.
2.  **Servidor MCP: `mcp-server-memory`**: Expõe `tools` para `add_interaction`, `get_recent_context`, `search_memory` (longo prazo Qdrant), `summarize_context` (pode chamar outro LLM via MCP). Implementa lógica de 3 níveis (working/short/long).
3.  **Refatoração `mcp-server-embeddings`**: Mudar backend para `ollama.embeddings(model='nomic-embed-text', ...)`.
4.  **Router Inteligente (no Host)**: Analisa input (via `mcp-server-ollama` para intenção) e decide qual MCP Client/Tool chamar (local vs. API externa).

### Entregáveis

- Chatbot utilizando processamento local para tarefas NLP específicas.
- Sistema de memória persistente acessível via MCP.
- Router inteligente funcional no Host MCP.

## Fase 4: Inteligência Avançada via Framework de Agentes MCP

### Objetivo

Implementar um **Framework de Agentes LangChain dentro do Host MCP** que utilize as funcionalidades dos Servidores MCP como **Tools**, e adicionar servidores para **Metacognição** e **Personalidade**.

### Tecnologias e Abordagens

- **Agentes**: `langchain` (no Host).
- **Tools para Agentes**: Wrappers em `src/agents/tools.py` que usam os MCP Clients para chamar as tools dos servidores MCP (`filesystem`, `rag`, `ollama`, `memory`, `fetch`, `media`, etc.).
- **Metacognição**: `mcp-server-metacognition` usando LLM (via outro MCP Server) para análise.
- **Personalidade**: `mcp-server-personality` usando LLM (via outro MCP Server) para ajuste de tom/estilo.
- **Orquestração (Host)**: `core/orchestrator.py` decide entre chamada direta (via Router) ou delegação para um Agente.

### Componentes a Desenvolver

1.  **Wrappers LangChain Tool (`agents/tools.py`)**: Classes que implementam `BaseTool` e internamente usam os MCP Clients.
2.  **Agent Factory/Executor (`agents/*.py`)**: Configuração de agentes LangChain (ex: `create_tool_calling_agent`) usando os wrappers acima e um LLM acessado via MCP Client.
3.  **Servidor MCP: `mcp-server-metacognition`**: Implementa tools `reflect_on_reasoning`, `verify_solution`, etc.
4.  **Servidor MCP: `mcp-server-personality`**: Implementa tool `apply_personality`.
5.  **Orquestrador (`core/orchestrator.py`)**: Lógica de alto nível para escolher entre o Router simples (Fase 3) e o Framework de Agentes.

### Entregáveis

- Capacidade de executar tarefas complexas multi-etapas via agentes LangChain que usam Tools MCP.
- Servidores MCP funcionais para metacognição e personalidade.
- Orquestrador no Host capaz de delegar tarefas para agentes.

## Fase 5: Otimização e API Host MCP (FastAPI)

### Objetivo

Transformar o **Host MCP (Controlador Principal)** em uma **API FastAPI**, otimizar o sistema e prepará-lo para servir um frontend. Os Servidores MCP rodam como processos/serviços separados.

### Tecnologias Principais

- **API**: **FastAPI**, Uvicorn.
- **Autenticação**: JWT (`python-jose[cryptography]`, `passlib[bcrypt]`).
- **Otimização**: Cache (`redis` ou `cachetools`), Compressão de Embeddings (`scikit-learn`), Rate Limiting (`slowapi`).
- **Monitoramento**: `prometheus-fastapi-instrumentator`.
- **Containerização (Opcional)**: Docker, Docker Compose.

### Componentes a Desenvolver

1.  **API FastAPI (`src/api/`)**:
    - `main.py`: Aplicação principal, gerenciamento do _lifespan_ para iniciar/parar MCP Clients.
    - `routers/*.py`: Endpoints RESTful (ex: `/chat/message`, `/documents/index`, `/memory/search`).
    - `dependencies.py`: Injeção do Orchestrator e MCP Clients nos endpoints.
    - `middleware.py`: Logging de requisições, métricas Prometheus, CORS.
2.  **Autenticação (`src/auth/`)**: Endpoints `/token`, dependência `get_current_user`.
3.  **Otimizações (`src/optimization/`)**:
    - `caching.py`: Integração de Redis/cachetools nos pontos apropriados (respostas LLM, resultados de tools custosas).
    - `compression.py`: Implementar classe `EmbeddingCompressor` com PCA; integrá-la ao fluxo de RAG/Memória nos servidores MCP relevantes (via configuração ou chamada de tool específica).
4.  **Deployment (`/deployment/`)**: Dockerfiles para API e servidores MCP, `docker-compose.yml` para orquestração local/staging.

### Entregáveis

- API FastAPI funcional e documentada (Swagger UI) atuando como Host MCP.
- Sistema com otimizações de cache e compressão implementadas.
- Configuração para deployment via Docker Compose (opcional).
- Testes de API e integração atualizados.

## Estratégia de Implementação Técnica (Mantida da Revisão Anterior)

- Fluxo Git (`main`, `develop`, `feature/*`, etc.).
- Ciclo de desenvolvimento incremental com testes e code review.
- Documentação contínua (docstrings, READMEs, diagrama de arquitetura).

## Estratégia de Economia de API (Reforçada pelo MCP)

A arquitetura MCP torna essa estratégia explícita:

1.  **Roteamento no Host**: O Router Inteligente (Fase 3) é chave. Ele direciona chamadas:
    - Para `mcp-server-ollama` (local) para tarefas como intenção, sentimento, NER, QA simples.
    - Para `mcp-server-embeddings` (local/Ollama) para RAG/busca de memória.
    - Para `mcp-server-llm-api` (remoto - Groq/HF) **apenas** para geração complexa, raciocínio, ou quando as capacidades locais são insuficientes.
2.  **Cache**: Implementado no Host FastAPI (para respostas de API) e potencialmente dentro de servidores MCP específicos (ex: `mcp-server-fetch`).
3.  **Otimização de Tokens**: Prompts otimizados; sumarização de contexto (via `mcp-server-memory` que pode usar um LLM local se possível).
4.  **Hardware Adequado**: O Ryzen 7 5800H com 16GB RAM é confirmado como adequado para rodar os servidores Ollama (NLP e Embeddings) e Qdrant localmente.

## Otimizações Técnicas Avançadas (Contexto MCP)

1.  **Compressão de Embeddings**: Implementada no `mcp-server-rag` e `mcp-server-memory` antes de enviar/armazenar vetores no Qdrant.
2.  **Otimização de Recursos**: Cache hierárquico (Host + Servers); economia de tokens gerenciada pelo Host/Orchestrator; batching pode ser implementado em _tools_ MCP que processam listas.
3.  **Segurança Robusta**: Validação no Host (API Auth) e em cada Servidor MCP (validação de inputs das tools, controle de acesso a recursos como no `filesystem_server`). Detecção de prompt injection pode ser uma _tool_ no `mcp-server-ollama` ou `llm-api`.
4.  **Arquitetura Async**: Mantida no Host (FastAPI) e nos Servidores (`FastMCP` é async).
5.  **Gerenciamento de Erros**: Circuit breakers no Host (`APIClient` interno ou nos MCP Clients); Retries implementados nos MCP Clients; Modo degradado gerenciado pelo Host/Orchestrator (ex: desabilitar chamada a um servidor MCP offline).
6.  **Feedback Loop**: Comando (`/feedback ...`) enviado ao Host, que chama uma _tool_ `add_feedback` no `mcp-server-memory` ou um serviço externo.

## Preparação para Frontend Futuro (Simplificada pelo MCP)

- A **API FastAPI (Host MCP)** é a única interface com a qual o frontend precisa interagir. Ela abstrai toda a rede de servidores MCP.
- Endpoints RESTful bem definidos para todas as ações do usuário.
- WebSockets (se implementados no FastAPI) podem fornecer atualizações em tempo real (ex: status de indexação, novas mensagens de chat) sem expor a complexidade do MCP.

## Cronograma e Marcos (Mantido)

| Marco | Descrição (com Foco MCP)                          | Timeline Estimado |
| :---- | :------------------------------------------------ | :---------------- |
| M1    | Chatbot Terminal Funcional (Estrutura Pré-MCP)    | Final da Fase 1   |
| M2    | RAG, Mídia, Web via **Servidores MCP**            | Final da Fase 2   |
| M3    | Memória MCP, NLP Local (Ollama) & Router no Host  | Final da Fase 3   |
| M4    | Agentes no Host usando Tools MCP, Meta/Pers Servs | Final da Fase 4   |
| M5    | API Host FastAPI Completa e Otimizada             | Final da Fase 5   |

## Próximos Passos Imediatos (Mantido da Revisão Anterior)

1.  Setup Inicial (Poetry, Git, `mcp` lib).
2.  Implementar Fase 1 com interfaces internas modulares.
3.  Planejamento detalhado das interfaces (`tools`/`resources`) dos Servidores MCP da Fase 2.

## Conclusão (Atualizada com MCP)

Este plano detalhado e atualizado define um caminho robusto para construir um chatbot avançado, utilizando a **arquitetura modular e padronizada do MCP** como pilar central. Ao encapsular funcionalidades em servidores MCP dedicados (Filesystem/Docling, RAG/Qdrant, Ollama NLP, Memória, etc.) e usar um Host central (Terminal, depois FastAPI) para orquestrar a comunicação via Clientes MCP, garantimos flexibilidade, segurança e manutenibilidade. A estratégia híbrida, alavancando **Ollama local para eficiência** e APIs externas (Groq/HF) para capacidade, gerenciada pelo Router Inteligente no Host, otimiza custos e performance. A arquitetura resultante não só atende aos requisitos funcionais de cada fase, mas também estabelece uma base sólida e escalável para a integração futura com interfaces web complexas através da API FastAPI final.

---

## Apêndice A: Bibliotecas Recomendadas por Componente MCP

- **Host (FastAPI - Fase 5)**: `fastapi`, `uvicorn`, `python-jose[cryptography]`, `passlib[bcrypt]`, `prometheus-fastapi-instrumentator`, `mcp[cli]`, `redis`/`cachetools`, `slowapi`, `langchain` (para agentes).
- **`mcp-server-filesystem`**: `mcp`, `FastMCP`, `docling`, `python-magic`, `pathlib`.
- **`mcp-server-rag`**: `mcp`, `FastMCP`, `qdrant-client`. (Depende do `mcp-server-embeddings` via client).
- **`mcp-server-embeddings`**: `mcp`, `FastMCP`, `ollama` (para `nomic-embed-text`).
- **`mcp-server-media`**: `mcp`, `FastMCP`, `ffmpeg-python`, `httpx`.
- **`mcp-server-ollama`**: `mcp`, `FastMCP`, `ollama`.
- **`mcp-server-memory`**: `mcp`, `FastMCP`, `aiosqlite`, `qdrant-client`. (Depende do `mcp-server-embeddings`).
- **`mcp-server-metacognition`**: `mcp`, `FastMCP`. (Depende do `mcp-server-llm-api`/`ollama` e `mcp-server-memory`).
- **`mcp-server-personality`**: `mcp`, `FastMCP`. (Depende do `mcp-server-llm-api`/`ollama`).
- **`mcp-server-fetch`**: `@modelcontextprotocol/server-fetch` (Node.js - usar `npx`).

## Apêndice B: Racional da Escolha Qdrant (Mantido)

Qdrant permanece como a escolha ideal para banco vetorial (RAG e memória de longo prazo) devido à sua escalabilidade local-para-cloud, filtros avançados, natureza open-source, API RESTful e boa integração com LangChain, encaixando-se bem na arquitetura MCP distribuída.

## Apêndice C: Modelos Ollama Recomendados (Mantido)

- **Embeddings**: `nomic-embed-text` (via `mcp-server-embeddings`).
- **NLP Tasks (no `mcp-server-ollama`)**:
  - Classificação: `bert-base` / `roberta-base`.
  - Sentimento: `distilbert-base-uncased-finetuned-sst-2-english`.
  - NER: `bert-base-ner`.
  - Sumarização/QA Simples (Opcional): Modelos menores como `llama3:8b` (se hardware permitir) ou fallback para API remota.
