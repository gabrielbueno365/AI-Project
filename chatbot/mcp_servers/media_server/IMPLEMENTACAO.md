# Implementação do Servidor MCP de Mídia

## Visão Geral

Este documento resume a implementação do servidor MCP para processamento de mídia, parte da Fase 2 do projeto de expansão do chatbot com servidores MCP.

## Estrutura Implementada

```
mcp_servers/
  media_server/
    ├── pyproject.toml        # Configuração Poetry com dependências isoladas
    ├── README.md             # Documentação básica
    ├── IMPLEMENTACAO.md      # Este documento
    └── src/
        ├── __init__.py
        ├── server.py         # Implementação principal do servidor MCP
        └── helpers.py        # Funções auxiliares para processamento de áudio
```

## Principais Funcionalidades

1. **Transcrição de Áudio**: 
   - Implementação da ferramenta `transcribe_audio`
   - Suporte a múltiplos formatos de áudio
   - Conversão automática de formatos não suportados
   - Fallback entre Groq e HuggingFace para transcrição
   - Validação de tamanho e duração

2. **Extração de Áudio**:
   - Implementação da ferramenta `extract_audio_uri`
   - Extração da trilha de áudio de arquivos de vídeo
   - Configuração de qualidade e formato

## Integração com o Sistema Existente

O servidor MCP de mídia foi implementado considerando a base de código existente:

1. **Reuso de Código**: 
   - As funções auxiliares foram adaptadas da implementação original em `audio_service.py`
   - Mantida a lógica de processamento principal, incluindo conversão e sanitização

2. **Compatibilidade**:
   - Interface consistente com a implementação anterior
   - Valores padrão alinhados com as configurações existentes
   - Suporte para os mesmos formatos e limitações

3. **Preparação para Migração**:
   - Cliente MCP implementado para facilitar a integração
   - Script de teste para validação independente
   - Documentação clara do processo de migração

## Cliente MCP

Foi implementado um cliente MCP para facilitar o uso do servidor:

```python
src/clients/media.py
```

Este cliente fornece:
- Gerenciamento da conexão com o servidor
- Métodos para chamar as ferramentas do servidor
- Tratamento de erros
- Interface Pythônica para usar as ferramentas MCP

## Configuração

A configuração do servidor foi implementada em múltiplos níveis:

1. **Variáveis de Ambiente**:
   - Chaves de API (`GROQ_API_KEY`, `HUGGING_FACE_API_KEY`)
   - Comando para iniciar o servidor (`MEDIA_SERVER_CMD`)

2. **Argumentos de Linha de Comando**:
   - Tamanho máximo de áudio (`--max-audio-size`)
   - Duração máxima de áudio (`--max-audio-duration`)
   - Modelo Whisper (`--whisper-model`)
   - Idioma (`--whisper-language`)
   - Diretório temporário (`--temp-dir`)

3. **Valores Padrão**:
   - Definidos no código para facilitar o uso imediato

## Testes

Foi implementado um script de teste para validar o funcionamento do servidor:

```python
scripts/test_mcp_media.py
```

Este script permite:
- Testar a transcrição de arquivos de áudio
- Testar a extração de áudio de vídeos
- Validar a conexão com o servidor MCP

## Documentação

Foram criados documentos detalhados para facilitar o uso e integração:

1. **README.md**: Visão geral e instruções básicas
2. **IMPLEMENTACAO.md**: Detalhes técnicos (este documento)
3. **docs/Audio/migracao-mcp.md**: Plano de migração do sistema existente
4. **docs/Audio/mcp-media-guia.md**: Guia completo de instalação e uso

## Próximos Passos

1. **Testes de Integração**:
   - Testar com o Host MCP principal
   - Validar a integração com outros servidores MCP

2. **Migração Completa**:
   - Refatorar `ChatbotApp` para usar o cliente MCP
   - Remover a implementação original após validação

3. **Otimizações**:
   - Implementar cache para transcrições
   - Otimizar o gerenciamento de arquivos temporários
   - Melhorar o tratamento de erros em situações específicas
