#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Servidor MCP de teste para verificar a configuração do ambiente.
"""

from mcp.server.fastmcp import FastMCP, Context

# Cria uma instância do servidor
mcp = FastMCP(name="Test Server")

@mcp.tool()
async def hello_world(name: str, ctx: Context) -> str:
    """Retorna uma mensagem de saudação."""
    ctx.info(f"Recebida chamada para hello_world com nome: {name}")
    return f"Olá, {name}! Seu primeiro servidor MCP está funcionando!"

@mcp.tool()
async def add_numbers(a: int, b: int, ctx: Context) -> int:
    """Soma dois números."""
    ctx.info(f"Recebida chamada para add_numbers com a={a}, b={b}")
    return a + b

@mcp.tool()
async def echo_message(message: str, ctx: Context) -> str:
    """Retorna a mensagem recebida."""
    ctx.info(f"Recebida chamada para echo_message: {message}")
    return message

if __name__ == "__main__":
    # Inicia o servidor via stdio
    mcp.run()
