IF EXISTS(SELECT * FROM produto WHERE produto.id = %s AND produto.stock >= %s) THEN 
(INSERT INTO item_encomenda(quantidade,encomenda_id,produto_id) VALUES(%s,%s,%s) 
UNION 
UPDATE produto SET produto.stock = produto.stock - %s WHERE produto.id=%s) 
END IF;