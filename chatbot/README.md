# Chatbot Inteligente (Fase 1)

Este é um projeto de chatbot inteligente desenvolvido em Python, seguindo uma arquitetura modular que está preparada para evoluir para o Model Context Protocol (MCP).

## Estado Atual

O projeto está na **Fase 1 - Chatbot Básico (Terminal)**, que implementa:

- Interface via terminal usando Rich e prompt_toolkit
- Arquitetura modular com serviços independentes
- Integração com APIs Groq e Hugging Face para geração de texto
- Processamento básico de arquivos de áudio para transcrição
- Gestão de contexto em memória para conversa contextual
- Inclusão da biblioteca MCP para futura migração

## Arquitetura

A arquitetura atual é baseada em componentes modulares Python que se comunicam via chamadas de método assíncronas. Esta abordagem já estabelece separações claras que facilitarão a migração para MCP nas próximas fases.

Principais componentes:

- **ChatbotApp**: Controlador principal (futuro MCP Host)
- **NLPService**: Processamento de linguagem natural
- **APIService**: Comunicação com APIs externas
- **ContextService**: Gestão do contexto da conversa
- **AudioService**: Processamento de arquivos de áudio

A documentação completa da arquitetura está disponível em `docs/architecture/mcp_vision.md`.

## Próximas Fases

1. **Fase 2**: Implementação dos servidores MCP essenciais (RAG, Filesystem, Mídia, Web)
2. **Fase 3**: Inteligência híbrida e memória MCP (Ollama local + Memória persistente)
3. **Fase 4**: Agentes MCP e inteligência avançada (Framework de Agentes, Metacognição)
4. **Fase 5**: API Host MCP (FastAPI) e otimização

## Instalação

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente (Windows)
.venv\Scripts\activate
# OU (Linux/Mac)
source .venv/bin/activate

# Instalar dependências via Poetry
pip install poetry
poetry install
```

## Uso

```bash
python -m src.main
```

## Testes

```bash
pytest tests/
```

## Licença

Todos os direitos reservados.
