# Guia de Configuração e Troubleshooting das APIs de Transcrição

Este documento fornece informações sobre como configurar e solucionar problemas com as APIs de transcrição de áudio utilizadas no chatbot.

## APIs Suportadas

O sistema utiliza duas APIs de transcrição de áudio, com um sistema de fallback:

1. **Groq API** (primária): Utiliza o modelo Whisper para transcrição
2. **Hugging Face API** (fallback): Também utiliza modelos Whisper

## Configuração de Chaves de API

As chaves de API são configuradas no arquivo `.env` na raiz do projeto:

```
GROQ_API_KEY=sua_chave_groq_aqui
HUGGINGFACE_TOKEN=sua_chave_huggingface_aqui
```

## Formato de Áudio

Para melhor compatibilidade, o sistema:

- Aceita formatos: MP3, WAV, OGG, FLAC, M4A e outros
- Converte automaticamente para MP3 os formatos que podem causar problemas com as APIs (especialmente M4A, AAC, WMA, AIFF e OGG)

## Solução de Problemas Comuns

### Erro "unsupported language: pt-BR"

**Problema**: A API da Groq não aceita códigos de idioma com região (como pt-BR).

**Solução**: O sistema agora extrai automaticamente o código de idioma principal (pt de pt-BR).

Se precisar modificar manualmente, altere a configuração `whisper_language` em `src/core/config.py` para usar apenas "pt" em vez de "pt-BR".

### Erro "Malformed soundfile"

**Problema**: A API não consegue processar o formato do arquivo de áudio.

**Soluções**:
1. Verifique se o FFmpeg está instalado corretamente (necessário para conversão)
2. Converta manualmente o arquivo para MP3 antes de fazer upload:
   ```
   ffmpeg -i seu_arquivo.m4a -codec:a libmp3lame -qscale:a 2 seu_arquivo.mp3
   ```
3. O sistema agora força a conversão para MP3 de certos formatos, mesmo que sejam válidos

### Erro "400 Bad Request" ou "401 Unauthorized"

**Problema**: Problema de autenticação com a API.

**Soluções**:
1. Verifique se as chaves de API no arquivo `.env` estão corretas
2. Confirme se as chaves possuem permissão para acesso aos modelos de transcrição
3. Verifique se as chaves não expiraram (algumas APIs possuem chaves temporárias)

### Ambas as APIs falham

Se tanto a API principal (Groq) quanto o fallback (Hugging Face) falharem:

1. Verifique a conectividade de internet
2. Confirme o status dos serviços em:
   - [Status Groq](https://status.groq.com/)
   - [Status Hugging Face](https://status.huggingface.co/)
3. Considere adicionar uma solução offline como fallback final

## Testando as APIs

Use o script de teste de áudio para verificar se as APIs estão funcionando corretamente:

```bash
python scripts/testar_audio.py
```

## Modificando Parâmetros de Transcrição

Para ajustar os parâmetros de transcrição, modifique os métodos:
- `_transcribe_with_groq` em `src/services/audio_service.py`
- `_transcribe_with_huggingface` em `src/services/audio_service.py`

Parâmetros comuns que podem ser ajustados:
- `model`: O modelo Whisper a ser utilizado (large-v3, medium, tiny, etc.)
- `temperature`: Controla aleatoriedade da transcrição
- `prompt`: Texto para guiar a transcrição

## Adicionando Novas APIs de Transcrição

Para adicionar uma nova API de transcrição como fallback, crie um novo método em `AudioService` seguindo o padrão dos existentes e inclua na cascata de fallback em `_transcribe_audio()`.
