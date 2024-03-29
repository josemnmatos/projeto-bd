/*
	#
	# Bases de Dados 2021/2022
	# Projeto
	#
*/

CREATE TABLE produto (
	id SERIAL,
	descricao				 VARCHAR(512),
	tipo				VARCHAR(512) NOT NULL,				
	preco				 FLOAT(8) NOT NULL CHECK(preco>=0),
	stock				 BIGINT NOT NULL CHECK(stock>=0),
	vendedor_utilizador_id INTEGER NOT NULL,
	PRIMARY KEY(id)
);


------------------------------------------------
CREATE TABLE especificacao_atual(
	nome VARCHAR(512),
	valor VARCHAR(512),
	produto_id BIGINT,
	PRIMARY KEY(produto_id,nome)
);

CREATE TABLE especificacao_antiga(
	nome VARCHAR(512),
	valor VARCHAR(512),
	produto_id BIGINT,
	exp_time TIMESTAMP
);

CREATE TABLE historico_preco(
	preco FLOAT(8) NOT NULL CHECK(preco>=0),
	data_exp TIMESTAMP,
	produto_id BIGINT,
	PRIMARY KEY(produto_id,data_exp)
);
-------------------------------------------------


CREATE TABLE utilizador (
	id		 SERIAL,
	username		 VARCHAR(512) UNIQUE NOT NULL,
	email		 VARCHAR(512) UNIQUE NOT NULL,
	password		 VARCHAR(512) NOT NULL,
	active_token VARCHAR(512) UNIQUE,
	PRIMARY KEY(id)
);


CREATE TABLE administrador (
	utilizador_id INTEGER,
	PRIMARY KEY(utilizador_id)
);


CREATE TABLE vendedor (
	utilizador_id INTEGER,
	nif			 BIGINT NOT NULL,
	morada_envio		 VARCHAR(512) NOT NULL,
	endereco_pagamento	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(utilizador_id)
);

CREATE TABLE comprador (
	utilizador_id INTEGER,
	morada			 VARCHAR(512) NOT NULL,
	nif			 BIGINT NOT NULL,
	PRIMARY KEY(utilizador_id)
);

CREATE TABLE rating (
	classificacao		 SMALLINT NOT NULL,
	comentario VARCHAR(512),
	comprador_utilizador_id INTEGER,
	produto_id		 BIGINT,
	PRIMARY KEY(comprador_utilizador_id,produto_id)
);

CREATE TABLE thread (
	id	 SERIAL,
	produto_id BIGINT,
	PRIMARY KEY(id)
);

CREATE TABLE pergunta_resposta (
	id  SERIAL,
	username				 VARCHAR(512) NOT NULL,
	texto				 VARCHAR(512) NOT NULL,
	questao_pai_id				 BIGINT,
	thread_id BIGINT,
	PRIMARY KEY(id)
);

CREATE TABLE encomenda (
	id					 SERIAL,
	data				 TIMESTAMP NOT NULL,
	valor_total FLOAT(8) ,
	notificacao_encomenda_notificacao_id BIGINT,
	comprador_utilizador_id	 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE item_encomenda (
	quantidade	 INTEGER NOT NULL,
	encomenda_id INTEGER,
	produto_id	 BIGINT,
	PRIMARY KEY(encomenda_id,produto_id)
);

CREATE TABLE notificacao (
	id		 SERIAL,
	mensagem	 VARCHAR(512) NOT NULL,
	estado_leitura BOOL NOT NULL,
	data_rececao TIMESTAMP,
	utilizador_id BIGINT,
	PRIMARY KEY(id)
);


/*
ADD CONSTRAINTS FOR FOREIGN KEYS
*/
ALTER TABLE produto ADD CONSTRAINT produto_fk1 FOREIGN KEY (vendedor_utilizador_id) REFERENCES vendedor(utilizador_id);
ALTER TABLE administrador ADD CONSTRAINT administrador_fk1 FOREIGN KEY (utilizador_id) REFERENCES utilizador(id);
ALTER TABLE vendedor ADD CONSTRAINT vendedor_fk1 FOREIGN KEY (utilizador_id) REFERENCES utilizador(id);
ALTER TABLE comprador ADD CONSTRAINT comprador_fk1 FOREIGN KEY (utilizador_id) REFERENCES utilizador(id);
ALTER TABLE rating ADD CONSTRAINT rating_fk1 FOREIGN KEY (comprador_utilizador_id) REFERENCES comprador(utilizador_id);
ALTER TABLE rating ADD CONSTRAINT rating_fk2 FOREIGN KEY (produto_id) REFERENCES produto(id);
ALTER TABLE pergunta_resposta ADD CONSTRAINT resposta_fk2 FOREIGN KEY (thread_id) REFERENCES thread(id);
ALTER TABLE encomenda ADD CONSTRAINT encomenda_fk2 FOREIGN KEY (comprador_utilizador_id) REFERENCES comprador(utilizador_id);
ALTER TABLE item_encomenda ADD CONSTRAINT item_encomenda_fk1 FOREIGN KEY (encomenda_id) REFERENCES encomenda(id);
ALTER TABLE item_encomenda ADD CONSTRAINT item_encomenda_fk2 FOREIGN KEY (produto_id) REFERENCES produto(id);

/*
BASE VALUES
*/
--first admin
INSERT INTO utilizador (username,email,password) VALUES ('admin','admin@gmail.com','password');
INSERT INTO administrador (utilizador_id) SELECT id from utilizador WHERE username='admin';


/*
FUNCTIONS
*/
CREATE FUNCTION save_old_specification() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
INSERT INTO especificacao_antiga(nome,valor,produto_id,exp_time) VALUES(old.nome,old.valor,old.produto_id,CURRENT_TIMESTAMP);
RETURN NEW;
END;
$$;

CREATE FUNCTION save_old_price() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
INSERT INTO historico_preco(preco,produto_id,data_exp) SELECT preco,id,CURRENT_TIMESTAMP from produto WHERE id=old.id;
RETURN NEW;
END;
$$;


/*
SELLER NOTIFICATIONS
*/
/*
CREATE FUNCTION notf_order() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE cur_seller_id CURSOR FOR SELECT vendedor_utilizador_id FROM produto WHERE id=new.produto_id;
seller_id BIGINT;
msg VARCHAR(512) :='';
BEGIN
open cur_seller_id;
FETCH cur_seller_id INTO seller_id;
msg:='Foram encomendadas '|| new.quantidade ||' unidades do seu produto com o id ' || new.produto_id;
INSERT INTO notificacao(id,mensagem,estado_leitura,data_rececao,utilizador_id) VALUES(DEFAULT,msg,FALSE,CURRENT_TIMESTAMP,seller_id);
RETURN NEW;
close cur_seller_id;
END;
$$;
*/

CREATE FUNCTION notf_question() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE 
cur_product_name CURSOR FOR SELECT descricao FROM produto WHERE id=new.produto_id;
cur_seller_id CURSOR FOR SELECT vendedor_utilizador_id FROM produto WHERE id=new.produto_id;
product_name VARCHAR(512);
seller_id BIGINT;
msg VARCHAR(512) :='';
BEGIN
open cur_product_name;
open cur_seller_id;
FETCH cur_product_name INTO product_name;
FETCH cur_seller_id INTO seller_id;
msg:='Foi feita uma nova pergunta no seu produto: '||product_name;
INSERT INTO notificacao(id,mensagem,estado_leitura,data_rececao,utilizador_id) VALUES(DEFAULT,msg,FALSE,CURRENT_TIMESTAMP,seller_id);
RETURN NEW;
close cur_seller_id;
close cur_product_name;
END;
$$;

/*
BUYER NOTIFICATIONS
*/

CREATE FUNCTION buyer_notf_order() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE
INSERT INTO notificacao(id,mensagem,estado_leitura,data_rececao,utilizador_id) VALUES(DEFAULT,'A sua encomenda está confirmada.',FALSE,CURRENT_TIMESTAMP,new.comprador_utilizador_id);
RETURN NEW;
END;
$$; 


/*
TRIGGERS - FALTA COMPRADOR QUANDO EXISTE RESPOSTA A SUA PERGUNTA
*/
CREATE TRIGGER notf_question_trigger
AFTER INSERT ON thread
FOR EACH ROW
EXECUTE PROCEDURE notf_question();

/*
CREATE TRIGGER notf_order_trigger
AFTER INSERT ON item_encomenda
FOR EACH ROW
EXECUTE PROCEDURE notf_order();
*/

CREATE TRIGGER buyer_notf_order_trigger
AFTER INSERT ON encomenda
FOR EACH ROW
EXECUTE PROCEDURE buyer_notf_order();


CREATE TRIGGER save_old_specification_trigger
BEFORE UPDATE ON especificacao_atual
FOR EACH ROW
EXECUTE PROCEDURE save_old_specification();

CREATE TRIGGER save_old_price_trigger
BEFORE UPDATE OF preco ON produto
FOR EACH ROW
EXECUTE PROCEDURE save_old_price();