"""Flask do Sabor & Clic — backend integrado ao MySQL (Parte 2)."""
import os
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

import pymysql
from flask import Flask, abort, redirect, render_template, request, session
from werkzeug.exceptions import HTTPException

from controllers.api import api


def create_app():
    app = Flask(__name__)
    # Em produção, configure SECRET_KEY para não perder sessões ao reiniciar.
    app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    app.json.ensure_ascii = False
    app.config.update(
        MAX_CONTENT_LENGTH=64 * 1024,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE') == '1',
    )
    app.register_blueprint(api)

    @app.before_request
    def proteger_requisicoes():
        # Bloqueia requisições de escrita de outros sites (CSRF básico por origem).
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            if request.headers.get('Sec-Fetch-Site') == 'cross-site':
                return {'erro': 'Origem não autorizada.'}, 403
            origem = request.headers.get('Origin')
            if origem and (urlsplit(origem).scheme, urlsplit(origem).netloc) != (request.scheme, request.host):
                return {'erro': 'Origem não autorizada.'}, 403

    @app.after_request
    def proteger_resposta(resposta):
        resposta.headers['X-Content-Type-Options'] = 'nosniff'
        resposta.headers['X-Frame-Options'] = 'DENY'
        resposta.headers['Referrer-Policy'] = 'same-origin'
        if request.path.startswith(('/api/', '/templates/')):
            resposta.headers['Cache-Control'] = 'no-store'
        return resposta

    @app.get('/favicon.ico')
    def favicon():
        return '', 204

    @app.get('/')
    def inicio():
        return redirect('/templates/index.html')

    @app.get('/templates/<pagina>')
    def pagina_existente(pagina):
        permitidas = {'index.html', 'CadastroCliente.html', 'CadastroCozinheiro.html',
                      'Cliente.html', 'ADM.html', 'Cozinheiro.html'}
        if pagina not in permitidas:
            abort(404)
        restritas = {'Cliente.html': 'cliente', 'ADM.html': 'administrador',
                     'Cozinheiro.html': 'cozinheiro'}
        if pagina in restritas:
            from models.loja import buscar_usuario
            usuario = buscar_usuario(usuario_id=session.get('uid')) if session.get('uid') else None
            if not usuario or not usuario['ativo'] or usuario['tipo_usuario'] != restritas[pagina]:
                return redirect('/templates/CadastroCozinheiro.html' if pagina == 'Cozinheiro.html'
                                else '/templates/CadastroCliente.html')
        return render_template(pagina)

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        return {'erro': erro.description}, erro.code

    @app.errorhandler(pymysql.err.OperationalError)
    @app.errorhandler(pymysql.err.ProgrammingError)
    def erro_mysql(erro):
        codigo = erro.args[0] if erro.args else None
        if codigo in (1205, 1213):
            return {'erro': 'Outra operação alterou esses dados. Atualize e tente novamente.'}, 409
        if codigo == 1644:  # SIGNAL disparado pelas triggers
            return {'erro': 'Regra de negócio recusou a operação (verifique o estoque).'}, 409

        app.logger.error('Falha no MySQL (código %s).', codigo)
        if codigo in (1044, 1045):
            return {'erro': 'O MySQL recusou o acesso. Confira o usuário e a senha da conexão.'}, 503
        if codigo in (1049, 1146):
            return {'erro': 'A base ainda não foi preparada. Siga a seção de MySQL do README.'}, 503
        if isinstance(erro, pymysql.err.ProgrammingError):
            return {'erro': 'Erro ao consultar o banco de dados.'}, 500
        return {'erro': 'Banco de dados indisponível. Inicie o MySQL e confira o endereço e a porta.'}, 503

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000)
