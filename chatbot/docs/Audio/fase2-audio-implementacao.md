# Implementação de Processamento de Áudio - Fase 2

## Visão Geral

Esta etapa da Fase 2 implementa o processamento de arquivos de áudio no chatbot, permitindo que os usuários enviem arquivos de áudio para transcrição e análise. O sistema utiliza o Whisper (modelo large-v3-turbo) via Groq como solução primária, com fallback para Hugging Face quando necessário.

## Componentes Implementados

1. **Serviço de Áudio (`audio_service.py`)**
   - Funcionalidades principais de transcrição e processamento
   - Implementação do sistema de fallback entre APIs
   - Otimização para português do Brasil

2. **Utilitários de Áudio (`utils/audio/helpers.py`)**
   - Validação e sanitização de arquivos de áudio
   - Extração de metadados de áudio (duração, formato, etc.)
   - Funções de segurança para processamento de arquivos

3. **Segurança (`utils/security.py`)**
   - Verificação de MIME types para evitar uploads maliciosos
   - Validação de tamanho e formato de arquivos
   - Prevenção contra path traversal e outras vulnerabilidades

4. **Integração com APIs (`api_service.py`)**
   - Métodos para transcrição via Groq Whisper API
   - Métodos para transcrição via Hugging Face (fallback)
   - Tratamento de erros e retry policies

5. **Interface do Usuário (CLI) (`main.py`)**
   - Comandos para upload de arquivos de áudio
   - Opções para instruções adicionais após a transcrição
   - Visualização formatada dos resultados

## Arquitetura

O sistema segue uma arquitetura em camadas:

```
Interface do Usuário (CLI)
        │
        ▼
    ChatbotApp
    │      │
    │      ▼
    │  AudioService
    │      │
    │      ▼
    │   API Client ──────┐
    │      │             │
    │      ▼             ▼
    │   Groq API      HuggingFace API
    │   (Primário)    (Fallback)
    │
    ▼
NLP Service (processa o texto transcrito)
```

## Configurações Atuais

- **Modelo**: `whisper-large-v3-turbo` (versão mais leve e otimizada)
- **Idioma padrão**: Português do Brasil (`pt-BR`)
- **Tamanho máximo de arquivo**: 50MB
- **Duração máxima de áudio**: 5 minutos
- **Formatos suportados**: MP3, WAV, OGG, FLAC, M4A, etc.

## Fluxo de Processamento

1. O usuário digita "arquivo" ou "áudio" na interface
2. O sistema solicita o caminho do arquivo e instruções adicionais
3. O arquivo é validado quanto a formato, tamanho e segurança
4. O sistema extrai metadados do áudio (duração, formato, etc.)
5. O áudio é enviado para a API Whisper via Groq para transcrição
6. Em caso de falha, o sistema tenta via Hugging Face como backup
7. A transcrição é apresentada ao usuário
8. Opcionalmente, o sistema processa as instruções adicionais com base na transcrição

## Melhorias Implementadas

- **Otimização para português**: Configuração específica para transcrição em pt-BR
- **Sistema de fallback robusto**: Backup automático entre provedores de API
- **Validação de segurança**: Prevenção contra uploads maliciosos
- **Manuseio de erros detalhado**: Feedback claro sobre problemas no processamento
- **Documentação**: Instruções de uso e solução de problemas

## Próximos Passos

Seguindo a estrutura da Fase 2, os próximos componentes a serem implementados são:

1. Processamento de Vídeo
2. Processamento de Documentos
3. Sistema RAG (Retrieval-Augmented Generation)

Os avanços feitos nesta etapa estabelecem uma base sólida para a implementação de processamento de outros tipos de mídia, utilizando uma arquitetura consistente e modular.
