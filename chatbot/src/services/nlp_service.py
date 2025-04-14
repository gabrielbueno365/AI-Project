#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serviço de processamento de linguagem natural.
Gerencia a interação com modelos e a seleção do serviço apropriado.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from src.core.config import get_settings
from src.services.api_service import HuggingFaceService, GroqService, FireworksAIService

logger = logging.getLogger(__name__)
settings = get_settings()


class NLPService:
    """
    Serviço que gerencia o processamento de linguagem natural.
    Roteia requisições para os provedores de API apropriados.
    """
    
    def __init__(self):
        """Inicializa o serviço de NLP."""
        logger.info("Inicializando serviço de NLP")
        
        # Inicializa os serviços de API
        self.huggingface_service = HuggingFaceService()
        self.groq_service = GroqService()
        self.fireworks_service = FireworksAIService()
        
        # Configura parâmetros padrão
        self.max_tokens = 500
    
    async def process_text(
        self, 
        text: str, 
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Processa o texto de entrada e gera uma resposta.
        
        Args:
            text: Texto de entrada do usuário
            context: Contexto da conversa (opcional)
            
        Returns:
            Resposta gerada
        """
        logger.info(f"Processando texto: {text[:50]}...")
        
        # Se não houver contexto, cria uma lista apenas com a mensagem atual
        if not context:
            messages = [{"role": "user", "content": text}]
        else:
            # Usa o contexto fornecido e adiciona a nova mensagem
            messages = context + [{"role": "user", "content": text}]
        
        # Determina qual serviço usar com base na complexidade
        response = await self._route_to_best_service(messages)
        
        return response
    
    async def _route_to_best_service(self, messages: List[Dict[str, str]]) -> str:
        """
        Roteia a requisição para o melhor serviço disponível.
        Implementa um sistema de fallback em cascata.
        
        Args:
            messages: Lista de mensagens da conversa
            
        Returns:
            Resposta gerada
        """
        # Estratégia 1: Tenta usar o serviço Fireworks AI (primeira escolha)
        try:
            logger.info("Tentando gerar resposta com Fireworks AI")
            response = await self.fireworks_service.generate_text(
                messages=messages,
                max_tokens=self.max_tokens
            )
            logger.info("Resposta gerada com sucesso usando Fireworks AI")
            return response
        except Exception as e:
            logger.warning(f"Falha ao usar Fireworks AI: {str(e)}")
        
        # Estratégia 2: Tenta usar o serviço Groq como fallback
        try:
            logger.info("Tentando gerar resposta com Groq (fallback)")
            response = await self.groq_service.generate_text(
                messages=messages,
                max_tokens=self.max_tokens
            )
            logger.info("Resposta gerada com sucesso usando Groq")
            return response
        except Exception as e:
            logger.warning(f"Falha ao usar Groq: {str(e)}")
        
        # Estratégia 3: Última tentativa com Hugging Face
        try:
            logger.info("Tentando gerar resposta com Hugging Face (último recurso)")
            response = await self.huggingface_service.generate_text(
                messages=messages,
                max_tokens=self.max_tokens
            )
            logger.info("Resposta gerada com sucesso usando Hugging Face")
            return response
        except Exception as e:
            logger.error(f"Todas as estratégias falharam: {str(e)}")
            return "Desculpe, não foi possível gerar uma resposta no momento. Por favor, tente novamente mais tarde."
