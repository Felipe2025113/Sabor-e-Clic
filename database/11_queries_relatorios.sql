
USE sabor_clic;

SELECT
    p.id_prato,
    p.nome AS prato,
    SUM(ip.quantidade) AS quantidade_vendida,
    SUM(ip.quantidade * ip.preco_unitario) AS faturamento
FROM item_pedido ip
JOIN prato p ON p.id_prato = ip.id_prato
JOIN pedido pe ON pe.id_pedido = ip.id_pedido
WHERE pe.status <> 'cancelado'
GROUP BY p.id_prato, p.nome
ORDER BY faturamento DESC;

SELECT
    nome AS ingrediente,
    quantidade_estoque,
    unidade_medida,
    estoque_minimo
FROM ingrediente
WHERE quantidade_estoque <= estoque_minimo
ORDER BY nome;

SELECT
    pe.id_pedido,
    u.nome AS cliente,
    pe.data_pedido,
    pe.valor_total,
    pe.status
FROM pedido pe
JOIN usuario u ON u.id_usuario = pe.id_cliente
ORDER BY pe.data_pedido DESC;

SELECT
    pe.id_pedido,
    p.nome AS prato,
    ip.quantidade,
    ip.preco_unitario,
    (ip.quantidade * ip.preco_unitario) AS subtotal
FROM item_pedido ip
JOIN pedido pe ON pe.id_pedido = ip.id_pedido
JOIN prato p ON p.id_prato = ip.id_prato
ORDER BY pe.id_pedido, p.nome;

SELECT
    b.nome AS bancada,
    u.nome AS cliente,
    l.data_inicio,
    l.data_fim,
    l.status,
    l.valor_total
FROM locacao l
JOIN bancada b ON b.id_bancada = l.id_bancada
JOIN usuario u ON u.id_usuario = l.id_cliente
WHERE l.status <> 'cancelada'
ORDER BY l.data_inicio;

SELECT
    COALESCE(SUM(valor_total), 0) AS faturamento_total_pedidos
FROM pedido
WHERE status <> 'cancelado';

SELECT
    COALESCE(SUM(valor_total), 0) AS total_locacoes_finalizadas
FROM locacao
WHERE status = 'finalizada';
