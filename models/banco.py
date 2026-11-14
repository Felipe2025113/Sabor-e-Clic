"""Conexão simples com o MySQL; todas as consultas usam parâmetros (%s)."""
import os
from contextlib import contextmanager

import pymysql
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def banco(sem_banco=False):
    conexao = pymysql.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=None if sem_banco else os.getenv('MYSQL_DATABASE', 'sabor_clic'),
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


def verificar_conexao():
    """Confirma acesso à base e ao esquema, sem gravar dados."""
    with banco() as cursor:
        cursor.execute('SELECT 1 FROM usuario LIMIT 1')
