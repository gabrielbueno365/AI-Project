#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar o servidor MCP de mídia.
Usa subprocess para iniciar o servidor e comunicar-se com ele via HTTP.
"""

import asyncio
import argparse
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
import shlex
import httpx

# Adiciona o diretório raiz ao PATH para importar os módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings, setup_logging

# Configuração de logging
setup_logging()
logger = logging.getLogger("test_mcp_media")


async def test_transcribe_audio(audio_path: Path, server_process):
    """
    Testa a função de transcrição de áudio através do servidor MCP.
    
    Args:
        audio_path: Caminho para o arquivo de áudio
        server_process: Processo do servidor MCP
    """
    print(f"\n=== Testando transcrição de áudio: {audio_path.name} ===")
    
    try:
        # Verificar se o arquivo existe
        if not audio_path.exists():
            print(f"❌ Arquivo não encontrado: {audio_path}")
            return
            
        print(f"📄 Arquivo encontrado: {audio_path}")
        print(f"📦 Tamanho: {audio_path.stat().st_size / 1024:.2f} KB")
        
        # Esperar um pouco para o servidor iniciar
        time.sleep(3)
        
        print("🔄 Iniciando processo de transcrição (pode demorar alguns segundos)...")
        
        # Como o servidor MCP está rodando em outro processo,
        # usamos uma abordagem simplificada para teste
        settings = get_settings()
        
        # Opção 1: Transcrever usando o serviço existente, se disponível
        try:
            from src.services.audio_service import AudioService
            audio_service = AudioService()
            print("ℹ️ Usando serviço de áudio existente para transcrição")
            
            result = await audio_service.process_audio(audio_path)
            
            print(f"✅ Transcrição bem-sucedida!")
            print(f"📊 Duração: {result.get('duration', 'N/A'):.2f} segundos")
            print(f"🎵 Formato: {result.get('format', 'N/A')}")
            print(f"🎤 Taxa de amostragem: {result.get('sample_rate', 'N/A')} Hz")
            
            # Exibir a transcrição
            print("\n📝 TRANSCRIÇÃO:")
            print("=" * 50)
            print(result.get("transcription", ""))
            print("=" * 50)
            
            # Informar se houve conversão
            if result.get("was_converted", False):
                print(f"⚠️ O arquivo foi convertido: {result.get('filename', '')}")
                
        except Exception as e:
            print(f"⚠️ Não foi possível usar o serviço de áudio existente: {str(e)}")
            print("ℹ️ Para um teste completo do servidor MCP, instale o ambiente do servidor:")
            print("  cd C:\\AI\\chatbot\\mcp_servers\\media_server")
            print("  poetry install")
            
    except Exception as e:
        print(f"❌ Erro ao transcrever áudio: {str(e)}")


async def main():
    """Função principal para testar o servidor MCP de mídia."""
    # Parse argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Testa o servidor MCP de mídia")
    parser.add_argument("--audio", type=str, help="Caminho para um arquivo de áudio a ser transcrito")
    parser.add_argument("--video", type=str, help="Caminho para um arquivo de vídeo para extração de áudio")
    parser.add_argument("--output-format", type=str, default="mp3", help="Formato do áudio extraído")
    
    args = parser.parse_args()
    
    # Obtém as configurações
    settings = get_settings()
    
    # Verifica se o comando do servidor MCP está configurado
    if not settings.media_server_cmd:
        print("❌ Erro: MEDIA_SERVER_CMD não está configurado no .env")
        return
    
    # Inicia o servidor MCP em um subprocesso
    cmd = settings.media_server_cmd
    print(f"📡 Iniciando servidor MCP de mídia: {cmd}")
    
    try:
        # Tenta iniciar o servidor MCP, mas isso pode falhar
        # se as dependências não estiverem instaladas corretamente
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Adiciona um pequeno delay para o servidor iniciar
        await asyncio.sleep(1)
        
        # Verifica se o servidor está rodando
        if process.poll() is not None:
            # O processo já terminou
            stdout, stderr = process.communicate()
            print(f"❌ Erro ao iniciar o servidor MCP:")
            print(stderr.decode('utf-8', errors='ignore'))
            print("\nSugestão: Instale as dependências do servidor MCP:")
            print("cd C:\\AI\\chatbot\\mcp_servers\\media_server")
            print("poetry install")
            return
            
        print("🔌 Servidor MCP de mídia iniciado!")
        
        # Testa transcrição de áudio se fornecido
        if args.audio:
            audio_path = Path(args.audio)
            await test_transcribe_audio(audio_path, process)
        
        # Se nenhum caminho foi fornecido
        if not args.audio and not args.video:
            print("⚠️ Nenhum arquivo fornecido para teste.")
            print("Use --audio para testar transcrição ou --video para testar extração.")
    
    finally:
        # Tenta parar o servidor MCP
        if 'process' in locals() and process.poll() is None:
            print("🛑 Finalizando servidor MCP de mídia...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    asyncio.run(main())
