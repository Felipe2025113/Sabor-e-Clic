"""Rotas iniciais: leitura de pratos e criação/acompanhamento de pedidos."""
from flask import Blueprint, current_app, request
from werkzeug.exceptions import BadRequest

from models.memoria import atualizar_status, buscar_por_id, montar_pedido
from views.respostas import erro, sucesso

api = Blueprint('api', __name__, url_prefix='/api')


def dados():
    return current_app.config['DADOS']


def ler_json():
    if not request.is_json:
        raise BadRequest('Envie Content-Type: application/json.')
    entrada = request.get_json()
    if not isinstance(entrada, dict):
        raise BadRequest('Envie um objeto JSON.')
    return entrada


@api.get('/health')
def health():
    return sucesso({'status': 'ok', 'etapa': 'Parte 1', 'armazenamento': 'memoria'})


@api.get('/pratos')
def listar_pratos():
    return sucesso(dados()['pratos'])


@api.get('/pedidos')
def listar_pedidos():
    return sucesso(dados()['pedidos'])


@api.get('/pedidos/<int:pedido_id>')
def consultar_pedido(pedido_id):
    pedido = buscar_por_id(dados()['pedidos'], pedido_id)
    if pedido is None:
        return erro('Pedido não encontrado.', 404)
    return sucesso(pedido)


@api.post('/pedidos')
def criar_pedido():
    entrada = ler_json()
    try:
        pedido = montar_pedido(dados(), entrada)
    except ValueError as excecao:
        return erro(str(excecao))
    dados()['pedidos'].append(pedido)
    return sucesso(pedido, 201)


@api.patch('/pedidos/<int:pedido_id>/status')
def mudar_status(pedido_id):
    entrada = ler_json()
    pedido = buscar_por_id(dados()['pedidos'], pedido_id)
    if pedido is None:
        return erro('Pedido não encontrado.', 404)
    try:
        atualizar_status(pedido, entrada)
    except ValueError as excecao:
        return erro(str(excecao))
    return sucesso(pedido)
