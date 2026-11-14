"""Operações de dados do Sabor & Clic. O frontend nunca acessa o banco diretamente."""
from models.banco import banco

STATUS_BANCO = {
    'Recebido': 'aguardando',
    'Em Preparo': 'em_preparo',
    'Pronto': 'pronto',
    'Entregue': 'entregue',
}
STATUS_TELA = {valor: chave for chave, valor in STATUS_BANCO.items()}
PROXIMO_STATUS = {'aguardando': 'em_preparo', 'em_preparo': 'pronto', 'pronto': 'entregue'}


def buscar_usuario(usuario_id=None, email=None):
    if usuario_id is None and email is None:
        return None
    with banco() as cursor:
        if usuario_id is not None:
            cursor.execute('SELECT * FROM usuario WHERE id_usuario = %s', (usuario_id,))
        else:
            cursor.execute('SELECT * FROM usuario WHERE email = %s', (email,))
        return cursor.fetchone()


def criar_usuario(dados):
    with banco() as cursor:
        cursor.execute('''
            INSERT INTO usuario
              (nome, email, senha_hash, tipo_usuario, endereco_entrega, turno,
               especialidade, ativo, trocar_senha)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (dados['nome'], dados['email'], dados['senha_hash'], dados['tipo'],
              dados.get('endereco'), dados.get('turno'), dados.get('especialidade'),
              dados.get('ativo', True), dados.get('trocar_senha', False)))
        return cursor.lastrowid


def mudar_senha(usuario_id, senha_hash):
    with banco() as cursor:
        cursor.execute('UPDATE usuario SET senha_hash=%s, trocar_senha=FALSE WHERE id_usuario=%s',
                       (senha_hash, usuario_id))


def atualizar_administrador(usuario_id, nome, email):
    with banco() as cursor:
        cursor.execute('UPDATE usuario SET nome=%s, email=%s WHERE id_usuario=%s',
                       (nome, email, usuario_id))


def formato_prato(prato):
    return {
        'id': prato['id_prato'], 'nome': prato['nome'],
        'descricao': prato['descricao'] or '', 'preco': float(prato['preco']),
        'categoria': prato['categoria'], 'ativo': bool(prato['ativo']),
    }


def listar_pratos(somente_ativos=False):
    with banco() as cursor:
        cursor.execute('SELECT * FROM prato' + (' WHERE ativo=TRUE' if somente_ativos else '') +
                       ' ORDER BY id_prato')
        return [formato_prato(prato) for prato in cursor.fetchall()]


def salvar_prato(prato, prato_id=None):
    with banco() as cursor:
        valores = (prato['nome'], prato['descricao'], prato['preco'], prato['categoria'], prato['ativo'])
        if prato_id is None:
            cursor.execute('''INSERT INTO prato (nome, descricao, preco, categoria, ativo)
                              VALUES (%s,%s,%s,%s,%s)''', valores)
            prato_id = cursor.lastrowid
        else:
            cursor.execute('''UPDATE prato SET nome=%s, descricao=%s, preco=%s,
                              categoria=%s, ativo=%s WHERE id_prato=%s''', valores + (prato_id,))
            if cursor.rowcount == 0:
                cursor.execute('SELECT 1 FROM prato WHERE id_prato=%s', (prato_id,))
                if not cursor.fetchone():
                    raise LookupError('Prato não encontrado.')
        cursor.execute('SELECT * FROM prato WHERE id_prato=%s', (prato_id,))
        return formato_prato(cursor.fetchone())


def remover_prato(prato_id):
    with banco() as cursor:
        cursor.execute('DELETE FROM prato WHERE id_prato=%s', (prato_id,))
        if cursor.rowcount == 0:
            raise LookupError('Prato não encontrado.')


def formato_cozinheiro(usuario):
    return {
        'id': usuario['id_usuario'], 'nome': usuario['nome'], 'email': usuario['email'],
        'perfil': 'COZINHEIRO', 'turno': usuario['turno'],
        'especialidade': usuario['especialidade'], 'ativo': bool(usuario['ativo']),
    }


def listar_cozinheiros():
    with banco() as cursor:
        cursor.execute("SELECT * FROM usuario WHERE tipo_usuario='cozinheiro' ORDER BY id_usuario")
        return [formato_cozinheiro(u) for u in cursor.fetchall()]


def aprovar_cozinheiro(usuario_id, senha_hash):
    with banco() as cursor:
        cursor.execute("SELECT ativo FROM usuario WHERE id_usuario=%s AND tipo_usuario='cozinheiro' FOR UPDATE", (usuario_id,))
        usuario = cursor.fetchone()
        if not usuario:
            raise LookupError('Cozinheiro não encontrado.')
        if usuario['ativo']:
            raise ValueError('Esse cozinheiro já foi aprovado.')
        cursor.execute('UPDATE usuario SET ativo=TRUE, senha_hash=%s, trocar_senha=TRUE WHERE id_usuario=%s',
                       (senha_hash, usuario_id))


def recusar_cozinheiro(usuario_id):
    with banco() as cursor:
        cursor.execute("SELECT ativo FROM usuario WHERE id_usuario=%s AND tipo_usuario='cozinheiro' FOR UPDATE", (usuario_id,))
        usuario = cursor.fetchone()
        if not usuario:
            raise LookupError('Cozinheiro não encontrado.')
        if usuario['ativo']:
            raise ValueError('Só é possível recusar cadastros pendentes.')
        cursor.execute('DELETE FROM usuario WHERE id_usuario=%s', (usuario_id,))


def listar_pedidos(cliente_id=None, pedido_id=None):
    """Retorna os mesmos campos esperados pela classe Pedido do JavaScript."""
    with banco() as cursor:
        sql = '''SELECT p.id_pedido, p.id_cliente, u.nome AS nome_cliente,
                   COALESCE(p.endereco_entrega, u.endereco_entrega) AS endereco,
                   p.status, p.tempo_estimado, p.valor_total
                 FROM pedido p JOIN usuario u ON u.id_usuario=p.id_cliente WHERE 1=1'''
        parametros = []
        if cliente_id is not None:
            sql += ' AND p.id_cliente=%s'
            parametros.append(cliente_id)
        if pedido_id is not None:
            sql += ' AND p.id_pedido=%s'
            parametros.append(pedido_id)
        sql += ' ORDER BY p.id_pedido'
        cursor.execute(sql, tuple(parametros))
        pedidos = cursor.fetchall()
        if not pedidos:
            return []
        ids = [p['id_pedido'] for p in pedidos]
        marcas = ','.join(['%s'] * len(ids))
        cursor.execute(f'''SELECT ip.id_pedido, pr.id_prato, pr.nome, ip.quantidade,
                               ip.preco_unitario FROM item_pedido ip
                           JOIN prato pr ON pr.id_prato=ip.id_prato
                           WHERE ip.id_pedido IN ({marcas}) ORDER BY ip.id_item''', tuple(ids))
        itens_por_pedido = {pid: [] for pid in ids}
        for item in cursor.fetchall():
            itens_por_pedido[item['id_pedido']].append({
                'id': item['id_prato'], 'nome': item['nome'],
                'preco': float(item['preco_unitario']), 'quantidade': item['quantidade'],
            })
        return [{
            'id': p['id_pedido'], 'idCliente': p['id_cliente'],
            'nomeCliente': p['nome_cliente'], 'endereco': p['endereco'],
            'status': STATUS_TELA.get(p['status'], 'Recebido'),
            'tempoEstimado': p['tempo_estimado'], 'total': float(p['valor_total']),
            'itens': itens_por_pedido[p['id_pedido']],
        } for p in pedidos]


def criar_pedido(cliente_id, endereco, itens):
    with banco() as cursor:
        cursor.execute('INSERT INTO pedido (id_cliente, endereco_entrega) VALUES (%s,%s)',
                       (cliente_id, endereco))
        pedido_id = cursor.lastrowid
        for item in itens:
            cursor.execute('SELECT id_prato, preco, ativo FROM prato WHERE id_prato=%s FOR UPDATE',
                           (item['id'],))
            prato = cursor.fetchone()
            if not prato or not prato['ativo']:
                raise ValueError('Um prato selecionado não está disponível.')
            cursor.execute('''INSERT INTO item_pedido
                            (id_pedido, id_prato, quantidade, preco_unitario)
                            VALUES (%s,%s,%s,%s)''',
                           (pedido_id, item['id'], item['quantidade'], prato['preco']))
    return listar_pedidos(pedido_id=pedido_id)[0]


def mudar_status(pedido_id, novo_status, tempo=None):
    with banco() as cursor:
        cursor.execute('SELECT status FROM pedido WHERE id_pedido=%s FOR UPDATE', (pedido_id,))
        pedido = cursor.fetchone()
        if not pedido:
            raise LookupError('Pedido não encontrado.')
        status_banco = STATUS_BANCO.get(novo_status)
        if not status_banco or PROXIMO_STATUS.get(pedido['status']) != status_banco:
            raise ValueError('Transição de status inválida.')
        cursor.execute('''UPDATE pedido SET status=%s,
                          tempo_estimado=IF(%s IS NULL, tempo_estimado, %s)
                          WHERE id_pedido=%s''', (status_banco, tempo, tempo, pedido_id))
    return listar_pedidos(pedido_id=pedido_id)[0]
