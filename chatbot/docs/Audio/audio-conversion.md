# Conversão Automática de Formatos de Áudio

## Visão Geral

O chatbot implementa um sistema de conversão automática de formatos de áudio, permitindo que praticamente qualquer arquivo de áudio conhecido seja processado sem intervenção manual do usuário. Esta funcionalidade se integra perfeitamente ao sistema de processamento de áudio existente, tornando a experiência mais fluida e abrangente.

## Como Funciona

1. **Detecção**: O sistema analisa o formato do arquivo carregado.
2. **Decisão**: Se o formato for suportado nativamente, o arquivo é usado diretamente. Caso contrário, ele é marcado para conversão.
3. **Conversão**: Arquivos não suportados são convertidos automaticamente para MP3 usando FFmpeg.
4. **Limpeza**: Os arquivos temporários são removidos após o processamento.

## Fluxo de Processamento

```
Arquivo de Áudio Original
        │
        ▼
┌─────────────────┐
│ Verificação de  │
│ Formato/MIME    │
└────────┬────────┘
         │
         ▼
      Formato      
     suportado?    
     /       \     
    Sim       Não  
    |          |   
    |          ▼   
    |    ┌──────────────┐
    |    │  Conversão   │
    |    │  para MP3    │
    |    └───────┬──────┘
    |            |
    ▼            ▼
┌────────────────────┐
│    Transcrição     │
│    via Whisper     │
└────────────────────┘
```

## Parâmetros de Conversão Configuráveis

A conversão pode ser personalizada através dos seguintes parâmetros:

| Parâmetro | Valor Padrão | Descrição |
|-----------|--------------|-----------|
| `target_format` | mp3 | Formato para o qual converter (mp3, wav, etc.) |
| `audio_quality` | 192k | Taxa de bits para codificação (qualidade) |
| `sample_rate` | 44100 | Taxa de amostragem em Hz |
| `channels` | 2 | Número de canais (2 = estéreo) |

## Formatos Suportados

### Formatos Nativos (Sem Conversão)
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- FLAC (.flac)
- M4A (.m4a)
- AAC (.aac)
- MP4 (.mp4)
- MPEG (.mpeg, .mpga)
- WebM (.webm)

### Formatos Automaticamente Convertidos
- Windows Media Audio (.wma)
- Audio Interchange File Format (.aiff, .aif)
- 3GPP (.3gp)
- Adaptive Multi-Rate (.amr)
- Real Audio (.ra, .rm)
- VOX (.vox)
- Raw Audio (.raw)
- AU (.au)
- DCT (.dct)
- GSM (.gsm)
- Protected AAC (.m4p)
- MIDI (.mid, .midi)
- Opus (.opus)

## Implementação Técnica

### Dependências
- **FFmpeg**: Biblioteca principal para conversão de áudio
- **Python-FFmpeg**: Wrapper Python para FFmpeg
- **Python-Magic**: Detecção precisa de MIME types

### Componentes Principais

1. **Função de detecção**: `verify_audio_format()` - Verifica se o formato precisa de conversão
2. **Função de conversão**: `convert_audio()` - Realiza a conversão para o formato desejado
3. **Função de sanitização**: `sanitize_audio_file()` - Decide se o arquivo precisa ser convertido

### Código da Função de Conversão

```python
async def convert_audio(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    target_format: str = "mp3",
    audio_quality: str = "192k",
    sample_rate: int = 44100,
    channels: int = 2
) -> Path:
    """Converte um arquivo de áudio para o formato especificado usando FFmpeg."""
    # Configura a conversão com parâmetros otimizados
    await asyncio.to_thread(
        lambda: ffmpeg
        .input(str(input_path))
        .output(
            str(output_path),
            acodec='libmp3lame' if target_format == 'mp3' else 'pcm_s16le',
            ar=sample_rate,      # Taxa de amostragem
            ac=channels,         # Número de canais
            ab=audio_quality,    # Taxa de bits
            **{'loglevel': 'error'}
        )
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )
    return output_path
```

## Benefícios

1. **Experiência do usuário aprimorada**: Os usuários não precisam converter manualmente seus arquivos
2. **Maior compatibilidade**: O sistema funciona com praticamente qualquer formato de áudio
3. **Robustez**: A validação e conversão aumentam a resistência a erros
4. **Flexibilidade**: Conversão personalizada de acordo com as necessidades específicas

## Considerações de Desempenho

- A conversão adiciona um pequeno overhead de processamento (~1-3 segundos para arquivos típicos)
- Arquivos muito grandes podem levar mais tempo para converter
- A qualidade do áudio é mantida em um nível ótimo (192kbps)

## Cenários de Uso

1. **Arquivos de áudio antigos**: Converte formatos legados (.wma, .ra) para formatos modernos
2. **Áudio de celular**: Processa formatos comuns em dispositivos móveis (.3gp, .amr)
3. **Áudio de gravadores**: Lida com formatos específicos de dispositivos de gravação (.vox, .gsm)
4. **Áudio de produção musical**: Processa formatos de alta qualidade (.aiff, .raw, .au)

## Extensibilidade

O sistema pode ser facilmente estendido para suportar novos formatos adicionando:
1. Novos tipos MIME na lista `AUDIO_MIME_TYPES`
2. Novas extensões na lista `FORMATS_TO_CONVERT`
3. Codecs específicos na função `convert_audio()`
