-- Os hashes de teste dos usuários abaixo não permitem login. Crie o administrador usando python -m scripts.criar_admin.

USE sabor_clic;

INSERT INTO usuario
(nome, email, senha_hash, tipo_usuario, nivel_permissao, endereco_entrega, turno, especialidade)
VALUES
('Ana Souza', 'ana@email.com', 'hash_de_teste_ana', 'cliente', NULL, 'Rua A, 100', NULL, NULL),
('Carlos Lima', 'carlos@email.com', 'hash_de_teste_carlos', 'administrador', 'total', NULL, NULL, NULL),
('Marina Costa', 'marina@email.com', 'hash_de_teste_marina', 'cozinheiro', NULL, NULL, 'Noite', 'Massas e molhos'),
('João Alves', 'joao@email.com', 'hash_de_teste_joao', 'cliente', NULL, 'Rua B, 200', NULL, NULL);

INSERT INTO prato (nome, descricao, preco, categoria, ativo) VALUES
('Hambúrguer artesanal', 'Hambúrguer com pão, carne e queijo.', 25.00, 'Lanches', TRUE),
('Pizza de mussarela', 'Pizza individual de mussarela.', 40.00, 'Pizzas', TRUE),
('Lasanha', 'Lasanha à bolonhesa.', 32.00, 'Massas', TRUE);

INSERT INTO ingrediente
(nome, quantidade_estoque, unidade_medida, estoque_minimo)
VALUES
('Pão', 100.000, 'unidade', 10.000),
('Carne', 50.000, 'kg', 5.000),
('Queijo', 20.000, 'kg', 2.000),
('Molho de tomate', 15.000, 'kg', 2.000),
('Massa de lasanha', 10.000, 'kg', 1.000);

INSERT INTO ficha_tecnica (id_prato, id_ingrediente, quantidade) VALUES
(1, 1, 1.000),   -- 1 pão
(1, 2, 0.150),   -- 150 g de carne
(1, 3, 0.050),   -- 50 g de queijo
(2, 3, 0.200),   -- 200 g de queijo
(2, 4, 0.100),   -- 100 g de molho
(3, 4, 0.150),   -- 150 g de molho
(3, 5, 0.200);   -- 200 g de massa

INSERT INTO bancada (nome, descricao, valor_hora, ativa) VALUES
('Bancada 1', 'Bancada equipada para preparo geral.', 35.00, TRUE),
('Bancada 2', 'Bancada equipada para confeitaria.', 45.00, TRUE);

INSERT INTO pedido (id_cliente, valor_total, status) VALUES
(1, 50.00, 'aguardando'),
(4, 40.00, 'aguardando');

INSERT INTO item_pedido (id_pedido, id_prato, quantidade, preco_unitario) VALUES
(1, 1, 2, 25.00),
(2, 2, 1, 40.00);

INSERT INTO locacao
(id_cliente, id_bancada, data_inicio, data_fim, valor_total, status)
VALUES
(1, 1, '2026-11-20 09:00:00', '2026-11-20 12:00:00', 105.00, 'reservada');
