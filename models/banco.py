"""Conexão simples com o MySQL; todas as consultas usam parâmetros (%s)."""
import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from dotenv import load_dotenv

ARQUIVO_ENV = Path(__file__).resolve().parents[1] / '.env'


def carregar_env(override=False):
    load_dotenv(ARQUIVO_ENV, encoding='utf-8-sig', interpolate=False, override=override)


carregar_env()


def configuracao_mysql():
    return {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'sabor_clic'),
    }


@contextmanager
def banco(sem_banco=False, configuracao=None):
    dados = configuracao_mysql() if configuracao is None else configuracao.copy()
    if sem_banco:
        dados['database'] = None
    conexao = pymysql.connect(
        **dados,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
        read_timeout=15,
        write_timeout=15,
    )
    try:
        with conexao.cursor() as cursor:
            yield cursor
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def verificar_conexao(configuracao=None):
    """Confirma acesso à base e ao esquema, sem gravar dados."""
    with banco(configuracao=configuracao) as cursor:
        cursor.execute('SELECT 1 FROM usuario LIMIT 1')


def motivo_conexao(erro):
    codigo = erro.args[0] if erro.args else None
    if codigo == 1044:
        return 'O usuário do MySQL não tem permissão para acessar a base configurada.'
    if codigo == 1045:
        return 'O MySQL recusou o acesso. Use o usuário e a senha do servidor MySQL.'
    if codigo in (1049, 1146):
        return 'A base do Sabor & Clic ainda precisa ser preparada. Veja o README.'
    return 'Banco de dados indisponível. Inicie o MySQL e confira o endereço e a porta.'
