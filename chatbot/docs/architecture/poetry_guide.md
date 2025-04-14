# Guia de Uso do Poetry no Projeto Chatbot

Este guia explica como usar o Poetry para gerenciar dependências no projeto do Chatbot, especialmente para os servidores MCP.

## O que é Poetry?

Poetry é uma ferramenta de gerenciamento de dependências e empacotamento para Python que simplifica a gestão de pacotes, ambientes virtuais e dependências de projetos Python.

## Instalação do Poetry

Se você ainda não tem o Poetry instalado, siga estas instruções:

### Windows
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Linux/macOS
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Após a instalação, reinicie o terminal e verifique se o Poetry foi instalado corretamente:
```bash
poetry --version
```

## Estrutura do Projeto com Poetry

Nosso projeto usa dois níveis de gerenciamento com Poetry:

1. **Host Principal** (diretório raiz do chatbot)
   - Contém o arquivo `pyproject.toml` principal para o código base/host
   
2. **Servidores MCP** (diretórios individuais em `mcp_servers/`)
   - Cada servidor tem seu próprio `pyproject.toml` com suas dependências específicas

```
/chatbot/
  pyproject.toml        # Dependências do host
  /src                  # Código fonte principal
  /mcp_servers/
    /filesystem_server/
      pyproject.toml    # Dependências específicas deste servidor
      /src/
    /embeddings_server/
      pyproject.toml    # Dependências específicas deste servidor
      /src/
    # ... outros servidores
```

## Operações Básicas do Poetry

### 1. Instalação de Dependências

Instalar dependências a partir do `pyproject.toml`:
```bash
cd caminho/para/o/projeto  # diretório contendo pyproject.toml
poetry install
```

### 2. Adicionando Novas Dependências

```bash
poetry add nome-do-pacote      # Adiciona uma dependência normal
poetry add nome-do-pacote -D   # Adiciona uma dependência de desenvolvimento
```

Exemplo:
```bash
# Adicionar Flask com versão específica
poetry add flask@^2.0.0

# Adicionar dependência com extras
poetry add "mcp[server]@^1.5.0"
```

### 3. Executando Comandos no Ambiente Virtual

```bash
poetry run python script.py   # Executa um script no ambiente virtual
poetry shell                  # Ativa o ambiente virtual para uso interativo
```

## Guia de Uso para o Projeto Chatbot

### Configurando um Servidor MCP

1. **Criar a estrutura do servidor**:
   ```bash
   mkdir -p mcp_servers/novo_servidor/src
   ```

2. **Criar o `pyproject.toml`**:
   ```bash
   cd mcp_servers/novo_servidor
   poetry init   # Guia interativo para criar o pyproject.toml
   # Ou criar o arquivo manualmente
   ```

3. **Instalar dependências**:
   ```bash
   cd mcp_servers/novo_servidor
   poetry install
   ```

### Exemplos de `pyproject.toml` para Servidores

**Servidor Filesystem**:
```toml
[tool.poetry]
name = "mcp-server-filesystem"
version = "0.1.0"
description = "MCP Server for Filesystem Operations"
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

**Servidor Embeddings**:
```toml
[tool.poetry]
name = "mcp-server-embeddings"
version = "0.1.0"
description = "MCP Server for Text Embeddings"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
mcp = { extras = ["server"], version = "^1.5.0" }
langchain-huggingface = "^0.0.3"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Executando Servidores MCP

Para iniciar um servidor MCP:
```bash
cd mcp_servers/servidor_x
poetry run python src/server.py [argumentos]
```

### Configuração no arquivo `.env`

Configurar os comandos no `.env` para usar Poetry:
```
FILESYSTEM_SERVER_CMD='cd C:\AI\chatbot\mcp_servers\filesystem_server && poetry run python src\server.py --allowed-dir C:\AI\docs'
```

## Gerenciamento de Ambientes

O Poetry gerencia os ambientes virtuais automaticamente. Não é necessário criar ou ativar manualmente ambientes `.venv` separados.

Para ver onde estão os ambientes virtuais:
```bash
poetry config --list
```

Para configurar a criação de ambientes virtuais no diretório do projeto (opcional):
```bash
poetry config virtualenvs.in-project true
```

## Dicas Extras

1. **Atualização de Dependências**:
   ```bash
   poetry update
   ```

2. **Exibir a árvore de dependências**:
   ```bash
   poetry show --tree
   ```

3. **Exportar requirements.txt**:
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```

4. **Verificar ambiente ativo**:
   ```bash
   poetry env info
   ```

## Solução de Problemas

Se encontrar erros como "Não foi possível encontrar uma versão compatível", pode tentar:

1. Atualizar o Poetry: `poetry self update`
2. Limpar o cache: `poetry cache clear PyPI --all`
3. Ajustar as restrições de versão no `pyproject.toml`

## Referências

- [Documentação oficial do Poetry](https://python-poetry.org/docs/)
- [Tutorial de início rápido do Poetry](https://python-poetry.org/docs/basic-usage/)
