# Processamento de Áudio

Este documento descreve como funciona o processamento de áudio no chatbot inteligente.

## Requisitos

Para que o processamento de áudio funcione corretamente, você precisa:

1. **FFmpeg instalado** no sistema: Usado para conversão de formatos de áudio
2. **Python 3.11+**: Com as dependências instaladas via Poetry

## Instalação do FFmpeg

### Método Automático
Execute o script de instalação incluído no projeto:

```bash
# Windows
python scripts/install_ffmpeg.py

# Linux/macOS
python3 scripts/install_ffmpeg.py
```

### Instalação Manual

#### Windows
1. Baixe o FFmpeg do site oficial: https://ffmpeg.org/download.html
2. Extraia os arquivos
3. Adicione o diretório `bin` ao PATH do sistema

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

## Formatos de Áudio Suportados

O sistema suporta os seguintes formatos de áudio:
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- FLAC (.flac)
- M4A (.m4a)
- AAC (.aac)
- MP4 (.mp4) - apenas a parte de áudio

Formatos não suportados são automaticamente convertidos para MP3 usando FFmpeg.

## Transcrição de Áudio

A transcrição é realizada usando a API Whisper através da Groq API. Em caso de falha na Groq, o sistema faz fallback para a API do Hugging Face.

## Solução de Problemas

### Erro "The system cannot find the file specified"

Este erro geralmente ocorre por um dos seguintes motivos:

1. **FFmpeg não está instalado** ou não está no PATH do sistema
   - Solução: Execute o script de instalação do FFmpeg

2. **Permissão de acesso negada ao arquivo**
   - Solução: Verifique permissões e caminhos

3. **Problemas no diretório temporário**
   - Solução: Certifique-se de que o usuário tem permissão de escrita no diretório temp

### Verificando a instalação do FFmpeg

```bash
# Para verificar se o ffmpeg está instalado corretamente:
ffmpeg -version
```

Se este comando não funcionar, o FFmpeg não está instalado ou não está no PATH.

## Logs

Os logs detalhados do processamento de áudio são salvos no sistema de log padrão do aplicativo. Você pode verificar os logs para diagnosticar problemas.
