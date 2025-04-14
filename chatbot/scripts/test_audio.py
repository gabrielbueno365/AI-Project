#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script simples para testar a transcrição de áudio usando o serviço existente.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Adiciona o diretório raiz ao PATH para importar os módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    # Parse argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Testa o processamento de áudio")
    parser.add_argument("--audio", type=str, required=True, help="Caminho para um arquivo de áudio")
    args = parser.parse_args()
    
    # Importar o serviço de áudio existente
    from src.services.audio_service import AudioService
    
    # Caminho do áudio
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"Erro: Arquivo não encontrado: {audio_path}")
        return
        
    print(f"Processando áudio: {audio_path}")
    print(f"Tamanho: {audio_path.stat().st_size / 1024:.2f} KB")
    
    # Criar o serviço de áudio
    audio_service = AudioService()
    
    # Processar o áudio
    try:
        result = await audio_service.process_audio(audio_path)
        
        # Exibir resultado
        print("\n=== Resultado da Transcrição ===")
        print(f"Duração: {result.get('duration', 'N/A'):.2f} segundos")
        print(f"Formato: {result.get('format', 'N/A')}")
        print(f"Taxa de amostragem: {result.get('sample_rate', 'N/A')} Hz")
        
        print("\nTRANSCRIÇÃO:")
        print("=" * 50)
        print(result.get("transcription", ""))
        print("=" * 50)
        
    except Exception as e:
        print(f"Erro ao processar áudio: {e}")

if __name__ == "__main__":
    asyncio.run(main())
