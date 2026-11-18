"""Configura a conexão com o MySQL instalado no computador e abre o site."""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import tempfile
from threading import Thread
import webbrowser

import pymysql
from dotenv import set_key
from werkzeug.serving import make_server

from app import create_app
from models.banco import ARQUIVO_ENV, carregar_env, motivo_conexao, verificar_conexao

VARIAVEIS = {
    'host': 'MYSQL_HOST',
    'port': 'MYSQL_PORT',
    'user': 'MYSQL_USER',
    'password': 'MYSQL_PASSWORD',
    'database': 'MYSQL_DATABASE',
}


def pedir_configuracao():
    print('Use os mesmos dados da conexão que funciona no MySQL Workbench.')
    host = input('Endereço do MySQL [127.0.0.1]: ').strip() or '127.0.0.1'
    porta = int(input('Porta do MySQL [3306]: ').strip() or '3306')
    if not 1 <= porta <= 65535:
        raise ValueError('Porta inválida')
    usuario = input('Usuário do MySQL [root]: ').strip() or 'root'
    base = input('Nome da base [sabor_clic]: ').strip() or 'sabor_clic'
    senha = getpass('Senha do MySQL (a digitação fica oculta): ')
    return {'host': host, 'port': porta, 'user': usuario, 'password': senha, 'database': base}


def salvar_configuracao(configuracao):
    variaveis = {nome: str(configuracao[campo]) for campo, nome in VARIAVEIS.items()}
    with tempfile.NamedTemporaryFile(dir=ARQUIVO_ENV.parent, prefix='.env-tmp-', delete=False) as arquivo:
        temporario = Path(arquivo.name)
    try:
        if ARQUIVO_ENV.exists():
            temporario.write_text(ARQUIVO_ENV.read_text(encoding='utf-8-sig'), encoding='utf-8')
        for nome, valor in variaveis.items():
            set_key(temporario, nome, json.dumps(valor, ensure_ascii=False),
                    quote_mode='never', encoding='utf-8')
        temporario.replace(ARQUIVO_ENV)
    finally:
        temporario.unlink(missing_ok=True)
    os.environ.update(variaveis)


def configurar():
    configuracao = pedir_configuracao()
    try:
        verificar_conexao(configuracao)
    except pymysql.MySQLError as erro:
        if not erro.args or erro.args[0] not in (1049, 1146):
            raise
        # O MySQL já autenticou o usuário. Guarda a conexão para a preparação da base.
        salvar_configuracao(configuracao)
        raise SystemExit(
            'A conexão foi salva no .env. Prepare uma base nova e vazia com '
            'python -m scripts.preparar_banco e abra o iniciador novamente.'
        ) from None
    salvar_configuracao(configuracao)


def abrir_site():
    with make_server('127.0.0.1', 0, create_app(), threaded=True) as servidor:
        endereco = f'http://127.0.0.1:{servidor.server_port}/'
        print(f'MySQL conectado. Sabor & Clic em {endereco}', flush=True)
        print('Mantenha esta janela aberta enquanto usa o site.', flush=True)
        Thread(target=webbrowser.open, args=(endereco,), daemon=True).start()
        servidor.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verificar', action='store_true', help='Só testa a conexão atual, sem alterar a configuração.')
    opcoes = parser.parse_args()
    carregar_env(override=True)
    try:
        verificar_conexao()
    except (pymysql.MySQLError, ValueError) as erro:
        if isinstance(erro, ValueError):
            mensagem = 'Confira a porta MYSQL_PORT no .env.'
        else:
            mensagem = motivo_conexao(erro)
        if opcoes.verificar:
            raise SystemExit(mensagem) from None
        print(mensagem)
        configurar()

    if opcoes.verificar:
        print('Conexão com o MySQL e a tabela de usuários verificada.')
        return
    abrir_site()


if __name__ == '__main__':
    try:
        main()
    except pymysql.MySQLError as erro:
        raise SystemExit(motivo_conexao(erro)) from None
    except ValueError:
        raise SystemExit('Informe uma porta numérica de 1 a 65535.') from None
    except (EOFError, KeyboardInterrupt):
        raise SystemExit('Iniciador encerrado.') from None
