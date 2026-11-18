"""Integração REAL: use MYSQL_DATABASE=sabor_clic_test e SABOR_TESTES=1.
A base terminada em _test é recriada por teste; nunca use dados pessoais nela.
"""
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pymysql
import pytest
from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app
from models.banco import banco

ROOT = Path(__file__).resolve().parents[1]


from scripts.preparar_banco import executar_sql


@pytest.fixture
def db():
    assert os.getenv('SABOR_TESTES') == '1', 'Defina SABOR_TESTES=1 para autorizar a base descartável.'
    assert os.getenv('MYSQL_DATABASE', '').endswith('_test'), 'A base deve terminar em _test.'
    with banco() as cur:
        for arquivo in ('01_modelo_fisico.sql', '20_triggers.sql', '02_insercoes_basicas.sql'):
            executar_sql(cur, ROOT / 'database' / arquivo)
        cur.execute('UPDATE usuario SET senha_hash=%s', (generate_password_hash('TesteSeguro123'),))
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY='chave-apenas-para-testes')
    return app


def login(app, email='ana@email.com', senha='TesteSeguro123'):
    c = app.test_client()
    r = c.post('/api/login', json={'email': email, 'senha': senha})
    assert r.status_code == 200, r.json
    return c


def sql(comando, valores=()):
    with banco() as cur:
        cur.execute(comando, valores)
        if cur.description:
            return cur.fetchall()
        return cur.lastrowid


def pedido(c, quantidade=2):
    r = c.post('/api/pedidos', json={'itens': [{'id': 1, 'quantidade': quantidade}], 'endereco': 'Rua Teste 123'})
    assert r.status_code == 201, r.json
    return r.json


def test_fluxo_completo_persistencia_e_hash(db):
    cliente = db.test_client()
    assert cliente.get('/api/health').json == {'status': 'ok', 'banco': 'mysql'}
    r = cliente.post('/api/clientes', json={'nome': 'Nova Cliente', 'email': 'nova@example.com', 'senha': 'NovaSenha123', 'endereco': 'Rua Nova 123', 'tipo': 'administrador'})
    assert r.status_code == 201
    registro = sql('SELECT * FROM usuario WHERE id_usuario=%s', (r.json['id'],))[0]
    assert registro['tipo_usuario'] == 'cliente'
    assert check_password_hash(registro['senha_hash'], 'NovaSenha123')
    cliente = login(db, 'nova@example.com', 'NovaSenha123')
    p = pedido(cliente)
    assert p['total'] == 50 and p['status'] == 'Recebido'
    cozinha = login(db, 'marina@email.com')
    for status in ('Em Preparo', 'Pronto', 'Entregue'):
        r = cozinha.put(f"/api/pedidos/{p['id']}/status", json={'status': status, 'tempoEstimado': 20})
        assert r.status_code == 200, r.json
        assert r.json['status'] == status
    assert sql('SELECT quantidade_estoque FROM ingrediente WHERE id_ingrediente=1')[0]['quantidade_estoque'] == 98
    assert len(sql('SELECT * FROM baixa_estoque_pedido WHERE id_pedido=%s', (p['id'],))) == 1
    # Nova instância Flask / nova conexão: dados continuam no servidor MySQL.
    nova_app = create_app()
    novo_cliente = login(nova_app, 'nova@example.com', 'NovaSenha123')
    assert novo_cliente.get(f"/api/pedidos/{p['id']}").json['status'] == 'Entregue'


@pytest.mark.parametrize('perfil,email', [('cliente','ana@email.com'), ('cozinheiro','marina@email.com'), ('administrador','carlos@email.com')])
def test_matriz_rbac(db, perfil, email):
    c = login(db, email)
    operacoes = [('get','/api/cozinheiros',None, {'administrador'}),
                 ('post','/api/pratos',{}, {'administrador'}),
                 ('put','/api/pratos/1',{}, {'administrador'}),
                 ('delete','/api/pratos/999',None, {'administrador'}),
                 ('put','/api/cozinheiros/999/aprovar',None, {'administrador'}),
                 ('delete','/api/cozinheiros/999',None, {'administrador'}),
                 ('put','/api/me',{}, {'administrador'}),
                 ('post','/api/pedidos',{}, {'cliente'}),
                 ('put','/api/pedidos/1/status',{}, {'cozinheiro'})]
    for metodo, caminho, dados, permitidos in operacoes:
        r = getattr(c, metodo)(caminho, json=dados)
        if perfil not in permitidos:
            assert r.status_code == 403, (perfil, caminho, r.json)
        else:
            assert r.status_code == 200 if metodo == 'get' else r.status_code in (400,404), (perfil,caminho,r.status_code)
    for pagina, dono in [('ADM.html','administrador'),('Cliente.html','cliente'),('Cozinheiro.html','cozinheiro')]:
        assert c.get('/templates/'+pagina).status_code == (200 if dono == perfil else 302)


def test_sessao_cookies_idor_e_revogacao(db):
    c = login(db)
    assert len(c.get('/api/pedidos').json) == 1
    assert c.get('/api/pedidos/2').status_code == 404
    r = c.post('/api/login', json={'email':'ana@email.com','senha':'TesteSeguro123'})
    cookie = r.headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie
    outro = db.test_client()
    outro.set_cookie('session', 'adulterado')
    assert outro.get('/api/me').status_code == 401
    assert 'senha_hash' not in c.get('/api/me').text
    sql('UPDATE usuario SET ativo=0 WHERE id_usuario=1')
    assert c.get('/api/pedidos').status_code == 401
    sql('UPDATE usuario SET ativo=1 WHERE id_usuario=1')
    c = login(db)
    assert c.post('/api/logout').status_code == 200
    assert c.get('/api/me').status_code == 401


def test_cadastro_aprovacao_troca_e_recusa(db):
    c = db.test_client()
    dados = {'nome':'Chef Teste','email':'chef@example.com','turno':'Noite','especialidade':'Massas e molhos'}
    r = c.post('/api/cozinheiros', json=dados)
    assert r.status_code == 201
    cid = r.json['id']
    assert sql('SELECT ativo FROM usuario WHERE id_usuario=%s',(cid,))[0]['ativo'] == 0
    adm = login(db, 'carlos@email.com')
    r = adm.put(f'/api/cozinheiros/{cid}/aprovar')
    assert r.status_code == 200
    provisoria = r.json['senhaProvisoria']
    chef = login(db, dados['email'], provisoria)
    assert chef.get('/api/me').json['deveTrocarSenha']
    assert chef.get('/api/pedidos').status_code == 403
    assert chef.put('/api/senha', json={'senhaAtual': 'errada', 'novaSenha': 'Definitiva123'}).status_code == 403
    assert chef.put('/api/senha', json={'senhaAtual': provisoria, 'novaSenha': 'Definitiva123'}).status_code == 200
    assert chef.get('/api/pedidos').status_code == 200
    assert adm.put(f'/api/cozinheiros/{cid}/aprovar').status_code == 400
    assert adm.delete(f'/api/cozinheiros/{cid}').status_code == 400
    dados['email'] = 'recusar@example.com'
    cid2 = c.post('/api/cozinheiros', json=dados).json['id']
    assert adm.delete(f'/api/cozinheiros/{cid2}').status_code == 200
    assert not sql('SELECT 1 FROM usuario WHERE id_usuario=%s',(cid2,))


def test_crud_cardapio_e_preco_do_servidor(db):
    adm = login(db,'carlos@email.com')
    c = login(db)
    dados = {'nome':'Teste Prato','descricao':'Descrição teste','categoria':'Testes','preco':19.90,'ativo':True}
    r = adm.post('/api/pratos', json=dados)
    assert r.status_code == 201
    pid = r.json['id']
    assert adm.put(f'/api/pratos/{pid}',json=dados).status_code == 200
    dados['ativo'] = False
    assert adm.put(f'/api/pratos/{pid}',json=dados).status_code == 200
    assert pid not in [p['id'] for p in c.get('/api/pratos').json]
    assert adm.delete(f'/api/pratos/{pid}').status_code == 200
    assert adm.delete('/api/pratos/1').status_code == 409
    r = c.post('/api/pedidos',json={'idCliente':4,'total':0,'itens':[{'id':1,'quantidade':1,'preco':0}]})
    assert r.status_code == 201
    assert r.json['total'] == 25 and r.json['idCliente'] == 1
    dados['ativo'] = False
    dados['preco'] = 25
    assert adm.put('/api/pratos/1',json=dados).status_code == 200
    anterior = len(sql('SELECT * FROM pedido'))
    assert c.post('/api/pedidos', json={'itens':[{'id':1,'quantidade':1}]}).status_code == 400
    assert len(sql('SELECT * FROM pedido')) == anterior


def test_validacao_sql_injection_e_json(db):
    c = db.test_client()
    for email in ("' OR 1=1 --", "x'OR'1'='1@example.com"):
        assert c.post('/api/login',json={'email':email,'senha':'qualquer'}).status_code in (400,401)
    for corpo in ([], None, 'texto', {'nome':[]}, {'nome':'a'*101}):
        assert c.post('/api/clientes',json=corpo).status_code == 400
    assert c.post('/api/login',data='{"x":',content_type='application/json').status_code == 400
    assert c.post('/api/login',data='x'*70000,content_type='application/json').status_code == 413
    c = login(db)
    for itens in ([], [{}], [{'id':True,'quantidade':1}], [{'id':1,'quantidade':False}], [{'id':1,'quantidade':101}], [{'id':1,'quantidade':1.1}]):
        assert c.post('/api/pedidos',json={'itens':itens}).status_code == 400
    assert sql('SELECT COUNT(*) AS n FROM usuario')[0]['n'] == 4
    # Aspas são dados, não comandos SQL.
    r = c.post('/api/pedidos',json={'endereco':"Rua O'Connor; DROP TABLE usuario;",'itens':[{'id':1,'quantidade':1}]})
    assert r.status_code == 201
    assert 'DROP TABLE' in r.json['endereco']
    assert sql('SELECT COUNT(*) AS n FROM usuario')[0]['n'] == 4


def test_entradas_malformadas_nao_geram_500(db):
    adm = login(db,'carlos@email.com')
    assert adm.put('/api/me',json={'nome':'Administrador','email':'novo@example.com','senhaAtual':123}).status_code == 400
    chef = login(db,'marina@email.com')
    for status in ([], {}, True, None, 'inexistente'):
        assert chef.put('/api/pedidos/1/status',json={'status':status}).status_code == 400
    dados = {'nome':'Teste Prato','descricao':'Descrição teste','categoria':'Testes','preco':True}
    assert adm.post('/api/pratos',json=dados).status_code == 400


def test_perfil_admin_e_senha(db):
    adm = login(db,'carlos@email.com')
    assert adm.put('/api/me',json={'nome':'Admin Novo','email':'admin@example.com','senhaAtual':'TesteSeguro123'}).status_code == 200
    assert adm.get('/api/me').json['usuario']['email'] == 'admin@example.com'
    assert adm.put('/api/senha',json={'senhaAtual':'TesteSeguro123','novaSenha':'NovaSegura456'}).status_code == 200
    assert login(db,'admin@example.com','NovaSegura456').get('/api/me').status_code == 200
    assert db.test_client().post('/api/login',json={'email':'admin@example.com','senha':'TesteSeguro123'}).status_code == 401


def test_csrf(db):
    c = login(db)
    for cabecalhos in ({'Origin':'https://evil.example'}, {'Sec-Fetch-Site':'cross-site'}, {'Origin':'https://localhost'}):
        assert c.post('/api/logout',headers=cabecalhos).status_code == 403
    assert c.get('/api/me').status_code == 200
    assert c.post('/api/logout',headers={'Origin':'http://localhost'}).status_code == 200


def test_trigger_estoque_insuficiente_rollback(db):
    chef = login(db,'marina@email.com')
    sql('UPDATE ingrediente SET quantidade_estoque=0 WHERE id_ingrediente=3')
    antes = sql('SELECT * FROM ingrediente ORDER BY id_ingrediente')
    r = chef.put('/api/pedidos/1/status',json={'status':'Em Preparo','tempoEstimado':15})
    assert r.status_code == 409, r.json
    assert sql('SELECT * FROM ingrediente ORDER BY id_ingrediente') == antes
    assert sql('SELECT status FROM pedido WHERE id_pedido=1')[0]['status'] == 'aguardando'
    assert not sql('SELECT * FROM baixa_estoque_pedido')


def test_triggers_total_insert_update_delete_e_bloqueio(db):
    sql('UPDATE item_pedido SET quantidade=3 WHERE id_item=1')
    assert sql('SELECT valor_total FROM pedido WHERE id_pedido=1')[0]['valor_total'] == 75
    iid = sql('INSERT INTO item_pedido (id_pedido,id_prato,quantidade,preco_unitario) VALUES (1,2,1,40)')
    assert sql('SELECT valor_total FROM pedido WHERE id_pedido=1')[0]['valor_total'] == 115
    sql('DELETE FROM item_pedido WHERE id_item=%s',(iid,))
    assert sql('SELECT valor_total FROM pedido WHERE id_pedido=1')[0]['valor_total'] == 75
    sql("UPDATE pedido SET status='em_preparo' WHERE id_pedido=1")
    for comando in ('UPDATE item_pedido SET quantidade=4 WHERE id_item=1', 'DELETE FROM item_pedido WHERE id_item=1', 'INSERT INTO item_pedido (id_pedido,id_prato,quantidade,preco_unitario) VALUES (1,2,1,40)'):
        with pytest.raises(pymysql.MySQLError):
            sql(comando)
    sql("UPDATE pedido SET status='pronto' WHERE id_pedido=1")
    sql("UPDATE pedido SET status='em_preparo' WHERE id_pedido=1")
    assert sql('SELECT quantidade_estoque FROM ingrediente WHERE id_ingrediente=1')[0]['quantidade_estoque'] == 97


def test_locacao_conflitos_e_limites(db):
    comando = 'INSERT INTO locacao (id_cliente,id_bancada,data_inicio,data_fim,valor_total,status) VALUES (1,1,%s,%s,35,%s)'
    with pytest.raises(pymysql.MySQLError):
        sql(comando,('2026-11-20 10:00:00','2026-11-20 13:00:00','reservada'))
    lid = sql(comando,('2026-11-20 12:00:00','2026-11-20 13:00:00','reservada'))
    with pytest.raises(pymysql.MySQLError):
        sql("UPDATE locacao SET data_inicio='2026-11-20 11:00:00' WHERE id_locacao=%s",(lid,))
    sql(comando,('2026-11-20 10:00:00','2026-11-20 11:00:00','cancelada'))
    with pytest.raises(pymysql.MySQLError):
        sql(comando,('2026-11-21 12:00:00','2026-11-21 11:00:00','reservada'))


def test_relatorios_e_restricoes(db):
    with banco() as cur:
        executar_sql(cur, ROOT/'database/11_queries_relatorios.sql')
    for comando in ('UPDATE ingrediente SET quantidade_estoque=-1 WHERE id_ingrediente=1', 'UPDATE prato SET preco=-1 WHERE id_prato=1', 'UPDATE item_pedido SET quantidade=0 WHERE id_item=1', 'UPDATE pedido SET id_cliente=99999 WHERE id_pedido=1'):
        with pytest.raises(pymysql.MySQLError):
            sql(comando)


@pytest.mark.parametrize("rodada", range(5))
def test_concorrencia_estoque(db, rodada):
    sql('UPDATE ingrediente SET quantidade_estoque=2 WHERE id_ingrediente=1')
    p = pedido(login(db))
    barreira = Barrier(2)
    def iniciar(pid):
        c = login(db,'marina@email.com')
        barreira.wait(timeout=10)
        return c.put(f'/api/pedidos/{pid}/status',json={'status':'Em Preparo','tempoEstimado':15}).status_code
    with ThreadPoolExecutor(2) as pool:
        respostas = list(pool.map(iniciar, [1,p['id']]))
    assert sorted(respostas) == [200,409], respostas
    assert sql('SELECT quantidade_estoque FROM ingrediente WHERE id_ingrediente=1')[0]['quantidade_estoque'] == 0
    assert len(sql('SELECT * FROM baixa_estoque_pedido')) == 1

@pytest.mark.parametrize('metodo,caminho',[
    ('get','/api/me'),('put','/api/me'),('put','/api/senha'),
    ('get','/api/pratos'),('post','/api/pratos'),('put','/api/pratos/1'),('delete','/api/pratos/1'),
    ('get','/api/pedidos'),('get','/api/pedidos/1'),('post','/api/pedidos'),('put','/api/pedidos/1/status'),
    ('get','/api/cozinheiros'),('put','/api/cozinheiros/1/aprovar'),('delete','/api/cozinheiros/1')])
def test_anonimo_bloqueado(db,metodo,caminho):
    assert getattr(db.test_client(),metodo)(caminho,json={}).status_code == 401


def test_locacoes_simultaneas(db):
    barreira = Barrier(2)
    def reservar(_):
        try:
            with banco() as cur:
                # Os dois clientes começam vendo o mesmo estado anterior.
                cur.execute('SELECT COUNT(*) FROM locacao')
                barreira.wait(timeout=10)
                cur.execute("INSERT INTO locacao (id_cliente,id_bancada,data_inicio,data_fim,valor_total) VALUES (1,2,'2026-12-01 10:00:00','2026-12-01 11:00:00',45)")
            return 'gravada'
        except pymysql.MySQLError:
            return 'recusada'
    with ThreadPoolExecutor(2) as pool:
        respostas = list(pool.map(reservar,[1,2]))
    assert sorted(respostas) == ['gravada','recusada'], respostas
    assert len(sql('SELECT * FROM locacao WHERE id_bancada=2')) == 1


def test_pedido_endereco_compativel_js(db):
    c = login(db)
    assert c.post('/api/pedidos',json={'endereco':'x'*101,'itens':[{'id':1,'quantidade':1}]}).status_code == 400


def test_total_ao_transferir_item(db):
    sql('UPDATE item_pedido SET id_pedido=2 WHERE id_item=1')
    assert sql('SELECT valor_total FROM pedido WHERE id_pedido=1')[0]['valor_total'] == 0
    assert sql('SELECT valor_total FROM pedido WHERE id_pedido=2')[0]['valor_total'] == 90
