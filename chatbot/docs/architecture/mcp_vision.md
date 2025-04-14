# Visão de Arquitetura MCP (Model Context Protocol)

## Visão Geral

Este documento descreve a arquitetura atual do chatbot e como ela está preparada para evoluir para uma arquitetura baseada no **Model Context Protocol (MCP)** nas próximas fases.

## Arquitetura Atual (Fase 1)

A arquitetura atual é baseada em componentes modulares Python que se comunicam via chamadas de método assíncronas. Esta abordagem já estabelece separações claras que facilitarão a migração para MCP.

### Diagrama de Alto Nível (Fase 1)

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

## Mapeamento para MCP (Futuro)

A arquitetura atual foi desenhada pensando na futura migração para MCP. Abaixo está o mapeamento entre os componentes atuais e seus equivalentes futuros no MCP:

| Componente Atual | Futuro Componente MCP |
|------------------|------------------------|
| `ChatbotApp` (core/app.py) | **MCP Host** - Orquestrador central |
| `NLPService` (services/nlp_service.py) | **mcp-server-nlp** - Servidor MCP para processamento NLP |
| `ContextService` (services/context_service.py) | **mcp-server-memory** - Servidor MCP para gerenciamento de memória |
| `APIService` (services/api_service.py) | **mcp-server-api-gateway** - Servidor MCP para comunicação com APIs externas |
| `AudioService` (services/audio_service.py) | **mcp-server-media** - Servidor MCP para processamento de mídia |

## Plano de Transição para MCP

A migração para MCP será gradual, seguindo estas etapas:

1. **Fase 2:** Implementar `mcp-server-filesystem`, `mcp-server-rag`, `mcp-server-media` e integrar com `mcp-server-fetch` oficial.
2. **Fase 3:** Adicionar `mcp-server-ollama` para processamento local e `mcp-server-memory` para persistência.
3. **Fase 4:** Implementar framework de agentes e servidores para metacognição e personalidade.
4. **Fase 5:** Converter o Host para FastAPI, mantendo a arquitetura MCP como base.

## Interfaces MCP em Desenvolvimento

As interfaces dos componentes atuais foram projetadas para facilitar a futura conversão para MCP tools/resources:

### Exemplo de Interface Atual vs Futura (NLPService)

**Atual (Fase 1):**
```python
async def process_text(self, text: str, context: List[Dict]) -> str:
    # Lógica de processamento
    return response_text
```

**Futura (MCP Tool):**
```python
@mcp.tool()
async def process_text(text: str, context: List[Dict], ctx: Context) -> str:
    # Lógica de processamento
    return response_text
```

## Modelos e Serialização

Os modelos Pydantic (`Message`, `Conversation`) foram desenhados com compatibilidade MCP em mente, incluindo métodos `to_dict()` e `from_dict()` para facilitar a serialização/deserialização.

## Próximos Passos

1. Finalizar a implementação dos componentes da Fase 1
2. Começar a desenvolver os servidores MCP para a Fase 2
3. Migrar gradualmente as chamadas de método para chamadas MCP
4. Implementar os clientes MCP no Host para comunicação com os servidores
