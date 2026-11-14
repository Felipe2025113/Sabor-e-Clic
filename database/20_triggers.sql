
USE sabor_clic;

DELIMITER $$

DROP TRIGGER IF EXISTS trg_item_pedido_ai_total$$

CREATE TRIGGER trg_item_pedido_ai_total
AFTER INSERT ON item_pedido
FOR EACH ROW
BEGIN
    UPDATE pedido
    SET valor_total = (
        SELECT COALESCE(SUM(quantidade * preco_unitario), 0)
        FROM item_pedido
        WHERE id_pedido = NEW.id_pedido
    )
    WHERE id_pedido = NEW.id_pedido;
END$$

DROP TRIGGER IF EXISTS trg_item_pedido_au_total$$

CREATE TRIGGER trg_item_pedido_au_total
AFTER UPDATE ON item_pedido
FOR EACH ROW
BEGIN
    UPDATE pedido
    SET valor_total = (
        SELECT COALESCE(SUM(quantidade * preco_unitario), 0)
        FROM item_pedido
        WHERE id_pedido = NEW.id_pedido
    )
    WHERE id_pedido = NEW.id_pedido;

    IF OLD.id_pedido <> NEW.id_pedido THEN
        UPDATE pedido
        SET valor_total = (
            SELECT COALESCE(SUM(quantidade * preco_unitario), 0)
            FROM item_pedido
            WHERE id_pedido = OLD.id_pedido
        )
        WHERE id_pedido = OLD.id_pedido;
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_item_pedido_ad_total$$

CREATE TRIGGER trg_item_pedido_ad_total
AFTER DELETE ON item_pedido
FOR EACH ROW
BEGIN
    UPDATE pedido
    SET valor_total = (
        SELECT COALESCE(SUM(quantidade * preco_unitario), 0)
        FROM item_pedido
        WHERE id_pedido = OLD.id_pedido
    )
    WHERE id_pedido = OLD.id_pedido;
END$$

DROP TRIGGER IF EXISTS trg_item_pedido_bi_bloqueio$$

CREATE TRIGGER trg_item_pedido_bi_bloqueio
BEFORE INSERT ON item_pedido
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM baixa_estoque_pedido
        WHERE id_pedido = NEW.id_pedido
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nao e permitido adicionar itens: o estoque deste pedido ja foi baixado.';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_item_pedido_bu_bloqueio$$

CREATE TRIGGER trg_item_pedido_bu_bloqueio
BEFORE UPDATE ON item_pedido
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM baixa_estoque_pedido
        WHERE id_pedido = OLD.id_pedido
    ) OR EXISTS (
        SELECT 1 FROM baixa_estoque_pedido
        WHERE id_pedido = NEW.id_pedido
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nao e permitido alterar itens: o estoque deste pedido ja foi baixado.';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_item_pedido_bd_bloqueio$$

CREATE TRIGGER trg_item_pedido_bd_bloqueio
BEFORE DELETE ON item_pedido
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM baixa_estoque_pedido
        WHERE id_pedido = OLD.id_pedido
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nao e permitido excluir itens: o estoque deste pedido ja foi baixado.';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_pedido_au_baixa_estoque$$

CREATE TRIGGER trg_pedido_au_baixa_estoque
AFTER UPDATE ON pedido
FOR EACH ROW
BEGIN
    DECLARE v_ingredientes_necessarios INT DEFAULT 0;
    DECLARE v_ingredientes_atualizados INT DEFAULT 0;

    IF NEW.status = 'em_preparo'
       AND OLD.status <> 'em_preparo'
       AND NOT EXISTS (
           SELECT 1 FROM baixa_estoque_pedido
           WHERE id_pedido = NEW.id_pedido
       ) THEN

        SELECT COUNT(*)
        INTO v_ingredientes_necessarios
        FROM (
            SELECT f.id_ingrediente
            FROM item_pedido ip
            JOIN ficha_tecnica f ON f.id_prato = ip.id_prato
            WHERE ip.id_pedido = NEW.id_pedido
            GROUP BY f.id_ingrediente
        ) AS ingredientes;

        UPDATE ingrediente i
        JOIN (
            SELECT
                f.id_ingrediente,
                SUM(f.quantidade * ip.quantidade) AS quantidade_necessaria
            FROM item_pedido ip
            JOIN ficha_tecnica f ON f.id_prato = ip.id_prato
            WHERE ip.id_pedido = NEW.id_pedido
            GROUP BY f.id_ingrediente
        ) AS consumo ON consumo.id_ingrediente = i.id_ingrediente
        SET i.quantidade_estoque =
            i.quantidade_estoque - consumo.quantidade_necessaria
        WHERE i.quantidade_estoque >= consumo.quantidade_necessaria;

        SET v_ingredientes_atualizados = ROW_COUNT();

        IF v_ingredientes_atualizados <> v_ingredientes_necessarios THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Estoque insuficiente para iniciar o preparo do pedido.';
        END IF;

        INSERT INTO baixa_estoque_pedido (id_pedido)
        VALUES (NEW.id_pedido);
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_locacao_bi_conflito$$

CREATE TRIGGER trg_locacao_bi_conflito
BEFORE INSERT ON locacao
FOR EACH ROW
BEGIN
    IF NEW.status <> 'cancelada' AND EXISTS (
        SELECT 1
        FROM locacao l
        WHERE l.id_bancada = NEW.id_bancada
          AND l.status <> 'cancelada'
          AND NEW.data_inicio < l.data_fim
          AND NEW.data_fim > l.data_inicio
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A bancada ja possui uma locacao nesse periodo.';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_locacao_bu_conflito$$

CREATE TRIGGER trg_locacao_bu_conflito
BEFORE UPDATE ON locacao
FOR EACH ROW
BEGIN
    IF NEW.status <> 'cancelada' AND EXISTS (
        SELECT 1
        FROM locacao l
        WHERE l.id_bancada = NEW.id_bancada
          AND l.id_locacao <> OLD.id_locacao
          AND l.status <> 'cancelada'
          AND NEW.data_inicio < l.data_fim
          AND NEW.data_fim > l.data_inicio
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A bancada ja possui uma locacao nesse periodo.';
    END IF;
END$$

DELIMITER ;
