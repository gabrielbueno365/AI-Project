#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Serviço para processamento e transcrição de arquivos de áudio.
Utiliza a API Whisper via Groq para transcrever áudio para texto.
Inclui conversão automática de formatos não suportados.
"""

import asyncio
import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, BinaryIO

from src.core.config import get_settings
from src.utils.audio.helpers import (
    verify_audio_format, 
    sanitize_audio_file, 
    get_audio_info,
    ALLOWED_AUDIO_FORMATS,
    FORMATS_TO_CONVERT,
)
from src.utils.security import validate_file_safety

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioService:
    """
    Serviço para processamento e transcrição de arquivos de áudio.
    Integra com a API Whisper da Groq para transcrição.
    Suporta conversão automática de formatos não suportados.
    """
    
    def __init__(self):
        """Inicializa o serviço de áudio."""
        self.temp_dir = Path(tempfile.gettempdir()) / "chatbot_audio"
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            # Verifica se tem permissão de escrita no diretório
            test_file = self.temp_dir / "test_write.tmp"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Diretório temporário para áudio criado com sucesso: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Erro ao criar/verificar diretório temporário: {str(e)}")
            # Tenta criar em outro local
            self.temp_dir = Path(os.getcwd()) / "temp" / "audio"
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.info(f"Usando diretório temporário alternativo: {self.temp_dir}")
        
        # Configurações para processamento de áudio
        self.max_audio_size = settings.max_audio_size
        self.max_audio_duration = settings.max_audio_duration
        self.whisper_model = settings.whisper_model
        self.whisper_language = settings.whisper_language
        
        # Formatos de áudio suportados (tanto diretos quanto convertíveis)
        self.supported_formats = ALLOWED_AUDIO_FORMATS + FORMATS_TO_CONVERT
        
        logger.info(f"Serviço de áudio inicializado com suporte para formatos: {', '.join(self.supported_formats)}")
    
    async def process_audio(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Processa um arquivo de áudio: valida, converte (se necessário), extrai informações e transcreve.
        
        Args:
            file_path: Caminho para o arquivo de áudio
            
        Returns:
            Dicionário com informações e transcrição do áudio
        """
        path = Path(file_path)
        
        # Log inicial
        logger.info(f"Processando arquivo de áudio: {path.name}")
        
        # Validação de segurança básica (existência do arquivo, tipo básico)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        
        # Validação de segurança
        is_safe, reason = await validate_file_safety(path, "audio")
        if not is_safe:
            # Se a rejeição for apenas pelo tipo, tentamos converter mesmo assim
            if "Tipo MIME não permitido" in reason or "Formato de arquivo não suportado" in reason:
                logger.warning(f"Arquivo pode precisar de conversão: {reason}")
            else:
                logger.warning(f"Arquivo rejeitado por segurança: {reason}")
                raise ValueError(f"Arquivo inseguro: {reason}")
        
        try:
            # Sanitiza e, se necessário, converte o arquivo
            clean_path = await sanitize_audio_file(
                path, self.temp_dir, self.max_audio_size
            )
            
            # Mostra informação sobre conversão se ocorreu
            converted_msg = ""
            if clean_path.name.startswith("converted_"):
                converted_msg = f" (convertido de {path.suffix} para {clean_path.suffix})"
                logger.info(f"Arquivo convertido: {path.suffix} -> {clean_path.suffix}")
            
            # Obtém informações do áudio
            audio_info = await get_audio_info(clean_path)
            
            # Verifica duração máxima
            if audio_info["duration"] > self.max_audio_duration:
                raise ValueError(
                    f"Áudio muito longo: {audio_info['duration']:.2f} segundos "
                    f"(máximo: {self.max_audio_duration} segundos)"
                )
            
            # Transcreve o áudio
            transcription = await self._transcribe_audio(clean_path)
            
            # Monta resultado
            result = {
                "type": "audio",
                "filename": path.name + converted_msg,
                "duration": audio_info["duration"],
                "transcription": transcription,
                "sample_rate": audio_info["sample_rate"],
                "channels": audio_info["channels"],
                "format": audio_info["format"],
                "was_converted": converted_msg != ""
            }
            
            # Limpa arquivo temporário se necessário
            if clean_path != path and clean_path.exists():
                clean_path.unlink()
            
            logger.info(f"Áudio processado com sucesso: {path.name}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar áudio {path}: {str(e)}", exc_info=True)
            
            # Assegura limpeza em caso de erro
            try:
                if 'clean_path' in locals() and clean_path != path and clean_path.exists():
                    clean_path.unlink()
            except Exception:
                pass
                
            raise ValueError(f"Falha ao processar áudio: {str(e)}")
    
    async def _transcribe_audio(self, audio_path: Path) -> str:
        """
        Transcreve o áudio usando a API Whisper via Groq ou fallback para Hugging Face.
        Implementa um sistema de fallback em cascata.
        
        Args:
            audio_path: Caminho para o arquivo de áudio limpo
            
        Returns:
            Texto transcrito do áudio
        """
        logger.info(f"Iniciando transcrição de áudio: {audio_path.name}")
        
        # Estratégia principal: Groq Whisper API
        try:
            transcription = await self._transcribe_with_groq(audio_path)
            logger.info("Transcrição de áudio concluída com sucesso (Groq)")
            return transcription
        except Exception as e:
            logger.warning(f"Falha na transcrição com Groq: {str(e)}")
        
        # Fallback: Hugging Face Whisper
        try:
            transcription = await self._transcribe_with_huggingface(audio_path)
            logger.info("Transcrição de áudio concluída com sucesso (HuggingFace fallback)")
            return transcription
        except Exception as e:
            logger.error(f"Todas as tentativas de transcrição falharam: {str(e)}")
            raise ValueError("Não foi possível transcrever o áudio. Serviços indisponíveis.")
    
    async def _transcribe_with_groq(self, audio_path: Path) -> str:
        """
        Transcreve áudio usando a API Whisper da Groq.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            
        Returns:
            Texto transcrito
        """
        from src.services.api_service import GroqService
        
        groq_service = GroqService()
        
        try:
            # Abre o arquivo em modo binário
            with open(audio_path, "rb") as audio_file:
                # Prepara a requisição - usando apenas 'pt' em vez de 'pt-BR'
                # Extrai apenas o código de idioma principal (pt de pt-BR)
                language_code = self.whisper_language.split('-')[0] if '-' in self.whisper_language else self.whisper_language
                logger.info(f"Usando código de idioma {language_code} para Groq Whisper")
                
                response = await groq_service.transcribe_audio(
                    audio_file=audio_file,
                    model=self.whisper_model,
                    language=language_code,
                    response_format="json"
                )
            
            # Extrai o texto da resposta
            if isinstance(response, dict) and "text" in response:
                return response["text"]
            else:
                logger.warning(f"Formato inesperado na resposta Groq: {response}")
                return "Transcrição indisponível (erro de formato)"
                
        except Exception as e:
            logger.error(f"Erro na transcrição Groq: {str(e)}", exc_info=True)
            raise
    
    async def _transcribe_with_huggingface(self, audio_path: Path) -> str:
        """
        Transcreve áudio usando a API Whisper via Hugging Face (fallback).
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            
        Returns:
            Texto transcrito
        """
        from src.services.api_service import HuggingFaceService
        
        hf_service = HuggingFaceService()
        
        try:
            # Abre o arquivo em modo binário
            with open(audio_path, "rb") as audio_file:
                # Prepara a requisição com parâmetros para português do Brasil
                response = await hf_service.transcribe_audio(
                    audio_file=audio_file,
                    model=f"openai/{self.whisper_model}",
                    language=self.whisper_language.split('-')[0]  # Usa apenas "pt" para HF
                )
            
            # Extrai o texto da resposta
            if isinstance(response, dict) and "text" in response:
                return response["text"]
            else:
                logger.warning(f"Formato inesperado na resposta HF: {response}")
                return "Transcrição indisponível (erro de formato)"
                
        except Exception as e:
            logger.error(f"Erro na transcrição HuggingFace: {str(e)}", exc_info=True)
            raise
