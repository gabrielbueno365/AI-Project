# Módulo de Otimização de Prompts

Este módulo implementa otimizações para o uso eficiente de tokens e suporte a processamento de entradas longas.

## Funcionalidades Principais

### 1. Otimização de Tokens

As funções `optimize_system_message` e `optimize_messages` reduzem o uso de tokens removendo redundâncias, convertendo frases verbosas para imperativas e normalizando o texto, sem alterar o significado original.

### 2. Processamento em Chunks

O sistema de processamento em chunks permite lidar com textos longos, dividindo-os em partes gerenciáveis, processando cada parte separadamente e combinando os resultados de forma inteligente.

### 3. Estimativa de Tokens

Fornece métodos para estimar o número de tokens em um texto, permitindo decisões dinâmicas sobre quando aplicar otimizações.

## Como Usar

### Otimização de Mensagens

```python
from src.utils.prompt.optimizers import optimize_token_usage

# Obtém versão otimizada das mensagens e max_tokens recomendado
messages = [{"role": "user", "content": "texto longo..."}]
optimized_messages, recommended_max_tokens = optimize_token_usage(messages)
```

### Processamento em Chunks

```python
from src.utils.prompt.optimizers import process_in_chunks

async def process_chunk(chunk_text, **kwargs):
    # Lógica para processar um chunk
    return processed_result

# Processa um texto longo em chunks
result = await process_in_chunks(long_text, process_chunk)
```

## Benefícios

1. **Economia de Tokens**: Reduz custos de API e permite lidar com mais contexto
2. **Suporte a Textos Longos**: Processa entradas que excederiam limites normais
3. **Respostas Melhores**: Ao otimizar prompts, melhora a qualidade das respostas
