# Migração do Processamento de Áudio para Arquitetura MCP

## Visão Geral

Este documento descreve o processo de migração do serviço de processamento de áudio existente para a arquitetura MCP (Model Context Protocol).

## Motivação

A migração para a arquitetura MCP oferece as seguintes vantagens:

1. **Modularidade**: Separação clara de responsabilidades
2. **Escalabilidade**: Servidores podem ser executados em processos/máquinas separados
3. **Reusabilidade**: Funcionalidades podem ser acessadas por outros componentes
4. **Segurança**: Isolamento do acesso a recursos do sistema
5. **Padronização**: Interface consistente com outros serviços

## Comparação: Antes e Depois

### Antes: Abordagem Monolítica

- Implementação em `src/services/audio_service.py`
- Acoplamento direto com outros serviços
- Transcrição implementada diretamente usando `api_service.py`
- Gerenciamento de arquivos temporários específico para cada função
- Dependências diretamente no projeto principal

### Depois: Arquitetura MCP

- Servidor MCP dedicado em `mcp_servers/media_server/`
- Cliente MCP em `src/clients/media.py`
- Comunicação baseada em protocolo padronizado
- Gerenciamento centralizado de arquivos temporários
- Dependências isoladas com Poetry próprio
- Interface clara através de "tools" MCP

## Implementação

### 1. Estrutura

```
mcp_servers/
  media_server/
    pyproject.toml     # Dependências isoladas
    src/
      __init__.py
      server.py         # Servidor MCP
      helpers.py        # Funções auxiliares
src/
  clients/
    __init__.py
    media.py           # Cliente MCP
```

### 2. Interface MCP

O servidor expõe duas tools principais:

- `transcribe_audio(file_uri: str) -> Dict[str, Any]`: Transcreve áudio
- `extract_audio_uri(video_uri: str, output_format: str = "mp3") -> str`: Extrai áudio de vídeo

### 3. Como Usar

#### Iniciar o Servidor

```bash
cd C:\AI\chatbot\mcp_servers\media_server
poetry install
poetry run python src/server.py --whisper-language pt-BR
```

#### Usar o Cliente

```python
from src.clients.media import MediaClient
from src.core.config import get_settings

settings = get_settings()
command = settings.media_server_cmd.split()
client = MediaClient(command)

async with client.connect():
    # Transcrever áudio
    result = await client.transcribe_audio("path/to/audio.mp3")
    print(f"Transcrição: {result['transcription']}")
    
    # Extrair áudio de vídeo
    audio_path = await client.extract_audio("path/to/video.mp4")
    print(f"Áudio extraído: {audio_path}")
```

## Plano de Transição

### Fase 1: Coexistência (Atual)

- Manter o serviço `audio_service.py` existente
- Implementar servidor e cliente MCP
- Validar funcionalidade com testes isolados
- Documentar nova abordagem

### Fase 2: Refatoração Gradual

- Atualizar o controlador principal (ChatbotApp) para usar o cliente MCP
- Redirecionar chamadas para o novo cliente quando disponível
- Usar o serviço antigo como fallback

### Fase 3: Migração Completa

- Remover código antigo quando todas as funcionalidades estiverem migradas
- Atualizar testes para usar apenas a nova implementação
- Transferir configurações para arquivo .env

## Conclusão

A migração para a arquitetura MCP representa um avanço significativo no design do sistema, alinhando-se com a visão de longo prazo do projeto e permitindo uma maior flexibilidade e escalabilidade no processamento de mídia.
