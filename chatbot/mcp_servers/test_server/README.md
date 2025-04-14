# Servidor MCP de Teste

Este é um servidor MCP simples para testar a configuração do ambiente MCP.

## Funcionalidades

O servidor implementa três tools básicas:

1. `hello_world`: Retorna uma mensagem de saudação com o nome fornecido
2. `add_numbers`: Soma dois números
3. `echo_message`: Retorna a mensagem recebida como parâmetro

## Uso

Para testar se sua configuração MCP está funcionando corretamente, execute:

```bash
poetry run python scripts/test_mcp.py
```

Este script inicia o servidor de teste e chama sua função `hello_world`.

## Estrutura

```
test_server/
├── src/
│   ├── __init__.py
│   └── server.py        # Implementação do servidor MCP
├── __init__.py
└── README.md            # Este arquivo
```

Este servidor é apenas para testes e não faz parte da funcionalidade principal do chatbot.
