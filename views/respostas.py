"""Mensagens Flash do Flask entregues como JSON para o Fetch existente."""
from flask import flash, get_flashed_messages


def mensagem(texto, status=200, **dados):
    categoria = 'erro' if status >= 400 else 'sucesso'
    flash(texto, categoria)
    # Consome imediatamente: não acumula mensagens no cookie da sessão.
    avisos = get_flashed_messages(with_categories=True)
    chave = 'erro' if status >= 400 else 'mensagem'
    return {**dados, chave: avisos[-1][1]}, status
