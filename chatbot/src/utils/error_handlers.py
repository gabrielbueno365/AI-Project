#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manipuladores de erro para a aplicação.
Configura tratamento de sinais e exceções globais.
"""

import logging
import signal
import sys
from typing import Callable, Any

logger = logging.getLogger(__name__)


def setup_error_handlers() -> None:
    """
    Configura manipuladores para sinais e exceções.
    Garante um encerramento gracioso da aplicação.
    """
    # Configura manipuladores de sinal
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _signal_handler)
    
    # Configura tratamento de exceções não capturadas
    sys.excepthook = _exception_handler
    
    logger.info("Manipuladores de erro configurados")


def _signal_handler(signum: int, frame: Any) -> None:
    """
    Manipulador de sinais para encerramento gracioso.
    
    Args:
        signum: Número do sinal recebido
        frame: Frame de execução atual
    """
    signal_name = signal.Signals(signum).name
    logger.info(f"Sinal recebido: {signal_name} ({signum})")
    
    # Realiza tarefas de limpeza, se necessário
    # ...
    
    logger.info("Encerrando aplicação...")
    sys.exit(0)


def _exception_handler(exctype: type, value: Exception, traceback: Any) -> None:
    """
    Manipulador global de exceções não capturadas.
    
    Args:
        exctype: Tipo da exceção
        value: Valor/mensagem da exceção
        traceback: Traceback da exceção
    """
    logger.critical(
        f"Exceção não capturada: {exctype.__name__}: {value}",
        exc_info=(exctype, value, traceback)
    )
    
    # Exibe informações úteis no console
    print(f"\nErro não tratado: {exctype.__name__}: {value}")
    print("Verifique os logs para mais detalhes.")
    
    # Realiza tarefas de limpeza, se necessário
    # ...
    
    sys.exit(1)


class RetryableError(Exception):
    """Exceção para erros que podem ser retentados."""
    pass


class PermanentError(Exception):
    """Exceção para erros que não devem ser retentados."""
    pass


async def retry_async(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Decorator para retry de funções assíncronas.
    
    Args:
        func: Função a ser executada
        max_retries: Número máximo de tentativas
        backoff_factor: Fator para backoff exponencial
        exceptions: Tupla de exceções a serem tratadas
        
    Returns:
        Resultado da função
        
    Raises:
        Exception: Se todas as tentativas falharem
    """
    import asyncio
    
    retries = 0
    while True:
        try:
            return await func()
        except exceptions as e:
            retries += 1
            
            # Se for um erro permanente, não tenta novamente
            if isinstance(e, PermanentError):
                logger.error(f"Erro permanente: {str(e)}")
                raise
            
            # Se atingiu o número máximo de tentativas, falha
            if retries >= max_retries:
                logger.error(f"Máximo de tentativas atingido ({max_retries}): {str(e)}")
                raise
            
            # Calcula tempo de espera para backoff exponencial
            wait_time = backoff_factor * (2 ** (retries - 1))
            logger.warning(
                f"Tentativa {retries}/{max_retries} falhou: {str(e)}. "
                f"Tentando novamente em {wait_time:.2f}s"
            )
            
            # Aguarda antes da próxima tentativa
            await asyncio.sleep(wait_time)
