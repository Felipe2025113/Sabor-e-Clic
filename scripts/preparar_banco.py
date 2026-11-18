"""Inicializa SOMENTE uma base vazia. Execute: python -m scripts.preparar_banco."""
import os
import re
from pathlib import Path
from models.banco import banco


def executar_sql(cursor, arquivo):
    nome = os.getenv('MYSQL_DATABASE', 'sabor_clic')
    if not re.fullmatch(r'[A-Za-z0-9_]+', nome):
        raise ValueError('Use apenas letras, números e sublinhado no nome do banco.')
    delimitador, partes = ';', []
    for linha in arquivo.read_text(encoding='utf-8').splitlines():
        if linha.strip().upper().startswith('DELIMITER '):
            delimitador = linha.split()[1]
            continue
        if not linha.strip() or linha.lstrip().startswith('--'):
            continue
        # Remove comentários SQL sem remover o texto dentro de aspas.
        linha = re.sub(r"'[^']*(?:''[^']*)*'|--[ \t].*$",
                       lambda m: '' if m.group().startswith('--') else m.group(), linha)
        partes.append(linha)
        if linha.rstrip().endswith(delimitador):
            comando = '\n'.join(partes).rstrip()[:-len(delimitador)]
            cursor.execute(comando.replace('sabor_clic', nome))
            partes = []


def main():
    nome = os.getenv('MYSQL_DATABASE', 'sabor_clic')
    with banco(sem_banco=True) as cursor:
        cursor.execute('SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema=%s', (nome,))
        if cursor.fetchone()['n']:
            raise SystemExit('A base já tem tabelas. Nada foi alterado. Use uma base nova.')
        pasta = Path(__file__).resolve().parents[1] / 'database'
        for arquivo in ('01_modelo_fisico.sql', '20_triggers.sql', '02_insercoes_basicas.sql'):
            executar_sql(cursor, pasta / arquivo)
    print('Banco inicializado. Agora execute: python -m scripts.criar_admin')


if __name__ == '__main__':
    main()
