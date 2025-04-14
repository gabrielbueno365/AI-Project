#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para testar a configuração MCP.
Inicia um servidor MCP de teste e se comunica com ele.
"""

import asyncio
import sys
import subprocess
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    # Comando para iniciar o servidor
    cmd = [sys.executable, "mcp_servers/test_server/src/server.py"]
    
    # Configurar parâmetros do servidor
    server_params = StdioServerParameters(command=cmd[0], args=cmd[1:])
    
    print("Iniciando servidor MCP...")
    
    # Conectar ao servidor
    try:
        async with stdio_client(server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                # Inicializar a sessão
                await session.initialize()
                
                print("Servidor MCP iniciado!")
                
                # Chamar o tool hello_world
                result = await session.call_tool("hello_world", {"name": "Desenvolvedor"})
                
                # Extrair e mostrar o resultado
                if result.content and isinstance(result.content[0], types.TextContent):
                    print(f"Resposta do servidor: {result.content[0].text}")
                else:
                    print("Formato de resposta inesperado.")
    except Exception as e:
        print(f"Erro ao conectar com o servidor MCP: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
