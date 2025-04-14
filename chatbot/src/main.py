#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Chatbot Inteligente - Fase 1
Aplicação de chatbot via terminal com integração a APIs LLM
"""

import asyncio
import os
import sys
import logging
from typing import Optional, Union, List
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.progress import Progress

# Adiciona o diretório principal ao path para importações corretas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.app import ChatbotApp
from src.utils.error_handlers import setup_error_handlers
from src.core.logging import setup_logging


# Adiciona logger específico para a UI
ui_logger = logging.getLogger("ui")

# Função para exibir mensagens apenas na UI do usuário (sem poluir o terminal com detalhes)
def log_to_user(message: str, level: str = "info"):
    """Registra uma mensagem que será visível apenas para o usuário"""
    extra = {"user_visible": True}
    if level.lower() == "info":
        ui_logger.info(message, extra=extra)
    elif level.lower() == "error":
        ui_logger.error(message, extra=extra)
    elif level.lower() == "warning":
        ui_logger.warning(message, extra=extra)
    else:
        ui_logger.debug(message, extra=extra)

# Console para interface do usuário
console = Console()


async def handle_file_input(console: Console) -> Optional[Path]:
    """Gerencia o input de arquivo do usuário."""
    console.print("\n[bold blue]Upload de Arquivo[/bold blue]")
    console.print("Formatos suportados: mp3, wav, ogg, flac, m4a")
    
    # Solicita o caminho do arquivo
    file_path_str = Prompt.ask("Digite o caminho completo do arquivo")
    
    # Remove aspas (simples ou duplas) caso existam
    file_path_str = file_path_str.strip()
    if (file_path_str.startswith('"') and file_path_str.endswith('"')) or \
       (file_path_str.startswith("'") and file_path_str.endswith("'")):
        file_path_str = file_path_str[1:-1]
    
    # Verifica se cancelou
    if not file_path_str.strip():
        console.print("[yellow]Upload cancelado[/yellow]")
        return None
    
    # Converte para objeto Path
    file_path = Path(file_path_str)
    
    # Verifica se existe
    if not file_path.exists():
        console.print(f"[red]Erro: Arquivo não encontrado: {file_path}[/red]")
        return None
    
    # Verifica o tamanho (limita a 50MB)
    max_size = 50 * 1024 * 1024
    if file_path.stat().st_size > max_size:
        console.print(f"[red]Erro: Arquivo muito grande: {file_path.stat().st_size / 1024 / 1024:.1f}MB (máximo: 50MB)[/red]")
        return None
    
    # Confirma o upload
    console.print(f"[green]Arquivo selecionado: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)[/green]")
    return file_path

async def main():
    """Função principal que executa o loop do chatbot"""
    # Configura tratamento de erros e finalização
    setup_error_handlers()
    
    # Configura o sistema de logging (se não foi configurado anteriormente)
    # Certifica que os logs não aparecerão para o usuário
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/chatbot.log"),
        console=True,
        json_format=False,
        user_visible=False  # Não mostrar logs técnicos para o usuário
    )
    
    # Registra que a aplicação foi iniciada (aparece apenas no arquivo de log)
    logging.info("Aplicação iniciada")
    
    # Inicializa o app principal
    app = ChatbotApp()
    
    # Verifica se o servidor MCP de mídia está configurado
    if app.media_client is not None:
        console.print("[green]Servidor MCP de mídia configurado e pronto para uso![/green]")
    else:
        console.print("[yellow]Aviso: Servidor MCP de mídia não configurado. Usando serviço legado.[/yellow]")
    
    # Mensagem de boas-vindas
    console.print(
        Panel.fit(
            Text("✨ Chatbot Inteligente - Fase 2 ✨", style="bold blue"),
            subtitle="Digite 'sair' para encerrar ou 'transcrever' para enviar um arquivo de áudio",
        )
    )
    
    # Loop principal da aplicação
    while True:
        # Coleta input do usuário
        user_input = Prompt.ask("\n[bold cyan]Você[/bold cyan] (digite 'transcrever' para enviar um arquivo de áudio)")
        
        # Verifica se deve encerrar
        if user_input.lower() in ('sair', 'exit', 'quit', 'q'):
            break
        
        # Verifica se o usuário quer enviar um arquivo
        file_path = None
        if user_input.lower() in ('transcrever', 'transcrição', 'audio', 'áudio'):
            file_path = await handle_file_input(console)
            if not file_path:
                continue  # Volta ao início se cancelou o upload
        
            # Pede instruções adicionais para o arquivo
            user_input = Prompt.ask("\n[bold cyan]Instruções adicionais[/bold cyan] (ou pressione Enter para apenas transcrever)")
            
            # Se o usuário não forneceu instruções ou pediu apenas para transcrever
            # definimos uma flag para pular o processamento com LLM
            skip_analysis = not user_input.strip() or user_input.lower() in ["transcreva", "transcrever", "transcrição"]
            
            if not user_input.strip():
                user_input = "Transcreva este áudio."
        
        try:
            # Processa a entrada do usuário
            with console.status("[bold green]Processando...[/bold green]"):
                # Passa a flag skip_analysis para controlar se deve usar LLM para análise
                response = await app.process_input(user_input, file_path, skip_analysis if 'skip_analysis' in locals() else False)
            
            # Exibe a resposta (formatada com markdown se necessário)
            console.print("\n[bold yellow]Bot[/bold yellow]")
            if "**" in response and "\n" in response:
                # Provavelmente contém markdown
                console.print(Markdown(response))
            else:
                # Texto simples
                console.print(response)
            
        except Exception as e:
            console.print(f"\n[bold red]Erro:[/bold red] {str(e)}")
    
    # Mensagem de encerramento
    console.print("\n[bold blue]Chatbot encerrado. Até a próxima![/bold blue]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[bold blue]Chatbot encerrado pelo usuário. Até a próxima![/bold blue]")
    except Exception as e:
        console.print(f"\n\n[bold red]Erro fatal: {str(e)}[/bold red]")
        sys.exit(1)
