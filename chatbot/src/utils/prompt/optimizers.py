#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Otimizadores de prompts e utilitários para eficiência de tokens.
Implementa técnicas para reduzir o uso de tokens e melhorar a eficiência das chamadas API.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Aproximação de tokens por caracteres (para quando não temos tokenizador disponível)
AVG_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """
    Estima o número de tokens em um texto usando uma heurística simples.
    
    Args:
        text: Texto a ser estimado
        
    Returns:
        Número estimado de tokens
    """
    if not text:
        return 0
    
    # Uma estimativa simples é dividir o número de caracteres por 4
    # (média aproximada para idiomas latinos no GPT)
    return len(text) // AVG_CHARS_PER_TOKEN


def optimize_system_message(system_message: str) -> str:
    """
    Otimiza mensagens de sistema para usar menos tokens.
    
    Args:
        system_message: Mensagem de sistema original
        
    Returns:
        Mensagem de sistema otimizada
    """
    # 1. Remover redundâncias comuns
    redundant_phrases = [
        r"Lembre-se (?:de )?que",
        r"Por favor,? ",
        r"É importante (?:notar|lembrar|destacar) que",
        r"Observe que",
        r"Note que",
        r"Vale (?:a pena )?(?:notar|lembrar|destacar) que"
    ]
    
    result = system_message
    for phrase in redundant_phrases:
        result = re.sub(phrase, "", result, flags=re.IGNORECASE)
    
    # 2. Converter instruções verbosas para imperativas diretas
    verbose_patterns = [
        (r"Você deve sempre", "Sempre"),
        (r"Você deve", ""),
        (r"Você precisa", ""),
        (r"Você não deve", "Não"),
        (r"Você é um assistente que", "Assistente que"),
        (r"Sua função é", "Função:"),
        (r"Sua tarefa é", "Tarefa:"),
    ]
    
    for pattern, replacement in verbose_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # 3. Remover espaços extras e normalizar pontuação
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\s*([.,;:!?])', r'\1', result)
    
    # 4. Condensar parágrafos curtos
    result = re.sub(r'(\w)\.\s+(\w)', r'\1. \2', result)
    
    logger.debug(f"Economia de tokens: {estimate_tokens(system_message) - estimate_tokens(result)}")
    return result.strip()


def optimize_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Otimiza uma lista de mensagens para usar menos tokens.
    
    Args:
        messages: Lista de mensagens no formato {"role": "...", "content": "..."}
        
    Returns:
        Lista otimizada de mensagens
    """
    optimized = []
    
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        # Sistema: aplica otimização mais agressiva
        if role == "system":
            optimized.append({
                "role": role,
                "content": optimize_system_message(content)
            })
        
        # Usuário: mantém intacto para preservar a intenção
        elif role == "user":
            optimized.append(msg)
        
        # Assistente: pode ser ligeiramente otimizado
        elif role == "assistant":
            # Remove apenas redundâncias óbvias
            cleaned = re.sub(r'(De qualquer forma|Em todo caso|Como eu estava dizendo)', '', content)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            optimized.append({
                "role": role,
                "content": cleaned
            })
        
        # Outros tipos de mensagens: manter como estão
        else:
            optimized.append(msg)
    
    return optimized


def chunk_long_content(content: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Divide conteúdo longo em chunks menores com sobreposição.
    Tenta dividir em limites de frases completas.
    
    Args:
        content: Texto a ser dividido
        chunk_size: Tamanho aproximado de cada chunk em tokens
        overlap: Sobreposição entre chunks em tokens
        
    Returns:
        Lista de chunks de texto
    """
    if estimate_tokens(content) <= chunk_size:
        return [content]
    
    # Converte chunk_size e overlap de tokens para caracteres
    char_chunk_size = chunk_size * AVG_CHARS_PER_TOKEN
    char_overlap = overlap * AVG_CHARS_PER_TOKEN
    
    # Divide o texto em frases
    sentences = re.split(r'(?<=[.!?])\s+', content)
    
    chunks = []
    current_chunk = ""
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        # Se a frase for muito grande, podemos dividir por parágrafos
        if sentence_size > char_chunk_size:
            paragraphs = sentence.split('\n\n')
            
            if len(paragraphs) > 1:
                # Processa a sentença atual
                for paragraph in paragraphs:
                    if current_size + len(paragraph) <= char_chunk_size:
                        current_chunk += paragraph + "\n\n"
                        current_size += len(paragraph) + 2
                    else:
                        # Finaliza o chunk atual e inicia um novo
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        
                        # Se o parágrafo for muito grande, divida-o
                        if len(paragraph) > char_chunk_size:
                            sub_chunks = split_large_paragraph(paragraph, char_chunk_size)
                            chunks.extend(sub_chunks[:-1])
                            current_chunk = sub_chunks[-1]
                            current_size = len(current_chunk)
                        else:
                            current_chunk = paragraph + "\n\n"
                            current_size = len(paragraph) + 2
            else:
                # Se ainda for grande, mas não tem parágrafos, divide por tamanho
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                sub_chunks = split_large_paragraph(sentence, char_chunk_size)
                chunks.extend(sub_chunks[:-1])
                current_chunk = sub_chunks[-1]
                current_size = len(current_chunk)
        
        # Frase normal
        elif current_size + sentence_size <= char_chunk_size:
            current_chunk += sentence + " "
            current_size += sentence_size + 1
        else:
            # Finaliza o chunk atual e inicia um novo
            chunks.append(current_chunk.strip())
            
            # Início do novo chunk inclui sobreposição do final anterior, se possível
            if current_size > char_overlap:
                # Encontra um ponto adequado para dividir com sobreposição
                overlap_text = get_overlap_text(current_chunk, char_overlap)
                current_chunk = overlap_text + sentence + " "
                current_size = len(current_chunk)
            else:
                current_chunk = sentence + " "
                current_size = sentence_size + 1
    
    # Adiciona o último chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def split_large_paragraph(paragraph: str, max_size: int) -> List[str]:
    """
    Divide um parágrafo grande em pedaços menores, tentando
    manter a divisão em limites de frases.
    
    Args:
        paragraph: Parágrafo a ser dividido
        max_size: Tamanho máximo em caracteres
        
    Returns:
        Lista de sub-parágrafos
    """
    if len(paragraph) <= max_size:
        return [paragraph]
    
    result = []
    # Tenta dividir por frases
    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
    
    current_chunk = ""
    current_size = 0
    
    for sentence in sentences:
        if len(sentence) > max_size:
            # Se uma única frase for muito grande, divide por tamanho
            if current_chunk:
                result.append(current_chunk.strip())
                current_chunk = ""
                current_size = 0
            
            # Divide a frase em partes iguais
            parts = []
            for i in range(0, len(sentence), max_size - 100):
                part = sentence[i:i + max_size - 100]
                if i > 0:
                    part = "... " + part
                if i + max_size - 100 < len(sentence):
                    part = part + " ..."
                parts.append(part)
            
            result.extend(parts[:-1])
            current_chunk = parts[-1] + " "
            current_size = len(current_chunk)
        elif current_size + len(sentence) <= max_size:
            current_chunk += sentence + " "
            current_size += len(sentence) + 1
        else:
            result.append(current_chunk.strip())
            current_chunk = sentence + " "
            current_size = len(sentence) + 1
    
    if current_chunk:
        result.append(current_chunk.strip())
    
    return result


def get_overlap_text(text: str, overlap_size: int) -> str:
    """
    Extrai um trecho de sobreposição do final de um texto.
    
    Args:
        text: Texto original
        overlap_size: Tamanho da sobreposição em caracteres
        
    Returns:
        Texto de sobreposição
    """
    if len(text) <= overlap_size:
        return text
    
    # Tenta encontrar um limite de frase dentro da sobreposição
    overlap_text = text[-overlap_size:]
    sentence_boundary = re.search(r'[.!?]\s+', overlap_text)
    
    if sentence_boundary:
        # Encontrou um limite de frase: começa do início dessa frase
        pos = sentence_boundary.end()
        return overlap_text[pos:]
    
    # Caso contrário, usa o ponto de sobreposição exato
    return overlap_text


def optimize_token_usage(messages: List[Dict[str, str]], 
                         max_prompt_tokens: int = 3000,
                         min_completion_tokens: int = 500) -> Tuple[List[Dict[str, str]], int]:
    """
    Otimiza o uso de tokens para uma chamada de API, garantindo espaço para a resposta.
    
    Args:
        messages: Lista de mensagens de contexto
        max_prompt_tokens: Máximo de tokens permitidos para o prompt
        min_completion_tokens: Mínimo de tokens necessários para a resposta
        
    Returns:
        Tupla (mensagens otimizadas, recommended_max_tokens)
    """
    # 1. Primeiro otimiza os prompts para reduzir uso de tokens
    optimized_messages = optimize_messages(messages.copy())
    
    # 2. Estima o uso atual de tokens
    total_tokens = sum(estimate_tokens(msg["content"]) for msg in optimized_messages)
    logger.debug(f"Uso estimado de tokens após otimização: {total_tokens}")
    
    # 3. Se ainda exceder o limite, começa a remover mensagens do meio
    # (mantendo sempre sistema + últimas 3-4 mensagens)
    if total_tokens > max_prompt_tokens:
        logger.info(f"Contexto excede limite de tokens ({total_tokens} > {max_prompt_tokens})")
        
        # Preserva a mensagem de sistema e as últimas 3 mensagens
        preserved = []
        
        # Mantém a mensagem de sistema
        system_messages = [msg for msg in optimized_messages if msg["role"] == "system"]
        if system_messages:
            preserved.extend(system_messages)
        
        # Adiciona as últimas 3 mensagens (ou todas se houver menos que 3)
        user_assistant_messages = [msg for msg in optimized_messages 
                                  if msg["role"] in ["user", "assistant"]]
        preserved.extend(user_assistant_messages[-3:])
        
        # Substitui as mensagens originais
        optimized_messages = preserved
        total_tokens = sum(estimate_tokens(msg["content"]) for msg in optimized_messages)
        logger.info(f"Contexto reduzido para {total_tokens} tokens após remoção de mensagens")
    
    # 4. Determina o max_tokens recomendado para a resposta
    # (menor é mais econômico, maior é mais completo)
    if total_tokens < 1000:
        # Para prompts curtos, permite respostas maiores
        recommended_max_tokens = 1500
    elif total_tokens < 2000:
        # Para prompts médios, ajusta proporcionalmente
        recommended_max_tokens = 1000
    else:
        # Para prompts longos, mantém o mínimo necessário
        recommended_max_tokens = min_completion_tokens
    
    logger.debug(f"Max tokens recomendado para resposta: {recommended_max_tokens}")
    return optimized_messages, recommended_max_tokens


def process_in_chunks(content: str, 
                     processor_func: callable, 
                     chunk_size: int = 800,
                     overlap: int = 100,
                     **kwargs) -> str:
    """
    Processa conteúdo longo em chunks e combina os resultados.
    
    Args:
        content: Conteúdo a ser processado
        processor_func: Função que processa cada chunk (deve aceitar uma string)
        chunk_size: Tamanho aproximado de cada chunk em tokens
        overlap: Sobreposição entre chunks em tokens
        **kwargs: Argumentos adicionais para processor_func
        
    Returns:
        Resultado combinado do processamento
    """
    # Se o conteúdo for pequeno o suficiente, processa diretamente
    if estimate_tokens(content) <= chunk_size:
        return processor_func(content, **kwargs)
    
    # Divide em chunks
    chunks = chunk_long_content(content, chunk_size, overlap)
    logger.info(f"Dividindo conteúdo em {len(chunks)} chunks para processamento")
    
    # Processa cada chunk
    results = []
    for i, chunk in enumerate(chunks):
        logger.debug(f"Processando chunk {i+1}/{len(chunks)} ({estimate_tokens(chunk)} tokens estimados)")
        
        # Adiciona informação de contexto para cada chunk
        if len(chunks) > 1:
            context_info = f"[Parte {i+1} de {len(chunks)}] "
            augmented_chunk = context_info + chunk
        else:
            augmented_chunk = chunk
        
        # Processa o chunk
        chunk_result = processor_func(augmented_chunk, **kwargs)
        results.append(chunk_result)
    
    # Combina os resultados
    combined = "\n\n".join(results)
    
    # Se houver muitos chunks, adiciona um resumo conciso
    if len(chunks) > 3:
        logger.info("Adicionando resumo consolidado para conteúdo extenso")
        summary_prompt = (
            f"O texto a seguir contém {len(chunks)} partes de uma análise mais longa. "
            f"Forneça um resumo conciso e consolidado em um parágrafo:\n\n{combined}"
        )
        
        try:
            summary = processor_func(summary_prompt, max_tokens=250, **kwargs)
            combined = f"**Resumo Executivo:** {summary}\n\n{combined}"
        except Exception as e:
            logger.warning(f"Não foi possível gerar resumo: {e}")
    
    return combined
