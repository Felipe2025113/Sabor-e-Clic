import unittest
from app import create_app


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()
        self.pedido = {
            'cliente': 'Cliente Teste', 'endereco': 'Rua de teste, 10',
            'itens': [{'prato_id': 1, 'quantidade': 2, 'preco': 0.01}],
        }

    def criar(self):
        return self.client.post('/api/pedidos', json=self.pedido)

    def test_total_calculado_no_servidor_e_consulta(self):
        resposta = self.criar()
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.json['dados']['total'], 65.8)
        consulta = self.client.get('/api/pedidos/1')
        self.assertEqual(consulta.json['dados']['cliente'], 'Cliente Teste')

    def test_itens_invalidos_nao_criam_pedido_parcial(self):
        for quantidade in (0, -1, True, 1.5, '2'):
            with self.subTest(quantidade=quantidade):
                self.pedido['itens'] = [
                    {'prato_id': 1, 'quantidade': 1},
                    {'prato_id': 2, 'quantidade': quantidade},
                ]
                self.assertEqual(self.criar().status_code, 400)
        self.assertEqual(self.client.get('/api/pedidos').json['dados'], [])

    def test_prato_inexistente_e_campos_obrigatorios(self):
        for itens in ([], [{'prato_id': 999, 'quantidade': 1}], [None]):
            self.pedido['itens'] = itens
            self.assertEqual(self.criar().status_code, 400)
        self.pedido['cliente'] = ' '
        self.assertEqual(self.criar().status_code, 400)

    def test_json_invalido(self):
        for opcoes in ({'json': []}, {'data': '{', 'content_type': 'application/json'}, {'data': 'teste'}):
            resposta = self.client.post('/api/pedidos', **opcoes)
            self.assertEqual(resposta.status_code, 400)
            self.assertFalse(resposta.json['sucesso'])

    def test_fluxo_status_e_tempo(self):
        self.criar()
        rota = '/api/pedidos/1/status'
        self.assertEqual(self.client.patch(rota, json={'status': 'Entregue'}).status_code, 400)
        for tempo in (None, -1, True, 'dez'):
            resposta = self.client.patch(rota, json={'status': 'Em Preparo', 'tempoEstimado': tempo})
            self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.client.get('/api/pedidos/1').json['dados']['status'], 'Pedido recebido')
        for status in ('Em Preparo', 'Pronto para Entrega', 'Entregue'):
            resposta = self.client.patch(rota, json={'status': status, 'tempoEstimado': 20})
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(resposta.json['dados']['status'], status)
        self.assertEqual(self.client.patch(rota, json={'status': 'Em Preparo', 'tempoEstimado': 20}).status_code, 400)

    def test_dados_reiniciam_com_aplicacao(self):
        self.criar()
        outra = create_app().test_client()
        self.assertEqual(outra.get('/api/pedidos').json['dados'], [])

    def test_rotas_paginas_e_arquivos_existentes(self):
        for caminho in ('/api/health', '/api/pratos', '/demo-api',
                        '/templates/index.html', '/templates/Cliente.html',
                        '/templates/ADM.html', '/templates/Cozinheiro.html',
                        '/templates/script.js', '/templates/imagens/cozinha.jpg',
                        '/static/css/style.css', '/static/js/demo_api.js'):
            with self.subTest(caminho=caminho):
                resposta = self.client.get(caminho)
                self.assertEqual(resposta.status_code, 200)
                resposta.close()
        self.assertEqual(self.client.get('/').location, '/templates/index.html')

    def test_nao_encontrado(self):
        for caminho in ('/api/pedidos/999', '/api/inexistente', '/templates/app.py'):
            resposta = self.client.get(caminho)
            self.assertEqual(resposta.status_code, 404)
            self.assertFalse(resposta.json['sucesso'])


if __name__ == '__main__':
    unittest.main()
