"""Servidor inicial da Parte 1. Execute com: python app.py."""
from flask import Flask, abort, redirect, render_template, send_from_directory
from werkzeug.exceptions import HTTPException

from controllers.api import api
from models.memoria import criar_dados
from views.respostas import erro


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False
    app.config['MAX_CONTENT_LENGTH'] = 64 * 1024
    app.config['DADOS'] = criar_dados()
    app.register_blueprint(api)

    @app.get('/')
    def inicio():
        return redirect('/templates/index.html')

    @app.get('/templates/<pagina>')
    def pagina_existente(pagina):
        if pagina not in {'index.html', 'Cliente.html', 'ADM.html', 'Cozinheiro.html'}:
            abort(404)
        return render_template(pagina)

    @app.get('/templates/script.js')
    def script_existente():
        return send_from_directory(app.template_folder, 'script.js')

    @app.get('/templates/imagens/<path:nome>')
    def imagem_existente(nome):
        return send_from_directory(app.template_folder + '/imagens', nome)

    @app.get('/demo-api')
    def demonstracao():
        return render_template('demo_api.html')

    @app.errorhandler(HTTPException)
    def erro_http(excecao):
        return erro(excecao.description, excecao.code)

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000)
