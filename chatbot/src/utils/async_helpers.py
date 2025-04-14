#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilitários para auxiliar no desenvolvimento assíncrono.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar, Optional, Dict, List, Coroutine

logger = logging.getLogger(__name__)
T = TypeVar('T')


async def limit_concurrency(
    coro: Coroutine[Any, Any, T],
    semaphore: asyncio.Semaphore
) -> T:
    """
    Limita a concorrência de uma coroutine usando um semáforo.
    
    Args:
        coro: Coroutine a ser executada
        semaphore: Semáforo para controle de concorrência
        
    Returns:
        Resultado da coroutine
    """
    async with semaphore:
        return await coro


async def gather_with_concurrency(
    n: int, 
    *coros: Coroutine[Any, Any, T],
    return_exceptions: bool = False
) -> List[T]:
    """
    Executa coroutines com limite de concorrência.
    
    Args:
        n: Número máximo de coroutines concorrentes
        *coros: Coroutines a serem executadas
        return_exceptions: Se True, retorna exceções em vez de propagá-las
        
    Returns:
        Lista com os resultados das coroutines
    """
    semaphore = asyncio.Semaphore(n)
    return await asyncio.gather(
        *(limit_concurrency(c, semaphore) for c in coros),
        return_exceptions=return_exceptions
    )


def async_timed() -> Callable:
    """
    Decorator para medir o tempo de execução de funções assíncronas.
    
    Returns:
        Função decorada
    """
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                logger.debug(f"{func.__name__} executado em {end - start:.4f}s")
        return wrapped
    return wrapper


class AsyncCache:
    """
    Cache simples para resultados de funções assíncronas.
    """
    
    def __init__(self, ttl: int = 3600):
        """
        Inicializa o cache.
        
        Args:
            ttl: Tempo de vida dos itens em segundos
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def __call__(self, func: Callable) -> Callable:
        """
        Aplica o cache à função.
        
        Args:
            func: Função a ser cacheada
            
        Returns:
            Função decorada
        """
        @functools.wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            # Cria uma chave baseada nos argumentos
            key = self._make_key(func.__name__, args, kwargs)
            
            # Verifica se o item está no cache e é válido
            if key in self.cache:
                item = self.cache[key]
                if time.time() - item["timestamp"] < self.ttl:
                    logger.debug(f"Cache hit para {func.__name__}")
                    return item["result"]
            
            # Executa a função e armazena o resultado
            result = await func(*args, **kwargs)
            self.cache[key] = {
                "result": result,
                "timestamp": time.time()
            }
            logger.debug(f"Cache miss para {func.__name__}")
            return result
            
        return wrapped
    
    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Cria uma chave única para os argumentos.
        
        Args:
            func_name: Nome da função
            args: Argumentos posicionais
            kwargs: Argumentos nomeados
            
        Returns:
            Chave para o cache
        """
        # Implementação simples, pode ser melhorada para casos complexos
        args_str = ','.join(str(arg) for arg in args)
        kwargs_str = ','.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{func_name}({args_str},{kwargs_str})"
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self.cache.clear()
        logger.debug("Cache limpo")
    
    def clear_item(self, func_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Remove um item específico do cache.
        
        Args:
            func_name: Nome da função
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
        """
        key = self._make_key(func_name, args, kwargs)
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Item removido do cache: {key}")
