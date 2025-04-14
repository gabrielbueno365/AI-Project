#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuração de logging estruturado para a aplicação.
Centraliza a configuração de logging para todo o sistema.
"""

import logging
import logging.handlers
import os
import json
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional


class EncodingFriendlyStreamHandler(logging.StreamHandler):
    """Handler que lida melhor com erros de codificação em diferentes terminais."""
    
    def emit(self, record):
        """Emite o registro com tratamento para erros de codificação."""
        try:
            msg = self.format(record)
            stream = self.stream
            # Substitui caracteres problemáticos comuns
            msg = msg.replace('→', '->')
            stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Tenta novamente codificando manualmente com substituição
            try:
                msg = self.format(record)
                stream = self.stream
                # Codifica com 'replace' para substituir caracteres não suportados
                if isinstance(msg, str):
                    msg = msg.encode(stream.encoding, 'replace').decode(stream.encoding)
                stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)
        except Exception:
            self.handleError(record)


class JsonFormatter(logging.Formatter):
    """
    Formatter que gera logs em formato JSON estruturado.
    Facilita análise posterior e integração com ferramentas de logs.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log como JSON.
        
        Args:
            record: O registro de log
            
        Returns:
            String JSON formatada
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Adiciona informações de exceção, se disponíveis
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Adiciona dados extras do registro
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            }:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
    json_format: bool = False,
    user_visible: bool = False,
) -> None:
    """
    Configura o sistema de logging.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para o arquivo de log (opcional)
        console: Se True, adiciona handler para console
        json_format: Se True, usa formato JSON estruturado
        user_visible: Se True, logs também aparecem para o usuário no terminal
    """
    # Obtém o level numérico do logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove handlers existentes para evitar duplicação
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Cria o formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Adiciona console handler
    if console:
        # Usa nosso handler personalizado que trata erros de codificação
        console_handler = EncodingFriendlyStreamHandler()
        console_handler.setFormatter(formatter)
        
        # Se não devemos mostrar logs para o usuário, filtramos os logs do console
        if not user_visible:
            # Filtro personalizado para excluir logs específicos do console
            class UserInterfaceFilter(logging.Filter):
                def filter(self, record):
                    # Exibe apenas logs críticos e permite logs específicos para UI
                    return (record.levelno >= logging.CRITICAL or 
                            getattr(record, 'user_visible', False))
                    
            console_handler.addFilter(UserInterfaceFilter())
        
        root_logger.addHandler(console_handler)
    
    # Adiciona file handler se o caminho foi especificado
    if log_file:
        # Garante que o diretório do log existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Adiciona um RotatingFileHandler para limitar o tamanho do arquivo
        # Usamos 'utf-8' como encoding para garantir compatibilidade com caracteres especiais
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Ajusta o nível de alguns loggers de bibliotecas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging configurado com nível {log_level}")
