#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para instalar e configurar o FFmpeg no sistema.
Suporta Windows, macOS e Linux.
"""

import os
import sys
import platform
import subprocess
import zipfile
import tarfile
import shutil
from pathlib import Path
import urllib.request
import tempfile

def is_ffmpeg_installed():
    """Verifica se o FFmpeg já está instalado no sistema."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception:
        return False

def download_file(url, destination):
    """Baixa um arquivo da web para o destino especificado."""
    print(f"Baixando {url}...")
    with urllib.request.urlopen(url) as response, open(destination, 'wb') as out_file:
        total_size = int(response.info().get('Content-Length', 0))
        downloaded = 0
        chunk_size = 8192
        
        while True:
            buffer = response.read(chunk_size)
            if not buffer:
                break
                
            downloaded += len(buffer)
            out_file.write(buffer)
            
            # Exibe progresso do download
            if total_size > 0:
                percent = int(100 * downloaded / total_size)
                sys.stdout.write(f"\rProgresso: {percent}% ({downloaded} / {total_size} bytes)")
                sys.stdout.flush()
    
    print("\nDownload concluído!")

def install_ffmpeg_windows():
    """Instala o FFmpeg no Windows."""
    # URL para download do FFmpeg para Windows (escolha a versão essentials)
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    # Cria diretório temporário para download
    temp_dir = Path(tempfile.gettempdir()) / "ffmpeg_install"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Baixa o arquivo
    zip_path = temp_dir / "ffmpeg.zip"
    download_file(ffmpeg_url, zip_path)
    
    # Extrai o arquivo
    print("Extraindo arquivos...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Encontra o diretório bin dentro da extração
    extracted_dir = next(d for d in temp_dir.glob("*") if d.is_dir() and "ffmpeg" in d.name.lower())
    bin_dir = extracted_dir / "bin"
    
    # Define o diretório de destino
    install_dir = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "FFmpeg"
    
    # Cria o diretório de instalação
    os.makedirs(install_dir, exist_ok=True)
    
    # Copia os arquivos binários
    print(f"Instalando FFmpeg em {install_dir}...")
    for file in bin_dir.glob("*"):
        shutil.copy2(file, install_dir)
    
    # Adiciona ao PATH
    if str(install_dir) not in os.environ.get("PATH", ""):
        print("Adicionando FFmpeg ao PATH do sistema...")
        # Utilizamos o PowerShell para adicionar ao PATH do sistema
        try:
            # Primeiro adiciona ao PATH da sessão atual
            os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + str(install_dir)
            
            # Em seguida, adiciona permanentemente usando PowerShell
            cmd = f'[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;{install_dir}", [EnvironmentVariableTarget]::User)'
            subprocess.run(["powershell", "-Command", cmd], check=True)
            
            # Verifica se a adição funcionou
            try:
                result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    print("FFmpeg verificado e funcionando corretamente!")
                else:
                    print("Adição ao PATH completa, mas FFmpeg não está respondendo corretamente.")
            except Exception:
                print("FFmpeg adicionado ao PATH, mas pode ser necessário reiniciar o terminal.")
                
            print("FFmpeg adicionado ao PATH com sucesso!")
            print("Você pode precisar reiniciar o terminal ou o sistema para que as alterações tenham efeito.")
        except subprocess.CalledProcessError:
            print("Falha ao adicionar FFmpeg ao PATH automaticamente.")
            print(f"Por favor, adicione manualmente o diretório '{install_dir}' à variável PATH do sistema.")
    
    # Limpeza
    print("Limpando arquivos temporários...")
    shutil.rmtree(temp_dir)
    
    print("Instalação do FFmpeg concluída com sucesso!")
    print(f"FFmpeg instalado em: {install_dir}")

def install_ffmpeg_macos():
    """Instala o FFmpeg no macOS usando Homebrew."""
    print("Verificando se o Homebrew está instalado...")
    try:
        subprocess.run(["brew", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Homebrew não encontrado. Instalando Homebrew...")
        try:
            install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            subprocess.run(install_cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            print("Falha ao instalar o Homebrew. Por favor, instale manualmente: https://brew.sh")
            return False
    
    print("Instalando FFmpeg via Homebrew...")
    try:
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
        print("FFmpeg instalado com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("Falha ao instalar o FFmpeg. Por favor, tente instalar manualmente: brew install ffmpeg")
        return False

def install_ffmpeg_linux():
    """Instala o FFmpeg no Linux usando o gerenciador de pacotes."""
    # Detecta o gerenciador de pacotes
    package_managers = {
        "apt": ["apt-get", "update", "&&", "apt-get", "install", "-y", "ffmpeg"],
        "dnf": ["dnf", "install", "-y", "ffmpeg"],
        "yum": ["yum", "install", "-y", "ffmpeg"],
        "pacman": ["pacman", "-Sy", "--noconfirm", "ffmpeg"],
        "zypper": ["zypper", "install", "-y", "ffmpeg"],
    }
    
    for pm, cmd in package_managers.items():
        try:
            if shutil.which(pm):
                print(f"Detectado gerenciador de pacotes: {pm}")
                print(f"Instalando FFmpeg via {pm}...")
                
                if pm == "apt":
                    subprocess.run(["sudo", "apt-get", "update"], check=True)
                    subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=True)
                elif pm == "dnf":
                    subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"], check=True)
                elif pm == "yum":
                    subprocess.run(["sudo", "yum", "install", "-y", "ffmpeg"], check=True)
                elif pm == "pacman":
                    subprocess.run(["sudo", "pacman", "-Sy", "--noconfirm", "ffmpeg"], check=True)
                elif pm == "zypper":
                    subprocess.run(["sudo", "zypper", "install", "-y", "ffmpeg"], check=True)
                
                print("FFmpeg instalado com sucesso!")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("Não foi possível instalar FFmpeg automaticamente.")
    print("Por favor, instale FFmpeg manualmente de acordo com sua distribuição Linux.")
    return False

def main():
    print("==== Instalador do FFmpeg ====")
    
    # Verifica se FFmpeg já está instalado
    if is_ffmpeg_installed():
        print("FFmpeg já está instalado no sistema!")
        
        # Mostra onde o FFmpeg está instalado
        ffmpeg_path = shutil.which("ffmpeg")
        print(f"Localização do FFmpeg: {ffmpeg_path}")
        
        # Verifica a versão
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            version_line = result.stdout.splitlines()[0]
            print(f"Versão: {version_line}")
        except Exception:
            pass
            
        return
    
    # Detecta o sistema operacional
    system = platform.system().lower()
    
    # Instala FFmpeg de acordo com o sistema
    if system == "windows":
        install_ffmpeg_windows()
    elif system == "darwin":  # macOS
        install_ffmpeg_macos()
    elif system == "linux":
        install_ffmpeg_linux()
    else:
        print(f"Sistema operacional não suportado: {system}")
        print("Por favor, instale o FFmpeg manualmente.")

if __name__ == "__main__":
    main()
