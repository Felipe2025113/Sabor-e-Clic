"""Casos mínimos de entradas malformadas e origem da requisição."""
from unittest.mock import patch
import socket
import pytest
from app import create_app
from werkzeug.security import generate_password_hash

@pytest.fixture
def cliente():
    app = create_app()
    app.config['TESTING'] = True
    c = app.test_client()
    with c.session_transaction() as sessao:
        sessao['uid'] = 1
    return c


def usuario(tipo):
    return {'id_usuario':1,'tipo_usuario':tipo,'ativo':True,'trocar_senha':False,
            'senha_hash':generate_password_hash('TesteSeguro123')}


def test_senha_atual_numerica(cliente):
    with patch('controllers.api.loja.buscar_usuario',return_value=usuario('administrador')):
        assert cliente.put('/api/me',json={'nome':'Admin Teste','email':'admin@example.com','senhaAtual':123}).status_code == 400

@pytest.mark.parametrize('status',[[],{}])
def test_status_tipo_invalido(cliente,status):
    with patch('controllers.api.loja.buscar_usuario',return_value=usuario('cozinheiro')):
        assert cliente.put('/api/pedidos/1/status',json={'status':status}).status_code == 400


def test_preco_booleano(cliente):
    with patch('controllers.api.loja.buscar_usuario',return_value=usuario('administrador')), patch('controllers.api.loja.salvar_prato',return_value={'id':1}):
        assert cliente.post('/api/pratos',json={'nome':'Prato Teste','descricao':'Descricao Teste','categoria':'Testes','preco':True}).status_code == 400


def test_origem_esquema_diferente(cliente):
    assert cliente.post('/api/logout',headers={'Origin':'https://localhost'}).status_code == 403

@pytest.mark.parametrize('codigo',[1205,1213])
def test_disputa_transacao_retorna_conflito(cliente,codigo):
    import pymysql
    with patch('controllers.api.loja.buscar_usuario',return_value=usuario('cozinheiro')), patch('controllers.api.loja.mudar_status',side_effect=pymysql.err.OperationalError(codigo,'conflito de teste')):
        r = cliente.put('/api/pedidos/1/status',json={'status':'Em Preparo','tempoEstimado':10})
        assert r.status_code == 409
        assert 'tente novamente' in r.json['erro']


def test_saude_e_login_indicam_mysql_fora_do_ar(cliente, monkeypatch):
    with socket.socket() as porta_sem_servidor:
        porta_sem_servidor.bind(('127.0.0.1', 0))
        monkeypatch.setenv('MYSQL_HOST', '127.0.0.1')
        monkeypatch.setenv('MYSQL_PORT', str(porta_sem_servidor.getsockname()[1]))
        saude = cliente.get('/api/health')
        login = cliente.post('/api/login', json={'email': 'teste@example.com', 'senha': 'TesteSeguro123'})
    assert saude.status_code == login.status_code == 503
    assert 'endereço e a porta' in saude.json['erro']
