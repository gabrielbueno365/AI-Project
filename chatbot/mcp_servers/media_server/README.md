# MCP Server: Media

Este servidor MCP fornece funcionalidades para processamento de áudio e mídia. Implementa transcrição de áudio e extração de áudio de vídeos.

## Funcionalidades

- **Transcrição de áudio**: Converte áudio em texto usando APIs Whisper (Groq ou HuggingFace)
- **Extração de áudio**: Extrai a trilha de áudio de arquivos de vídeo
- **Suporte a múltiplos formatos**: Converte automaticamente formatos não suportados
- **Validação e sanitização**: Verifica segurança e validade dos arquivos

## Instalação

```bash
cd mcp_servers/media_server
poetry install
```

## Requisitos

- FFmpeg instalado no sistema e acessível via PATH
- Chaves de API para Groq e/ou HuggingFace (opcional, mas necessário para transcrição)

## Uso

Iniciar o servidor:

```bash
cd C:\AI\chatbot\mcp_servers\media_server
poetry run python src/server.py
```

### Opções de configuração:

```
--max-audio-size BYTES    Tamanho máximo de áudio (padrão: 50MB)
--max-audio-duration SEC  Duração máxima em segundos (padrão: 600)
--whisper-model MODEL     Modelo Whisper (padrão: whisper-large-v3)
--whisper-language LANG   Idioma para transcrição (padrão: pt)
--temp-dir DIR            Diretório temporário personalizado
```

### Variáveis de ambiente:

- `GROQ_API_KEY`: Chave de API para serviço Groq
- `HUGGING_FACE_API_KEY`: Chave de API para HuggingFace

## Integração com o Host MCP

Este servidor expõe as seguintes funções para o Host MCP:

### Tools:

- `transcribe_audio(file_uri: str) -> Dict[str, Any]`: Transcreve arquivo de áudio
- `extract_audio_uri(video_uri: str, output_format: str = "mp3") -> str`: Extrai e salva áudio de vídeo

## Formatos Suportados

Formatos de áudio suportados diretamente:
`.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.aac`, `.mp4`, `.mpeg`, `.mpga`, `.oga`, `.webm`

Formatos que serão automaticamente convertidos:
`.wma`, `.aiff`, `.aif`, `.3gp`, `.amr`, `.m4b`, `.ra`, `.rm`, `.vox`, `.raw`, `.au`, `.dct`, `.gsm`, `.vox`, `.m4p`, `.mid`, `.midi`, `.opus`
