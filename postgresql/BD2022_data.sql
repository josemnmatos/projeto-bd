/*
	#
	# Bases de Dados 2021/2022
	# Projeto
	#
*/

CREATE TABLE produto (
	id SERIAL,
	descricao				 VARCHAR(512),
	tipo				VARCHAR(512),				
	preco				 FLOAT(8) NOT NULL CHECK(preco>=0),
	stock				 BIGINT NOT NULL CHECK(stock>=0),
	vendedor_utilizador_id INTEGER NOT NULL,
	PRIMARY KEY(id)
);

/*
CREATE TABLE televisao (
	tamanho	 VARCHAR(512),
	produto_id BIGINT,
	PRIMARY KEY(produto_id)
);

CREATE TABLE computador (
	processador VARCHAR(512),
	produto_id	 BIGINT,
	PRIMARY KEY(produto_id)
);

CREATE TABLE smartphone (
	sist_op	 VARCHAR(512),
	produto_id BIGINT,
	PRIMARY KEY(produto_id)
);
*/
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
	PRIMARY KEY(produto_id,nome)
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
	username	 VARCHAR(512) NOT NULL,
	pergunta	 VARCHAR(512) NOT NULL,
	produto_id BIGINT,
	PRIMARY KEY(id)
);

CREATE TABLE resposta (
	username				 VARCHAR(512) NOT NULL,
	resposta				 VARCHAR(512) NOT NULL,
	notificacao_resposta_notificacao_id BIGINT,
	thread_id				 BIGINT NOT NULL
);

CREATE TABLE encomenda (
	id					 SERIAL,
	data				 TIMESTAMP NOT NULL,
	notificacao_encomenda_notificacao_id BIGINT,
	comprador_utilizador_id	 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE notificacao (
	id		 SERIAL,
	mensagem	 VARCHAR(512) NOT NULL,
	estado_leitura BOOL NOT NULL,
	data_rececao TIMESTAMP,
	utilizador_id BIGINT,
	PRIMARY KEY(id)
);

CREATE TABLE item_encomenda (
	quantidade	 INTEGER NOT NULL,
	encomenda_id INTEGER,
	produto_id	 BIGINT,
	PRIMARY KEY(encomenda_id,produto_id)
);

/*
CREATE TABLE versao_antiga (
	versao	 INTEGER,
	ativo_ate	 TIMESTAMP,
	produto_id BIGINT NOT NULL,
	PRIMARY KEY(versao)
);

CREATE TABLE notificacao_resposta (
	notificacao_id BIGINT,
	PRIMARY KEY(notificacao_id)
);

CREATE TABLE notificacao_encomenda (
	notificacao_id BIGINT,
	PRIMARY KEY(notificacao_id)
);

CREATE TABLE comprador_notificacao_resposta (
	comprador_utilizador_id INTEGER,
	notificacao_resposta_notificacao_id BIGINT UNIQUE NOT NULL,
	PRIMARY KEY(comprador_utilizador_id)
);

CREATE TABLE vendedor_notificacao_encomenda (
	vendedor_utilizador_id	 INTEGER,
	notificacao_encomenda_notificacao_id BIGINT UNIQUE NOT NULL,
	PRIMARY KEY(vendedor_utilizador_id)
);
*/


/*
ADD CONSTRAINTS FOR FOREIGN KEYS
*/
ALTER TABLE produto ADD CONSTRAINT produto_fk1 FOREIGN KEY (vendedor_utilizador_id) REFERENCES vendedor(utilizador_id);
--ALTER TABLE televisao ADD CONSTRAINT televisao_fk1 FOREIGN KEY (produto_id) REFERENCES produto(id);
--ALTER TABLE computador ADD CONSTRAINT computador_fk1 FOREIGN KEY (produto_id) REFERENCES produto(id);
--ALTER TABLE smartphone ADD CONSTRAINT smartphone_fk1 FOREIGN KEY (produto_id) REFERENCES produto(id);
ALTER TABLE administrador ADD CONSTRAINT administrador_fk1 FOREIGN KEY (utilizador_id) REFERENCES utilizador(id);
ALTER TABLE vendedor ADD CONSTRAINT vendedor_fk1 FOREIGN KEY (utilizador_id) REFERENCES utilizador(id);
ALTER TABLE comprador ADD CONSTRAINT comprador_fk1 FOREIGN KEY (utilizador_id) REFERENCES utilizador(id);
ALTER TABLE rating ADD CONSTRAINT rating_fk1 FOREIGN KEY (comprador_utilizador_id) REFERENCES comprador(utilizador_id);
ALTER TABLE rating ADD CONSTRAINT rating_fk2 FOREIGN KEY (produto_id) REFERENCES produto(id);
--ALTER TABLE resposta ADD CONSTRAINT resposta_fk1 FOREIGN KEY (notificacao_resposta_notificacao_id) REFERENCES notificacao_resposta(notificacao_id);
ALTER TABLE resposta ADD CONSTRAINT resposta_fk2 FOREIGN KEY (thread_id) REFERENCES thread(id);
--ALTER TABLE encomenda ADD CONSTRAINT encomenda_fk1 FOREIGN KEY (notificacao_encomenda_notificacao_id) REFERENCES notificacao_encomenda(notificacao_id);
ALTER TABLE encomenda ADD CONSTRAINT encomenda_fk2 FOREIGN KEY (comprador_utilizador_id) REFERENCES comprador(utilizador_id);
ALTER TABLE item_encomenda ADD CONSTRAINT item_encomenda_fk1 FOREIGN KEY (encomenda_id) REFERENCES encomenda(id);
ALTER TABLE item_encomenda ADD CONSTRAINT item_encomenda_fk2 FOREIGN KEY (produto_id) REFERENCES produto(id);
--ALTER TABLE versao_antiga ADD CONSTRAINT versao_antiga_fk1 FOREIGN KEY (produto_id) REFERENCES produto(id);
--ALTER TABLE notificacao_resposta ADD CONSTRAINT notificacao_resposta_fk1 FOREIGN KEY (notificacao_id) REFERENCES notificacao(id);
--ALTER TABLE notificacao_encomenda ADD CONSTRAINT notificacao_encomenda_fk1 FOREIGN KEY (notificacao_id) REFERENCES notificacao(id);
--LTER TABLE comprador_notificacao_resposta ADD CONSTRAINT comprador_notificacao_resposta_fk1 FOREIGN KEY (comprador_utilizador_id) REFERENCES comprador(utilizador_id);
--ALTER TABLE comprador_notificacao_resposta ADD CONSTRAINT comprador_notificacao_resposta_fk2 FOREIGN KEY (notificacao_resposta_notificacao_id) REFERENCES notificacao_resposta(notificacao_id);
--ALTER TABLE vendedor_notificacao_encomenda ADD CONSTRAINT vendedor_notificacao_encomenda_fk1 FOREIGN KEY (vendedor_utilizador_id) REFERENCES vendedor(utilizador_id);
--ALTER TABLE vendedor_notificacao_encomenda ADD CONSTRAINT vendedor_notificacao_encomenda_fk2 FOREIGN KEY (notificacao_encomenda_notificacao_id) REFERENCES notificacao_encomenda(notificacao_id);

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
INSERT INTO especificacao_antiga(nome,valor,produto_id) VALUES(old.nome,old.valor,old.produto_id);
END;
$$;


/*
SELLER NOTIFICATIONS
*/
CREATE FUNCTION notf_order() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE cur_seller_id CURSOR FOR SELECT vendedor_utilizador_id FROM produto WHERE id=new.produto_id;
seller_id BIGINT;
BEGIN
open cur_seller_id;
FETCH cur_seller_id INTO seller_id;
INSERT INTO notificacao(id,mensagem,estado_leitura,data_rececao,utilizador_id) VALUES(DEFAULT,FORMAT("Foram encomendadas %s unidades do seu produto com o id %s.",new.quantidade, new.produto_id),FALSE,CURRENT_TIMESTAMP,seller_id);
RETURN NEW;
close cur_seller_id;
END;
$$;


CREATE FUNCTION notf_question() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE 
cur_product_name CURSOR FOR SELECT descricao FROM produto WHERE id=new.produto_id;
cur_seller_id CURSOR FOR SELECT vendedor_utilizador_id FROM produto WHERE id=new.produto_id;
product_name VARCHAR(512);
seller_id BIGINT;
BEGIN
open cur_product_name;
open cur_seller_id;
FETCH cur_product_name INTO cur_product_name;
FETCH cur_seller_id INTO seller_id;
INSERT INTO notificacao(id,mensagem,estado_leitura,data_rececao,utilizador_id) VALUES(DEFAULT,FORMAT("Foi feita uma nova pergunta no seu produto: %s",product_name),FALSE,CURRENT_TIMESTAMP,seller_id);
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
--DECLARE cur_seller_id CURSOR FOR SELECT vendedor_utilizador_id FROM produto WHERE id=new.produto_id;
--seller_id BIGINT;
BEGIN
--open cur_seller_id;
--FETCH cur_seller_id INTO seller_id;
INSERT INTO notificacao(id,mensagem,estado_leitura,data_rececao,utilizador_id) VALUES(DEFAULT,FORMAT("A sua encomenda está confirmada.",new.quantidade, new.produto_id),FALSE,CURRENT_TIMESTAMP,new.comprador_utilizador_id);
RETURN NEW;
--close cur_seller_id;
END;
$$; 


/*
TRIGGERS - FALTA COMPRADOR QUANDO EXISTE RESPOSTA A SUA PERGUNTA
*/
CREATE TRIGGER notf_question_trigger
AFTER INSERT ON thread
FOR EACH ROW
EXECUTE PROCEDURE notf_question();


CREATE TRIGGER notf_order_trigger
AFTER INSERT ON item_encomenda
FOR EACH ROW
EXECUTE PROCEDURE notf_order();

CREATE TRIGGER buyer_notf_order_trigger
AFTER INSERT ON encomenda
FOR EACH ROW
EXECUTE PROCEDURE buyer_notf_order();


CREATE TRIGGER save_old_specification_trigger
AFTER UPDATE ON especificacao_atual
FOR EACH ROW
EXECUTE PROCEDURE save_old_specification();