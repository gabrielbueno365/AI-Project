#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar o processamento de áudio no contexto real.
"""

import os
import sys
import tempfile
from pathlib import Path
import asyncio
import argparse

# Adiciona o diretório pai ao sys.path para poder importar os módulos do chatbot
sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    print("=== Teste de Processamento de Áudio ===")
    
    # Tenta importar os módulos necessários
    print("Verificando importações...")
    
    try:
        import filetype
        print(f"✅ filetype importado (versão: {getattr(filetype, '__version__', 'desconhecida')})")
    except ImportError as e:
        print(f"❌ Erro ao importar filetype: {e}")
        return False
        
    try:
        import ffmpeg
        print(f"✅ ffmpeg-python importado (versão: {getattr(ffmpeg, '__version__', 'desconhecida')})")
    except ImportError as e:
        print(f"❌ Erro ao importar ffmpeg-python: {e}")
        return False
    
    # Tenta importar módulos do chatbot
    try:
        from src.utils.audio.helpers import verify_audio_format, convert_audio
        print("✅ Módulos de áudio do chatbot importados com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar módulos do chatbot: {e}")
        return False
    
    # Cria arquivos de teste
    temp_dir = Path(tempfile.gettempdir()) / "chatbot_audio_test"
    os.makedirs(temp_dir, exist_ok=True)
    
    test_wav = temp_dir / "test_audio.wav"
    test_mp3 = temp_dir / "test_audio.mp3"
    
    # Gera um arquivo WAV de teste usando ffmpeg
    print("\nCriando arquivo WAV de teste...")
    try:
        import subprocess
        result = subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
            "-t", "1", "-q:a", "9", "-acodec", "pcm_s16le", 
            str(test_wav)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Erro ao criar arquivo WAV de teste: {result.stderr}")
            return False
            
        if not test_wav.exists():
            print("❌ Arquivo WAV não foi criado")
            return False
            
        print(f"✅ Arquivo WAV criado: {test_wav}")
    except Exception as e:
        print(f"❌ Erro ao criar arquivo WAV: {str(e)}")
        return False
    
    # Testa a função verify_audio_format
    print("\nTestando verificação de formato...")
    try:
        is_valid, reason = await verify_audio_format(test_wav)
        print(f"Verificação: {is_valid}, Razão: {reason}")
        
        if not is_valid:
            print(f"❌ Verificação falhou: {reason}")
        else:
            print("✅ Verificação de formato OK")
    except Exception as e:
        print(f"❌ Erro ao verificar formato: {str(e)}")
        return False
    
    # Testa a função convert_audio
    print("\nTestando conversão para MP3...")
    try:
        await convert_audio(test_wav, test_mp3)
        
        if not test_mp3.exists():
            print("❌ Arquivo MP3 não foi criado")
            return False
            
        print(f"✅ Conversão para MP3 bem-sucedida: {test_mp3}")
    except Exception as e:
        print(f"❌ Erro na conversão para MP3: {str(e)}")
        return False
    
    # Limpa arquivos temporários
    try:
        if test_wav.exists():
            os.remove(test_wav)
        if test_mp3.exists():
            os.remove(test_mp3)
        print("\n✅ Limpeza de arquivos temporários concluída")
    except Exception as e:
        print(f"❌ Erro ao limpar arquivos: {str(e)}")
    
    print("\n=== Resultado Final ===")
    print("✅ Todos os testes de áudio foram bem-sucedidos!")
    print("O sistema está pronto para processar arquivos de áudio.")
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
