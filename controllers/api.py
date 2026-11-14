"""Rotas HTTP. Acesso por perfil, validação de dados e respostas em JSON."""
import re
import secrets
from functools import wraps

import pymysql
from flask import Blueprint, g, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from models import loja
from models.banco import verificar_conexao
from views.respostas import mensagem as resposta_flash

api = Blueprint('api', __name__, url_prefix='/api')
EMAIL = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
SENHA = re.compile(r'^(?=.*[A-Za-z])(?=.*\d).{10,}$')
TURNOS = ('Manhã', 'Tarde', 'Noite')
ESPECIALIDADES = ('Churrasqueiro', 'Confeitaria', 'Frutos do Mar', 'Massas e molhos')


class ErroEntrada(ValueError):
    pass


def falha(mensagem, codigo=400):
    return resposta_flash(mensagem, codigo)


def json_entrada():
    if not request.is_json or not isinstance(request.get_json(silent=True), dict):
        raise ErroEntrada('Envie um objeto JSON válido (Content-Type: application/json).')
    return request.get_json()


def texto(dados, campo, min_chars=3, max_chars=100):
    valor = dados.get(campo)
    if not isinstance(valor, str) or not min_chars <= len(valor.strip()) <= max_chars:
        raise ErroEntrada(f'O campo {campo} deve ter de {min_chars} a {max_chars} caracteres.')
    return valor.strip()


def email_valido(dados):
    email = texto(dados, 'email', 3, 150).lower()
    if not EMAIL.fullmatch(email):
        raise ErroEntrada('Email inválido.')
    return email


def senha_valida(senha):
    if not isinstance(senha, str) or len(senha) > 128 or not SENHA.fullmatch(senha):
        raise ErroEntrada('A senha deve ter de 10 a 128 caracteres, incluindo letras e números.')
    return senha


def confere_senha(hash_armazenado, senha):
    if not isinstance(senha, str) or len(senha) > 128:
        return False
    try:
        return check_password_hash(hash_armazenado, senha)
    except ValueError:  # contas antigas usam texto fictício, não um hash válido
        return False


def dados_usuario(usuario):
    perfil = {'administrador': 'ADM', 'cliente': 'CLIENTE', 'cozinheiro': 'COZINHEIRO'}[usuario['tipo_usuario']]
    return {
        'id': usuario['id_usuario'], 'nome': usuario['nome'], 'email': usuario['email'],
        'perfil': perfil, 'nivelPermissao': usuario['nivel_permissao'],
        'endereco': usuario['endereco_entrega'], 'turno': usuario['turno'],
        'especialidade': usuario['especialidade'], 'ativo': bool(usuario['ativo']),
    }


def exigir(*perfis):
    """Verifica a sessão e o papel do usuário a CADA requisição protegida."""
    def decorar(funcao):
        @wraps(funcao)
        def protegida(*args, **kwargs):
            uid = session.get('uid')
            if not uid:
                return falha('Faça login para continuar.', 401)
            usuario = loja.buscar_usuario(usuario_id=uid)
            if not usuario or not usuario['ativo']:
                session.clear()
                return falha('Sessão inválida ou conta inativa.', 401)
            g.usuario = usuario
            if usuario['tipo_usuario'] not in perfis:
                return falha('Você não tem permissão para esta operação.', 403)
            if usuario['trocar_senha'] and request.endpoint not in ('api.alterar_senha', 'api.me'):
                return falha('Altere sua senha provisória antes de continuar.', 403)
            return funcao(*args, **kwargs)
        return protegida
    return decorar


@api.errorhandler(ErroEntrada)
def erro_de_entrada(e):
    return falha(str(e))


@api.errorhandler(LookupError)
def nao_encontrado(e):
    return falha(str(e), 404)


@api.errorhandler(ValueError)
def regra_invalida(e):
    return falha(str(e))


@api.errorhandler(pymysql.err.IntegrityError)
def conflito_dados(e):
    return falha('Registro duplicado ou referenciado por outro cadastro.', 409)


@api.errorhandler(pymysql.err.InternalError)
def erro_de_regra_mysql(e):
    return falha('Operação recusada pelo banco (estoque insuficiente ou regra de negócio).', 409)


@api.get('/health')
def health():
    verificar_conexao()
    return {'status': 'ok', 'banco': 'mysql'}


@api.post('/clientes')
def cadastrar_cliente():
    entrada = json_entrada()
    dados = {
        'tipo': 'cliente', 'nome': texto(entrada, 'nome'), 'email': email_valido(entrada),
        'senha_hash': generate_password_hash(senha_valida(entrada.get('senha'))),
        'endereco': texto(entrada, 'endereco'),
    }
    return resposta_flash('Cadastro realizado com sucesso.', 201, id=loja.criar_usuario(dados))


@api.post('/cozinheiros')
def cadastrar_cozinheiro():
    entrada = json_entrada()
    turno = entrada.get('turno')
    especialidade = entrada.get('especialidade')
    if turno not in TURNOS or especialidade not in ESPECIALIDADES:
        raise ErroEntrada('Escolha um turno e uma especialidade válidos.')
    dados = {
        'tipo': 'cozinheiro', 'nome': texto(entrada, 'nome'), 'email': email_valido(entrada),
        'senha_hash': generate_password_hash(secrets.token_urlsafe(24)),
        'turno': turno, 'especialidade': especialidade, 'ativo': False, 'trocar_senha': True,
    }
    return resposta_flash('Cadastro realizado com sucesso.', 201, id=loja.criar_usuario(dados))


@api.post('/login')
def login():
    entrada = json_entrada()
    email = email_valido(entrada)
    senha = entrada.get('senha')
    usuario = loja.buscar_usuario(email=email)
    if not isinstance(senha, str) or not usuario or not confere_senha(usuario['senha_hash'], senha):
        return falha('E-mail ou senha incorretos.', 401)
    if not usuario['ativo']:
        return falha('Cadastro ainda não aprovado.', 403)
    session.clear()
    session['uid'] = usuario['id_usuario']
    session.permanent = True
    return resposta_flash('Login realizado com sucesso.', usuario=dados_usuario(usuario),
                          deveTrocarSenha=bool(usuario['trocar_senha']))


@api.post('/logout')
def logout():
    session.clear()
    return resposta_flash('Sessão encerrada.')


@api.get('/me')
@exigir('cliente', 'cozinheiro', 'administrador')
def me():
    return {'usuario': dados_usuario(g.usuario), 'deveTrocarSenha': bool(g.usuario['trocar_senha'])}


@api.put('/senha')
@exigir('cliente', 'cozinheiro', 'administrador')
def alterar_senha():
    entrada = json_entrada()
    atual = entrada.get('senhaAtual')
    nova = senha_valida(entrada.get('novaSenha'))
    if not isinstance(atual, str) or not confere_senha(g.usuario['senha_hash'], atual):
        return falha('Senha atual incorreta.', 403)
    if atual == nova:
        raise ErroEntrada('A nova senha deve ser diferente da anterior.')
    loja.mudar_senha(g.usuario['id_usuario'], generate_password_hash(nova))
    return resposta_flash('Senha alterada com sucesso.')


@api.put('/me')
@exigir('administrador')
def atualizar_meus_dados():
    entrada = json_entrada()
    nome = texto(entrada, 'nome')
    email = email_valido(entrada)
    if not isinstance(entrada.get('senhaAtual'), str):
        raise ErroEntrada('Informe a senha atual como texto.')
    if not confere_senha(g.usuario['senha_hash'], entrada['senhaAtual']):
        return falha('Senha atual incorreta.', 403)
    loja.atualizar_administrador(g.usuario['id_usuario'], nome, email)
    return {'usuario': dados_usuario(loja.buscar_usuario(usuario_id=g.usuario['id_usuario']))}


@api.get('/pratos')
@exigir('cliente', 'cozinheiro', 'administrador')
def pratos():
    return loja.listar_pratos(somente_ativos=g.usuario['tipo_usuario'] != 'administrador')


def validar_prato(entrada):
    preco = entrada.get('preco')
    if isinstance(preco, bool):
        raise ErroEntrada('Informe um preço numérico válido.')
    try:
        preco = float(preco)
    except (TypeError, ValueError):
        raise ErroEntrada('Informe um preço numérico válido.')
    if not 0.01 <= preco <= 9999.99 or round(preco, 2) != preco:
        raise ErroEntrada('Preço deve estar entre R$ 0,01 e R$ 9.999,99 (duas casas decimais).')
    ativo = entrada.get('ativo', True)
    if not isinstance(ativo, bool):
        raise ErroEntrada('O campo ativo deve ser verdadeiro ou falso.')
    return {
        'nome': texto(entrada, 'nome'), 'descricao': texto(entrada, 'descricao'),
        'preco': preco, 'categoria': texto(entrada, 'categoria'), 'ativo': ativo,
    }


@api.post('/pratos')
@exigir('administrador')
def criar_prato():
    return loja.salvar_prato(validar_prato(json_entrada())), 201


@api.put('/pratos/<int:prato_id>')
@exigir('administrador')
def atualizar_prato(prato_id):
    return loja.salvar_prato(validar_prato(json_entrada()), prato_id)


@api.delete('/pratos/<int:prato_id>')
@exigir('administrador')
def remover_prato(prato_id):
    loja.remover_prato(prato_id)
    return {'mensagem': 'Prato removido.'}


@api.get('/cozinheiros')
@exigir('administrador')
def cozinheiros():
    return loja.listar_cozinheiros()


@api.put('/cozinheiros/<int:cozinheiro_id>/aprovar')
@exigir('administrador')
def aprovar_cozinheiro(cozinheiro_id):
    senha = secrets.token_urlsafe(14)
    loja.aprovar_cozinheiro(cozinheiro_id, generate_password_hash(senha))
    return {'senhaProvisoria': senha}


@api.delete('/cozinheiros/<int:cozinheiro_id>')
@exigir('administrador')
def recusar_cozinheiro(cozinheiro_id):
    loja.recusar_cozinheiro(cozinheiro_id)
    return {'mensagem': 'Cadastro recusado.'}


@api.get('/pedidos')
@exigir('cliente', 'cozinheiro', 'administrador')
def pedidos():
    uid = g.usuario['id_usuario'] if g.usuario['tipo_usuario'] == 'cliente' else None
    return loja.listar_pedidos(cliente_id=uid)


@api.get('/pedidos/<int:pedido_id>')
@exigir('cliente', 'cozinheiro', 'administrador')
def consultar_pedido(pedido_id):
    uid = g.usuario['id_usuario'] if g.usuario['tipo_usuario'] == 'cliente' else None
    pedidos = loja.listar_pedidos(cliente_id=uid, pedido_id=pedido_id)
    if not pedidos:
        raise LookupError('Pedido não encontrado.')
    return pedidos[0]


@api.post('/pedidos')
@exigir('cliente')
def criar_pedido():
    entrada = json_entrada()
    itens = entrada.get('itens')
    if not isinstance(itens, list) or not itens or len(itens) > 100:
        raise ErroEntrada('O pedido deve conter de 1 a 100 itens.')
    for item in itens:
        if (not isinstance(item, dict) or type(item.get('id')) is not int
                or item['id'] < 1 or type(item.get('quantidade')) is not int
                or item['quantidade'] < 1 or item['quantidade'] > 100):
            raise ErroEntrada('Cada item precisa de id positivo e quantidade inteira de 1 a 100.')
    endereco = entrada.get('endereco') or g.usuario['endereco_entrega']
    if not isinstance(endereco, str) or not 3 <= len(endereco.strip()) <= 100:
        raise ErroEntrada('Informe um endereço de entrega de 3 a 100 caracteres.')
    return loja.criar_pedido(g.usuario['id_usuario'], endereco.strip(), itens), 201


@api.put('/pedidos/<int:pedido_id>/status')
@exigir('cozinheiro')
def atualizar_status(pedido_id):
    entrada = json_entrada()
    status = entrada.get('status')
    if not isinstance(status, str) or status not in loja.STATUS_BANCO:
        raise ErroEntrada('Status do pedido inválido.')
    tempo = None
    if status == 'Em Preparo':
        tempo = entrada.get('tempoEstimado')
        if type(tempo) is not int or not 1 <= tempo <= 240:
            raise ErroEntrada('Tempo de preparo deve ser inteiro entre 1 e 240 minutos.')
    return loja.mudar_status(pedido_id, status, tempo)
