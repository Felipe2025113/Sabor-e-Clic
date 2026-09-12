"""Dados simulados: reiniciar o servidor apaga os pedidos."""
from datetime import datetime, timezone
from decimal import Decimal


def criar_dados():
    return {
        'pratos': [
            {'id': 1, 'nome': 'Marmita Gourmet - Strogonoff de Filé', 'preco': 32.90},
            {'id': 2, 'nome': 'Feijoada Completa Individual', 'preco': 38.50},
            {'id': 3, 'nome': 'Suco Natural de Laranja (500ml)', 'preco': 9.00},
        ],
        'pedidos': [],
    }


def buscar_por_id(lista, identificador):
    return next((item for item in lista if item['id'] == identificador), None)


def montar_pedido(dados, entrada):
    """Valida todos os itens antes de acrescentar o pedido à memória."""
    cliente = entrada.get('cliente')
    endereco = entrada.get('endereco')
    if not isinstance(cliente, str) or len(cliente.strip()) < 3:
        raise ValueError('Informe um cliente com pelo menos 3 caracteres.')
    if not isinstance(endereco, str) or len(endereco.strip()) < 3:
        raise ValueError('Informe um endereço com pelo menos 3 caracteres.')
    itens = entrada.get('itens')
    if not isinstance(itens, list) or not itens:
        raise ValueError('O pedido deve conter pelo menos um item.')

    itens_validados = []
    total = Decimal('0.00')
    for item in itens:
        if not isinstance(item, dict):
            raise ValueError('Cada item deve ser um objeto JSON.')
        prato_id = item.get('prato_id')
        quantidade = item.get('quantidade')
        if type(prato_id) is not int or type(quantidade) is not int or quantidade <= 0:
            raise ValueError('prato_id e quantidade devem ser inteiros positivos.')
        prato = buscar_por_id(dados['pratos'], prato_id)
        if prato is None:
            raise ValueError('Prato não encontrado no cardápio.')
        # O preço vem do servidor, nunca do valor enviado pelo cliente.
        subtotal = Decimal(str(prato['preco'])) * quantidade
        total += subtotal
        itens_validados.append({
            'prato_id': prato_id, 'nome': prato['nome'],
            'quantidade': quantidade, 'preco': prato['preco'],
            'subtotal': float(subtotal),
        })

    return {
        'id': len(dados['pedidos']) + 1,
        'cliente': cliente.strip(), 'endereco': endereco.strip(),
        'itens': itens_validados, 'total': float(total),
        'status': 'Pedido recebido', 'tempoEstimado': None,
        'data_hora': datetime.now(timezone.utc).isoformat(),
    }


def atualizar_status(pedido, entrada):
    proximo_status = {
        'Pedido recebido': 'Em Preparo',
        'Em Preparo': 'Pronto para Entrega',
        'Pronto para Entrega': 'Entregue',
    }
    status = entrada.get('status')
    if pedido['status'] not in proximo_status or status != proximo_status[pedido['status']]:
        raise ValueError('Transição de status inválida.')
    if status == 'Em Preparo':
        tempo = entrada.get('tempoEstimado')
        if type(tempo) is not int or tempo <= 0:
            raise ValueError('Informe tempoEstimado em minutos, como inteiro positivo.')
        pedido['tempoEstimado'] = tempo
    pedido['status'] = status
