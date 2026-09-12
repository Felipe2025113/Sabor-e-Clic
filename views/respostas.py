"""Apresentação das respostas da API em JSON."""
from flask import jsonify


def sucesso(dados, status=200):
    return jsonify({'sucesso': True, 'dados': dados}), status


def erro(mensagem, status=400):
    return jsonify({'sucesso': False, 'erro': mensagem}), status
