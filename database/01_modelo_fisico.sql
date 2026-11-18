

CREATE DATABASE IF NOT EXISTS sabor_clic
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE sabor_clic;


SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS baixa_estoque_pedido;
DROP TABLE IF EXISTS locacao;
DROP TABLE IF EXISTS bancada;
DROP TABLE IF EXISTS item_pedido;
DROP TABLE IF EXISTS pedido;
DROP TABLE IF EXISTS ficha_tecnica;
DROP TABLE IF EXISTS ingrediente;
DROP TABLE IF EXISTS prato;
DROP TABLE IF EXISTS usuario;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    tipo_usuario ENUM('administrador', 'cliente', 'cozinheiro') NOT NULL,
    nivel_permissao VARCHAR(50) NULL,
    endereco_entrega VARCHAR(255) NULL,
    turno VARCHAR(50) NULL,
    especialidade VARCHAR(100) NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    trocar_senha BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE prato (
    id_prato INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT NULL,
    categoria VARCHAR(100) NOT NULL DEFAULT 'Diversos',
    preco DECIMAL(10,2) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_prato_preco CHECK (preco >= 0)
) ENGINE=InnoDB;

CREATE TABLE ingrediente (
    id_ingrediente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    quantidade_estoque DECIMAL(10,3) NOT NULL DEFAULT 0,
    unidade_medida VARCHAR(20) NOT NULL,
    estoque_minimo DECIMAL(10,3) NOT NULL DEFAULT 0,
    CONSTRAINT chk_ingrediente_estoque CHECK (quantidade_estoque >= 0),
    CONSTRAINT chk_ingrediente_minimo CHECK (estoque_minimo >= 0)
) ENGINE=InnoDB;

-- Tabela associativa entre PRATO e INGREDIENTE

CREATE TABLE ficha_tecnica (
    id_prato INT NOT NULL,
    id_ingrediente INT NOT NULL,
    quantidade DECIMAL(10,3) NOT NULL,
    PRIMARY KEY (id_prato, id_ingrediente),
    CONSTRAINT fk_ficha_prato FOREIGN KEY (id_prato)
        REFERENCES prato(id_prato)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ficha_ingrediente FOREIGN KEY (id_ingrediente)
        REFERENCES ingrediente(id_ingrediente)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_ficha_quantidade CHECK (quantidade > 0)
) ENGINE=InnoDB;

CREATE TABLE pedido (
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    data_pedido DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valor_total DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('aguardando', 'em_preparo', 'pronto', 'entregue', 'cancelado')
        NOT NULL DEFAULT 'aguardando',
    endereco_entrega VARCHAR(255) NULL,
    tempo_estimado INT NULL,
    CONSTRAINT chk_pedido_tempo CHECK (tempo_estimado IS NULL OR tempo_estimado BETWEEN 1 AND 240),
    CONSTRAINT fk_pedido_cliente FOREIGN KEY (id_cliente)
        REFERENCES usuario(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_pedido_total CHECK (valor_total >= 0)
) ENGINE=InnoDB;

CREATE TABLE item_pedido (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido INT NOT NULL,
    id_prato INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_item_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido(id_pedido)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_item_prato FOREIGN KEY (id_prato)
        REFERENCES prato(id_prato)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_item_quantidade CHECK (quantidade > 0),
    CONSTRAINT chk_item_preco CHECK (preco_unitario >= 0)
) ENGINE=InnoDB;

CREATE TABLE bancada (
    id_bancada INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT NULL,
    valor_hora DECIMAL(10,2) NOT NULL,
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_bancada_valor CHECK (valor_hora >= 0)
) ENGINE=InnoDB;

CREATE TABLE locacao (
    id_locacao INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_bancada INT NOT NULL,
    data_inicio DATETIME NOT NULL,
    data_fim DATETIME NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL,
    status ENUM('reservada', 'em_andamento', 'finalizada', 'cancelada')
        NOT NULL DEFAULT 'reservada',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_locacao_cliente FOREIGN KEY (id_cliente)
        REFERENCES usuario(id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_locacao_bancada FOREIGN KEY (id_bancada)
        REFERENCES bancada(id_bancada)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_locacao_periodo CHECK (data_fim > data_inicio),
    CONSTRAINT chk_locacao_valor CHECK (valor_total >= 0)
) ENGINE=InnoDB;

CREATE TABLE baixa_estoque_pedido (
    id_pedido INT PRIMARY KEY,
    data_baixa DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_baixa_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido(id_pedido)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;
