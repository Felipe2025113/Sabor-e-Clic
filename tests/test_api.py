"""Testes rápidos do contrato Flask (sem precisar de MySQL real)."""
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash
from app import create_app


class TesteAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.usuario = {
            'id_usuario': 10, 'nome': 'Cliente Teste', 'email': 'teste@email.com',
            'senha_hash': generate_password_hash('MinhaSenha123'),
            'tipo_usuario': 'cliente', 'nivel_permissao': None,
            'endereco_entrega': 'Rua Exemplo 123', 'turno': None,
            'especialidade': None, 'ativo': 1, 'trocar_senha': 0,
        }

    def entrar_com_sessao(self):
        with self.client.session_transaction() as sessao:
            sessao['uid'] = self.usuario['id_usuario']

    def test_saude_publica_e_paginas_login(self):
        with patch('controllers.api.verificar_conexao') as verificar:
            self.assertEqual(self.client.get('/api/health').status_code, 200)
            verificar.assert_called_once()
        for pagina in ['index.html', 'CadastroCliente.html', 'CadastroCozinheiro.html']:
            self.assertEqual(self.client.get('/templates/' + pagina).status_code, 200)
        self.assertEqual(self.client.get('/templates/ADM.html').status_code, 302)

    def test_rotas_restritas_sem_sessao(self):
        self.assertEqual(self.client.get('/api/pedidos').status_code, 401)
        self.assertEqual(self.client.post('/api/pratos', json={}).status_code, 401)
        self.assertEqual(self.client.get('/api/cozinheiros').status_code, 401)

    def test_cadastro_cliente_valida_e_hash_senha(self):
        corpo = {'nome': 'Ana Silva', 'email': 'ana@email.com',
                 'endereco': 'Rua Central 123', 'senha': 'SenhaSegura123'}
        with patch('controllers.api.loja.criar_usuario', return_value=15) as criar:
            resposta = self.client.post('/api/clientes', json=corpo)
            self.assertEqual(resposta.status_code, 201)
            dados_enviados = criar.call_args.args[0]
            self.assertNotEqual(dados_enviados['senha_hash'], corpo['senha'])
            self.assertTrue(dados_enviados['senha_hash'].startswith('scrypt:') or
                            dados_enviados['senha_hash'].startswith('pbkdf2:'))
        self.assertEqual(self.client.post('/api/clientes', json={**corpo, 'senha': '123'}).status_code, 400)
        self.assertEqual(self.client.post('/api/clientes', json={**corpo, 'email': 'invalido'}).status_code, 400)

    def test_login_sessao_e_permissao(self):
        with patch('controllers.api.loja.buscar_usuario', return_value=self.usuario):
            login = self.client.post('/api/login', json={
                'email': self.usuario['email'], 'senha': 'MinhaSenha123'})
            self.assertEqual(login.status_code, 200)
            self.assertIn('session=', login.headers.get('Set-Cookie', ''))
            eu = self.client.get('/api/me')
            self.assertEqual(eu.status_code, 200)
            self.assertEqual(eu.json['usuario']['perfil'], 'CLIENTE')
            self.assertEqual(self.client.post('/api/pratos', json={}).status_code, 403)
        logout = self.client.post('/api/logout')
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get('/api/me').status_code, 401)

    def test_cliente_so_ve_pedidos_proprios(self):
        self.entrar_com_sessao()
        with patch('controllers.api.loja.buscar_usuario', return_value=self.usuario), \
             patch('controllers.api.loja.listar_pedidos', return_value=[]) as listar:
            self.assertEqual(self.client.get('/api/pedidos').status_code, 200)
            listar.assert_called_once_with(cliente_id=10)
            self.assertEqual(self.client.get('/api/pedidos/999').status_code, 404)

    def test_pedido_validado_antes_de_gravar(self):
        self.entrar_com_sessao()
        with patch('controllers.api.loja.buscar_usuario', return_value=self.usuario), \
             patch('controllers.api.loja.criar_pedido') as criar:
            for itens in ([], [{'id': 1, 'quantidade': -1}], [{'id': 1, 'quantidade': True}]):
                self.assertEqual(self.client.post('/api/pedidos', json={
                    'endereco': 'Rua Teste 123', 'itens': itens}).status_code, 400)
            criar.assert_not_called()
            criar.return_value = {'id': 5}
            self.assertEqual(self.client.post('/api/pedidos', json={
                'endereco': 'Rua Teste 123', 'itens': [{'id': 1, 'quantidade': 2}]
            }).status_code, 201)
            self.assertEqual(criar.call_args.args[0], 10)

    def test_origem_cruzada_bloqueada(self):
        self.assertEqual(self.client.post('/api/login', json={}, headers={
            'Origin': 'https://site-estranho.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/login', json={}, headers={
            'Sec-Fetch-Site': 'cross-site'}).status_code, 403)

    def test_tempo_de_preparo_e_perfil(self):
        cozinheiro = {**self.usuario, 'tipo_usuario': 'cozinheiro',
                     'turno': 'Noite', 'especialidade': 'Massas e molhos'}
        self.entrar_com_sessao()
        with patch('controllers.api.loja.buscar_usuario', return_value=cozinheiro), \
             patch('controllers.api.loja.mudar_status') as mudar:
            for minutos in (0, 241, -1, 'dez', 1.5):
                self.assertEqual(self.client.put('/api/pedidos/2/status', json={
                    'status': 'Em Preparo', 'tempoEstimado': minutos}).status_code, 400)
            mudar.assert_not_called()
            mudar.return_value = {'id': 2, 'status': 'Em Preparo'}
            self.assertEqual(self.client.put('/api/pedidos/2/status', json={
                'status': 'Em Preparo', 'tempoEstimado': 20}).status_code, 200)


if __name__ == '__main__':
    unittest.main()
