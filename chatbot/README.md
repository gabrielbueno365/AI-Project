# Chatbot Inteligente - Fase 1

Este projeto implementa um chatbot baseado em terminal com capacidades de IA avançadas, utilizando modelos de linguagem de ponta via APIs.

## Descrição

O chatbot utiliza arquitetura assíncrona e integra-se com diversas APIs de LLM:

- Fireworks AI via HuggingFace
- Groq
- HuggingFace

A fase 1 implementa uma base sólida com:
- Interface de terminal
- Gerenciamento de contexto de conversas
- Processamento de linguagem natural básico
- Sistema de fallback entre APIs

## Instalação e Requisitos

### Pré-requisitos

- Python 3.11+
- Poetry (gerenciador de pacotes)

### Instalação

1. Clone o repositório:
   ```
   git clone <url-do-repositorio>
   cd chatbot
   ```

2. Instale as dependências com Poetry:
   ```
   poetry install
   ```

3. Configure as credenciais de API:
   - Crie um arquivo `.env` na raiz do projeto com suas chaves de API:
   ```
   HUGGINGFACE_TOKEN=sua_chave_aqui
   GROQ_API_KEY=sua_chave_aqui
   OPENAI_API_KEY=sua_chave_aqui
   GEMINI_API_KEY=sua_chave_aqui
   ```

## Execução

Para iniciar o chatbot:

```
poetry run python src/main.py
```

Ou ative o ambiente virtual e execute:

```
poetry shell
python src/main.py
```

## Estrutura do Projeto

```
/chatbot
├── /src                  # Código fonte principal
│   ├── /core             # Funcionalidades core
│   ├── /models           # Modelos de dados
│   ├── /services         # Serviços de API e processamento
│   ├── /utils            # Utilitários
│   └── main.py           # Ponto de entrada
├── /tests                # Testes (a serem implementados)
├── .env                  # Variáveis de ambiente
└── README.md             # Este arquivo
```

## Uso

- Digite perguntas ou mensagens naturalmente
- Use o comando "sair" para encerrar o chatbot

## Recursos Planejados (Próximas Fases)

- Processamento de mídia (áudio, vídeo)
- Leitura de arquivos
- RAG (Retrieval-Augmented Generation)
- Interface web
- Suporte a múltiplos modelos de IA

## Contribuição

Este projeto segue um plano de desenvolvimento estruturado. Contribuições devem ser alinhadas com o roadmap de fases.

## Licença

Todos os direitos reservados.
