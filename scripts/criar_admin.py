"""Execute: python -m scripts.criar_admin (após importar os arquivos SQL)."""
import argparse
from getpass import getpass

from werkzeug.security import generate_password_hash

from models.banco import banco
from controllers.api import texto, email_valido, senha_valida, ErroEntrada


def main():
    parser = argparse.ArgumentParser(description='Cria ou atualiza o administrador.')
    parser.add_argument('--stdin', action='store_true', help='Recebe nome, e-mail e senha por entrada padrão.')
    if parser.parse_args().stdin:
        nome, email, senha = input(), input(), input()
    else:
        nome = input('Nome do administrador: ')
        email = input('E-mail do administrador: ')
        senha = getpass('Senha (mínimo 10 caracteres, letras e números): ')
    nome, email = nome.strip(), email.strip().lower()
    try:
        texto({'nome': nome}, 'nome')
        email_valido({'email': email})
        senha_valida(senha)
    except ErroEntrada as erro:
        raise SystemExit(str(erro))
    with banco() as cursor:
        cursor.execute('SELECT id_usuario, tipo_usuario FROM usuario WHERE email=%s', (email,))
        existente = cursor.fetchone()
        if existente:
            if existente['tipo_usuario'] != 'administrador':
                raise SystemExit('Este e-mail já pertence a outro perfil.')
            cursor.execute('''UPDATE usuario SET nome=%s, senha_hash=%s, ativo=TRUE,
                              trocar_senha=FALSE WHERE id_usuario=%s''',
                           (nome, generate_password_hash(senha), existente['id_usuario']))
        else:
            cursor.execute('''INSERT INTO usuario (nome,email,senha_hash,tipo_usuario,
                              nivel_permissao,ativo) VALUES (%s,%s,%s,'administrador','total',TRUE)''',
                           (nome, email, generate_password_hash(senha)))
    print('Administrador configurado com sucesso.')


if __name__ == '__main__':
    main()
