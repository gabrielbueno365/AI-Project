#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de diagnóstico para identificar problemas no processamento de áudio.
Verifica instalação do FFmpeg, permissões e dependências necessárias.
"""

import sys
import os
import platform
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def check_python_version():
    """Verifica a versão do Python."""
    print("Verificando versão do Python...")
    
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"Python: {python_version}")
    
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 11):
        print("❌ Python 3.11 ou superior é recomendado")
        return False
    else:
        print("✅ Versão do Python OK")
        return True

def check_ffmpeg():
    """Verifica se o FFmpeg está instalado e funcionando."""
    print("\nVerificando FFmpeg...")
    
    try:
        # Tenta executar o comando ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        if result.returncode == 0:
            # Extrai e exibe a versão
            version_line = result.stdout.splitlines()[0]
            ffmpeg_path = shutil.which("ffmpeg")
            print(f"✅ FFmpeg instalado: {version_line}")
            print(f"   Localização: {ffmpeg_path}")
            return True
        else:
            print("❌ FFmpeg não está funcionando corretamente")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg não encontrado. Certifique-se de que está instalado e no PATH")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar FFmpeg: {str(e)}")
        return False

def check_temp_directory():
    """Verifica se o diretório temporário está acessível e com permissões corretas."""
    print("\nVerificando diretório temporário...")
    
    temp_dir = Path(tempfile.gettempdir())
    chatbot_temp = temp_dir / "chatbot_audio"
    
    print(f"Diretório temporário do sistema: {temp_dir}")
    print(f"Diretório temporário do chatbot: {chatbot_temp}")
    
    # Verifica se o diretório base existe
    if not temp_dir.exists():
        print(f"❌ Diretório temporário do sistema não existe: {temp_dir}")
        return False
    
    # Verifica permissões
    try:
        # Tenta criar o diretório do chatbot
        os.makedirs(chatbot_temp, exist_ok=True)
        print(f"✅ Diretório do chatbot criado/acessado com sucesso")
        
        # Tenta criar um arquivo temporário
        test_file = chatbot_temp / "test_write.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        
        print(f"✅ Arquivo de teste criado com sucesso: {test_file}")
        
        # Lê o arquivo
        with open(test_file, "r") as f:
            content = f.read()
            if content == "test":
                print(f"✅ Leitura do arquivo de teste bem-sucedida")
            else:
                print(f"❌ Conteúdo do arquivo de teste não corresponde")
        
        # Remove o arquivo
        os.remove(test_file)
        print(f"✅ Arquivo de teste removido com sucesso")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao acessar ou modificar o diretório temporário: {str(e)}")
        return False

def check_file_conversion():
    """Testa a conversão básica de um arquivo de áudio."""
    print("\nTestando conversão básica de áudio...")
    
    # Cria diretório temporário para o teste
    temp_dir = Path(tempfile.gettempdir()) / "chatbot_audio_test"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Cria um arquivo de áudio de teste (silêncio de 1 segundo)
    test_wav = temp_dir / "test.wav"
    
    try:
        # Cria um arquivo WAV com 1 segundo de silêncio
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
            "-t", "1", "-q:a", "9", "-acodec", "pcm_s16le", 
            str(test_wav)
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Arquivo de teste WAV criado: {test_wav}")
        
        # Tenta converter para MP3
        test_mp3 = temp_dir / "test.mp3"
        subprocess.run([
            "ffmpeg", "-i", str(test_wav), "-codec:a", "libmp3lame", 
            "-qscale:a", "2", str(test_mp3)
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Conversão para MP3 bem-sucedida: {test_mp3}")
        
        # Limpa arquivos temporários
        os.remove(test_wav)
        os.remove(test_mp3)
        os.rmdir(temp_dir)
        
        print("✅ Teste de conversão completo e bem-sucedido")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar FFmpeg: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste de conversão: {str(e)}")
        return False
    finally:
        # Garante limpeza mesmo em caso de erro
        try:
            if test_wav.exists():
                os.remove(test_wav)
            if 'test_mp3' in locals() and test_mp3.exists():
                os.remove(test_mp3)
            if temp_dir.exists():
                os.rmdir(temp_dir)
        except:
            pass

def check_dependencies():
    """Verifica as dependências Python necessárias."""
    print("\nVerificando dependências Python...")
    print(f"Executando com Python: {sys.executable}")
    
    dependencies = [
        "filetype",
        "ffmpeg-python"
    ]
    
    all_ok = True
    
    for dep in dependencies:
        try:
            # Tenta importar e mostrar a versão
            module_name = dep.replace("-", "_")
            module = __import__(module_name)
            version = getattr(module, "__version__", "versão desconhecida")
            print(f"✅ {dep} instalado (v{version})")
        except ImportError as e:
            print(f"❌ {dep} não encontrado: {e}")
            # Tenta obter mais informações sobre o erro
            print(f"   Tentando localizar em: {', '.join(sys.path[:3])}...")
            all_ok = False
    
    # Verificando se estamos em um ambiente virtual
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        print(f"Ambiente virtual ativo: {venv}")
    else:
        print("Aviso: Nenhum ambiente virtual detectado")
    
    return all_ok

def main():
    """Função principal que executa todas as verificações."""
    print("=== Diagnóstico de Processamento de Áudio ===")
    print(f"Sistema: {platform.system()} {platform.release()}")
    print(f"Arquitetura: {platform.machine()}")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
    # Executa as verificações
    python_ok = check_python_version()
    ffmpeg_ok = check_ffmpeg()
    temp_ok = check_temp_directory()
    deps_ok = check_dependencies()
    
    # Só testa a conversão se o FFmpeg estiver ok
    conv_ok = check_file_conversion() if ffmpeg_ok else False
    
    # Resumo
    print("\n=== Resumo do Diagnóstico ===")
    print(f"Python: {'✅ OK' if python_ok else '❌ Problema'}")
    print(f"FFmpeg: {'✅ OK' if ffmpeg_ok else '❌ Problema'}")
    print(f"Diretório Temporário: {'✅ OK' if temp_ok else '❌ Problema'}")
    print(f"Dependências Python: {'✅ OK' if deps_ok else '❌ Problema'}")
    print(f"Teste de Conversão: {'✅ OK' if conv_ok else '❌ Problema'}")
    
    # Conclusão e próximos passos
    if all([python_ok, ffmpeg_ok, temp_ok, deps_ok, conv_ok]):
        print("\n✅ Todos os componentes estão funcionando corretamente!")
        print("O sistema deve ser capaz de processar áudio sem problemas.")
    else:
        print("\n❌ Foram detectados problemas no diagnóstico.")
        print("\nRecomendações:")
        
        if not ffmpeg_ok:
            print("- Instale o FFmpeg utilizando o script: python scripts/install_ffmpeg.py")
            print("  Ou baixe manualmente de: https://ffmpeg.org/download.html")
        
        if not deps_ok:
            print("- Instale as dependências Python: poetry install")
            print("  Ou manualmente: pip install ffmpeg-python filetype")
        
        if not temp_ok:
            print("- Verifique as permissões do diretório temporário")
            print(f"  Diretório temp: {tempfile.gettempdir()}")
        
        if not conv_ok and ffmpeg_ok:
            print("- Houve um problema na conversão de áudio")
            print("  Verifique se há restrições de segurança ou permissão no sistema")

if __name__ == "__main__":
    main()
