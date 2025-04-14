# Processamento de Áudio - Documentação

## Visão Geral

O módulo de processamento de áudio permite que o chatbot transcreva e analise arquivos de áudio. Utilizamos a API Whisper da Groq como solução primária para transcrição, com fallback para a API Whisper via Hugging Face quando necessário. O sistema está otimizado para transcrever áudio em português do Brasil.

## Funcionalidades

- **Transcrição de áudio**: Converte fala em texto usando o modelo Whisper
- **Conversão automática de formatos**: Converte formatos não suportados para MP3
- **Análise do conteúdo transcrito**: Gera respostas baseadas na transcrição
- **Suporte a múltiplos formatos**: MP3, WAV, OGG, FLAC, M4A, entre outros

## Como Usar

1. Inicie o chatbot normalmente com `python src/main.py`
2. Digite "arquivo" ou "áudio" quando quiser processar um arquivo de áudio
3. Forneça o caminho completo para o arquivo quando solicitado (praticamente **qualquer formato de áudio** funcionará)
4. Opcionalmente, forneça instruções adicionais sobre como processar o conteúdo transcrito
5. O chatbot converterá o arquivo se necessário, transcreverá o áudio e responderá conforme suas instruções

## Exemplos de Uso

### Transcrição Simples
- Digite "arquivo" e forneça o caminho do áudio
- Pressione Enter nas instruções adicionais para apenas transcrever

### Análise de Conteúdo
- Digite "arquivo" e forneça o caminho do áudio
- Nas instruções adicionais, digite algo como "Resuma os pontos principais desta transcrição"

### Resposta a Perguntas
- Digite "arquivo" e forneça o caminho do áudio
- Nas instruções adicionais, pergunte algo como "Qual é a principal mensagem deste áudio?"

## Detalhes Técnicos

### APIs Utilizadas
- **Principal**: API Whisper (modelo large-v3-turbo) via Groq
- **Fallback**: API Whisper (modelo large-v3-turbo) via Hugging Face

### Idioma
- Otimizado para português do Brasil (pt-BR)
- Configuração via parâmetro `whisper_language` em `settings`

## Formatos Suportados

### Formatos Nativos (Usados Diretamente)
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- FLAC (.flac)
- M4A (.m4a)
- AAC (.aac)
- MP4 (.mp4) - apenas áudio
- MPEG (.mpeg, .mpga)
- WebM (.webm) - apenas áudio

### Formatos Convertidos Automaticamente
- WMA (.wma)
- AIFF (.aiff, .aif)
- 3GP (.3gp)
- AMR (.amr)
- Real Audio (.ra, .rm)
- VOX (.vox)
- Raw Audio (.raw)
- AU (.au)
- DCT (.dct)
- GSM (.gsm)
- M4P (.m4p)
- MIDI (.mid, .midi)
- Opus (.opus)

### Limitações
- Tamanho máximo do arquivo: 50MB
- Duração máxima: 5 minutos (300 segundos)
- Requer conectividade com internet para acesso às APIs

## Dependências

- `ffmpeg-python`: Extração de informações de áudio
- `python-magic`: Detecção segura de MIME types
- `filetype`: Validação adicional de tipos de arquivo

## Solução de Problemas

### Erro "Arquivo não encontrado"
- Verifique se o caminho do arquivo está correto e se o arquivo existe
- Use caminhos absolutos para evitar problemas relativos

### Erro "Formato não suportado"
- Este erro é raro agora, pois o sistema tenta converter automaticamente quase qualquer formato
- Se ainda ocorrer, pode ser que o formato seja extremamente incomum ou corrompido

### Erro "Arquivo muito grande"
- Divida arquivos maiores que 50MB
- Comprima o áudio para reduzir o tamanho do arquivo

### Erro "Áudio muito longo"
- Divida áudios com mais de 5 minutos em segmentos menores

### Falhas na Transcrição
- Verifique sua conexão com a internet
- Tente novamente mais tarde se as APIs estiverem indisponíveis
