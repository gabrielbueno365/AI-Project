# Servidores MCP

Este diretório contém os servidores MCP (Model Context Protocol) utilizados pelo chatbot. Cada servidor é um módulo independente que fornece funcionalidades específicas através do protocolo MCP.

## O que é MCP?

O Model Context Protocol (MCP) é um protocolo aberto que padroniza a comunicação entre aplicações de IA e ferramentas/fontes de dados. MCP permite:

1. Comunicação padronizada entre componentes
2. Modularidade e separação de responsabilidades
3. Segurança no acesso a recursos externos
4. Extensibilidade do sistema

## Estrutura de Diretórios

```
mcp_servers/
  ├── media_server/          # Processamento de áudio e mídia
  ├── test_server/           # Servidor de teste para diagnóstico
  └── README.md              # Esta documentação
```

## Servidores Disponíveis

### Media Server

Servidor MCP para processamento de áudio e mídia.

**Funcionalidades:**
- Transcrição de áudio usando Whisper via Groq ou HuggingFace
- Extração de áudio de arquivos de vídeo
- Conversão automática de formatos não suportados

**Instalação:**
```bash
cd media_server
poetry install
```

**Uso:**
```bash
poetry run python src/server.py --whisper-language pt-BR
```

## Gestão de Dependências

Cada servidor MCP tem suas próprias dependências gerenciadas via Poetry, o que permite:

1. Isolamento dos requisitos de cada servidor
2. Evitar conflitos de versões entre servidores
3. Simplificar a instalação e atualização

## Como Adicionar um Novo Servidor

1. Crie um novo diretório:
```bash
mkdir mcp_servers/nome_servidor
```

2. Inicialize a estrutura básica:
```
nome_servidor/
  ├── src/
  │   ├── __init__.py
  │   └── server.py
  ├── pyproject.toml
  └── README.md
```

3. Configure o `pyproject.toml`:
```toml
[tool.poetry]
name = "mcp-server-nome"
version = "0.1.0"
description = "Descrição do servidor"
authors = ["Sua Equipe <info@chatbot.com>"]

[tool.poetry.dependencies]
python = "^3.11"
mcp = { extras = ["server"], version = "^1.5.0" }
# Outras dependências específicas deste servidor

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

4. Implemente seu servidor usando o módulo FastMCP.

5. Adicione uma variável no arquivo `.env` para o comando de inicialização:
```
NOME_SERVER_CMD=poetry run python C:\AI\chatbot\mcp_servers\nome_servidor\src\server.py --opcoes
```

## Desenvolvimento e Testes

Para testar um servidor MCP:

1. Instale as dependências:
```bash
cd mcp_servers/nome_servidor
poetry install
```

2. Execute o servidor manualmente:
```bash
poetry run python src/server.py
```

3. Use a ferramenta de diagnóstico MCP para testar:
```bash
cd C:\AI\chatbot
poetry run python scripts/test_mcp_nome.py
```
