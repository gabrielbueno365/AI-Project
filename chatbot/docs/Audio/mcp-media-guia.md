# Guia de Instalação e Uso do Servidor MCP de Mídia

Este guia fornece instruções passo a passo para configurar e utilizar o servidor MCP de mídia para processamento de áudio.

## Requisitos

Antes de começar, verifique se você tem os seguintes requisitos:

1. **FFmpeg**: Necessário para processamento de áudio/vídeo
   - Windows: Baixe do [site oficial](https://ffmpeg.org/download.html) e adicione ao PATH
   - Linux: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`

2. **Python 3.11+**: Verifique com `python --version`

3. **Poetry**: Para gerenciamento de dependências
   - Instale seguindo as instruções em [python-poetry.org](https://python-poetry.org/docs/#installation)

4. **Chaves de API** (para transcrição):
   - Groq: [Obtenha aqui](https://console.groq.com/)
   - HuggingFace: [Obtenha aqui](https://huggingface.co/settings/tokens)

## Instalação

Siga os passos abaixo para instalar o servidor MCP de mídia:

1. **Clone o repositório** (se ainda não o fez):
   ```bash
   git clone <url-do-repositorio>
   cd chatbot
   ```

2. **Instale as dependências do servidor MCP de mídia**:
   ```bash
   cd mcp_servers/media_server
   poetry install
   ```

3. **Configure as variáveis de ambiente**:
   Adicione as seguintes linhas ao arquivo `.env` na raiz do projeto:
   ```
   # API Keys para transcrição
   GROQ_API_KEY=sua_chave_groq_aqui
   HUGGING_FACE_API_KEY=sua_chave_huggingface_aqui
   
   # Configuração do servidor MCP de mídia
   MEDIA_SERVER_CMD=poetry run python C:\AI\chatbot\mcp_servers\media_server\src\server.py --whisper-language pt-BR
   ```

4. **Verifique a instalação do FFmpeg**:
   ```bash
   ffmpeg -version
   ```
   Se o comando não for reconhecido, verifique a instalação do FFmpeg.

## Execução

### Iniciar o Servidor MCP de Mídia Manualmente

Para iniciar o servidor manualmente (útil para testes):

```bash
cd mcp_servers/media_server
poetry run python src/server.py --whisper-language pt-BR
```

### Opções de Linha de Comando

O servidor suporta as seguintes opções:

```
--max-audio-size BYTES    Tamanho máximo de áudio (padrão: 50MB)
--max-audio-duration SEC  Duração máxima em segundos (padrão: 600)
--whisper-model MODEL     Modelo Whisper (padrão: whisper-large-v3)
--whisper-language LANG   Idioma para transcrição (padrão: pt)
--temp-dir DIR            Diretório temporário personalizado
```

### Testar o Servidor

Use o script de teste para verificar se o servidor está funcionando corretamente:

```bash
cd C:\AI\chatbot
poetry run python scripts/test_mcp_media.py --audio caminho/para/audio.mp3
```

Para testar a extração de áudio de um vídeo:

```bash
poetry run python scripts/test_mcp_media.py --video caminho/para/video.mp4
```

## Utilização no Código

Para utilizar o cliente MCP de mídia em seu código:

```python
from src.clients.media import MediaClient
from src.core.config import get_settings

settings = get_settings()
command = settings.media_server_cmd.split()
client = MediaClient(command)

async with client.connect():
    # Transcrever áudio
    result = await client.transcribe_audio("caminho/para/audio.mp3")
    print(f"Transcrição: {result['transcription']}")
    
    # Extrair áudio de vídeo
    audio_path = await client.extract_audio("caminho/para/video.mp4")
    print(f"Áudio extraído: {audio_path}")
```

## Arquivos e Formatos Suportados

### Formatos Suportados Diretamente

`.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.aac`, `.mp4`, `.mpeg`, `.mpga`, `.oga`, `.webm`

### Formatos com Conversão Automática

`.wma`, `.aiff`, `.aif`, `.3gp`, `.amr`, `.m4b`, `.ra`, `.rm`, `.vox`, `.raw`, `.au`, `.dct`, `.gsm`, `.vox`, `.m4p`, `.mid`, `.midi`, `.opus`

## Solução de Problemas

### Erros Comuns

1. **FFmpeg não encontrado**
   - Certifique-se de que o FFmpeg está instalado e no PATH
   - Erro: `FFmpeg não encontrado no sistema. Necessário para conversão de áudio.`

2. **Falha na API de transcrição**
   - Verifique se as chaves de API estão configuradas corretamente
   - Verifique a validade das chaves
   - Erro: `Falha na transcrição: código 401`

3. **Arquivo muito grande**
   - Reduza o tamanho do arquivo ou aumente o limite com `--max-audio-size`
   - Erro: `Arquivo muito grande: X bytes (máximo: Y bytes)`

4. **Áudio muito longo**
   - Reduza a duração do áudio ou aumente o limite com `--max-audio-duration`
   - Erro: `Áudio muito longo: X segundos (máximo: Y segundos)`

### Logs

Para verificar os logs do servidor, execute-o com o nível de log desejado:

```bash
poetry run python src/server.py --whisper-language pt-BR --log-level DEBUG
```

## Considerações sobre Performance

Para melhor desempenho:

1. **Hardware**: O processamento de áudio/vídeo é intensivo em CPU. Um processador multi-core é recomendado.
2. **Memória**: Pelo menos 4GB de RAM disponível.
3. **Armazenamento**: Espaço suficiente para arquivos temporários (pelo menos 1GB livre).
4. **Rede**: Conexão estável com a internet para APIs de transcrição.

## Próximos Passos

- Adicione suporte para processamento de imagens
- Implemente análise de sentimento em áudio
- Adicione suporte para reconhecimento de locutor
