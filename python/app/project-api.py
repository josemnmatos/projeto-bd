import flask
import logging, psycopg2, time
import jwt
from datetime import date, datetime

jwt_secret = "bdprojeto"

app = flask.Flask(__name__)

StatusCodes = {"success": 200, "api_error": 400, "internal_error": 500}


# types of product allowed (only 3 for testing)
allowed_types = ["tv", "smartphone", "computer"]
# types of specs allowed for each product (only one for testing)
tv_allowed_specs = ["size"]
smartphone_allowed_specs = ["os"]
computer_allowed_specs = ["cpu"]

##########################################################
## DATABASE ACCESS
##########################################################


def db_connection():
    db = psycopg2.connect(user="dev", password="password", host="db", port="5432", database="dbprojeto")

    return db


##########################################################
## AUX FUNCTIONS
##########################################################

# funcao para ajudar na construcao do payload da jwt
def get_user_permission(id):
    conn = db_connection()
    cur = conn.cursor()
    values = (id,)
    # vendedor
    query1 = "SELECT * from vendedor WHERE utilizador_id=%s"
    cur.execute(query1, values)
    result = cur.fetchone()
    if result is not None:
        return "vendedor"
    # admin
    query2 = "SELECT * from administrador WHERE utilizador_id=%s"
    cur.execute(query2, values)
    result = cur.fetchone()
    if result is not None:
        return "administrador"
    # comprador
    return "comprador"


##########################################################
## ENDPOINTS
##########################################################


@app.route("/dbproj/")
def landing_page():
    return """

    This is the landing page for the Databases Course project.  <br/>
    <br/>
    Check documentation for information on how to use endpoints.<br/>
    <br/>
    The project team: José Matos, Eugénia Oliveira.<br/>
    <br/>
    """


##########################################################
## USER: CRIAR E AUTENTICAR, NOTIFICACOES
##########################################################

## Registo de utilizadores
##-----------------------------------------------
@app.route("/dbproj/user/", methods=["POST"])
def cria_utilizador():
    logger.info("POST /dbproj/user")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /dbproj/user - payload: {payload}")

    # do not forget to validate every argument, e.g.,:
    if "username" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "username value not in payload"}
        return flask.jsonify(response)

    if "email" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "email value not in payload"}
        return flask.jsonify(response)

    if "password" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "password value not in payload"}
        return flask.jsonify(response)

    if "role" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "role value not in payload"}
        return flask.jsonify(response)

    if payload["role"] not in ["comprador", "vendedor", "administrador"]:
        response = {
            "status": StatusCodes["api_error"],
            "results": "role value not valid: comprador,vendedor or administrador",
        }
        return flask.jsonify(response)

    # parameterized queries, good for security and performance

    # verificar permissao presente na token
    if payload["role"] in ["vendedor", "administrador"]:
        # necessidade de verificar token de administrador
        if "token" not in payload:
            response = {
                "status": StatusCodes["api_error"],
                "results": "token value needed when creating vendedor or administrador",
            }
            return flask.jsonify(response)

        auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms=["HS256"])

        if auth_payload["auth_role"] != "administrador":
            response = {
                "status": StatusCodes["api_error"],
                "results": "admin permission needed to create administrador or vendedor",
            }
            return flask.jsonify(response)

    statement1 = "INSERT INTO utilizador (id, username, email, password) VALUES (DEFAULT, %s, %s,%s) RETURNING id"
    values1 = (payload["username"], payload["email"], payload["password"])

    try:
        cur.execute(statement1, values1)
        ret_id = cur.fetchone()[0]

        # insert nas tabelas relativas ao cargo
        if payload["role"] == "comprador":
            if "nif" not in payload:
                response = {"status": StatusCodes["api_error"], "results": "nif value not in payload"}
                return flask.jsonify(response)

            if "morada" not in payload:
                response = {"status": StatusCodes["api_error"], "results": "morada value not in payload"}
                return flask.jsonify(response)

            statement2 = "INSERT INTO comprador (utilizador_id, morada, nif) VALUES (%s, %s,%s)"
            values2 = (ret_id, payload["morada"], payload["nif"])

        elif payload["role"] == "vendedor":
            if "nif" not in payload:
                response = {"status": StatusCodes["api_error"], "results": "nif value not in payload"}
                return flask.jsonify(response)

            if "morada_envio" not in payload:
                response = {"status": StatusCodes["api_error"], "results": "morada_envio value not in payload"}
                return flask.jsonify(response)

            if "endereco_pagamento" not in payload:
                response = {"status": StatusCodes["api_error"], "results": "endereco_pagamento value not in payload"}
                return flask.jsonify(response)

            statement2 = (
                "INSERT INTO vendedor (utilizador_id,nif,morada_envio,endereco_pagamento) VALUES (%s, %s,%s,%s)"
            )
            values2 = (ret_id, payload["nif"], payload["morada_envio"], payload["endereco_pagamento"])

        elif payload["role"] == "administrador":
            statement2 = "INSERT INTO administrador (utilizador_id) VALUES (%s) RETURNING id"
            values2 = (ret_id,)

        # insert into tabelas de cargo
        cur.execute(statement2, values2)

        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f"{ret_id}"}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"POST /user - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Autenticacao de utilizadores
##-----------------------------------------------
@app.route("/dbproj/user/", methods=["PUT"])
def autenticar_user():
    logger.info("PUT /dbproj/user/")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"PUT /dbproj/user/ - payload: {payload}")

    # do not forget to validate every argument, e.g.,:
    if "username" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "username value not in payload"}
        return flask.jsonify(response)

    if "password" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "password value not in payload"}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    # atualiza descricao
    statement = "SELECT password,id from utilizador WHERE username=%s"
    req_username = payload["username"]
    req_password = payload["password"]

    try:
        cur.execute(statement, (req_username,))  # postgres apenas aceita tuplo
        res = cur.fetchall()[0]
        if res[0] == str(req_password):  # passwords match
            login_user_id = res[1]
            # codifica token própria do user para o login atual
            token = jwt.encode(
                {
                    "auth_id": login_user_id,
                    "auth_user": payload["username"],
                    "auth_role": get_user_permission(login_user_id),
                },
                jwt_secret,
                algorithm="HS256",
            )
            # adicionar token ao user
            statement = "UPDATE utilizador SET active_token=%s WHERE username = %s"
            args = (token, req_username)
            cur.execute(statement, args)
            response = {"status": StatusCodes["success"], "results": f"User logged in: {req_username}", "token": token}
        else:
            response = {"status": StatusCodes["internal_error"], "results": f"Passwords do not match."}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##########################################################
## PRODUTO: CRIAR, ATUALIZAR, CONSULTAR INFO
##########################################################

## Obter todos os produtos(testar)
##-----------------------------------------------
@app.route("/dbproj/product/", methods=["GET"])
def get_all_products():
    logger.info("GET /dbproj/product")

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id,tipo, descricao, preco,stock FROM produto ORDER BY id")
        rows = cur.fetchall()

        logger.debug("GET /dbproj/product - parse")
        Results = []
        for row in rows:
            logger.debug(row)
            content = {"id": int(row[0]), "tipo": row[1], "description": row[2], "price": row[3], "stock": row[4]}
            Results.append(content)  # appending to the payload to be returned

        response = {"status": StatusCodes["success"], "results": Results}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"GET /dbproj/product - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Criar novo produto
##-----------------------------------------------
@app.route("/dbproj/product/", methods=["POST"])
def cria_produto():
    logger.info("POST /dbproj/product")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /dbproj/product - payload: {payload}")

    # do not forget to validate every argument, e.g.,:

    if "description" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "description value not in payload"}
        return flask.jsonify(response)

    if "price" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "pr value not in payload"}
        return flask.jsonify(response)

    if "stock" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "stock value not in payload"}
        return flask.jsonify(response)

    if "type" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "stock value not in payload"}
        return flask.jsonify(response)

    if "spec_name" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "spec_name not in payload"}
        return flask.jsonify(response)

    if "spec_value" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "spec_value not in payload"}
        return flask.jsonify(response)

    if "token" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "token value not in payload"}
        return flask.jsonify(response)

    # check specs
    if payload["type"] not in allowed_types:
        response = {"status": StatusCodes["api_error"], "results": "type value not allowed"}
        return flask.jsonify(response)
    elif payload["type"] == "tv":
        # check for size
        if payload["spec_name"] != "size":
            response = {
                "status": StatusCodes["api_error"],
                "results": "size spec needed to register product of type tv",
            }
            return flask.jsonify(response)

    elif payload["type"] == "smartphone":
        # check for os
        if payload["spec_name"] != "os":
            response = {"status": StatusCodes["api_error"], "results": "os spec needed to register product of type tv"}
            return flask.jsonify(response)

    elif payload["type"] == "computer":
        # check for cpu
        if payload["spec_name"] != "cpu":
            response = {
                "status": StatusCodes["api_error"],
                "results": "cpu spec needed to register product of type tv",
            }
            return flask.jsonify(response)

    # verifica se user é vendedor

    auth_token = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")

    if auth_token["auth_role"] != "vendedor":
        response = {
            "status": StatusCodes["api_error"],
            "results": "must have vendedor permission to execute this request",
        }
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement1 = "INSERT INTO produto (id, descricao,tipo, preco, stock, vendedor_utilizador_id) VALUES (DEFAULT,%s, %s, %s,%s,%s) RETURNING id"
    values1 = (
        payload["description"],
        payload["type"],
        float(payload["price"]),
        int(payload["stock"]),
        auth_token["auth_id"],
    )

    statement2 = "INSERT INTO especificacao_atual(nome,valor,produto_id) VALUES(%s,%s,%s)"

    try:
        # executa e retorna id para adicionar ao produto
        cur.execute(statement1, values1)
        product_id = cur.fetchone()[0]

        # executa a adiçao da especificacao
        values2 = (payload["spec_name"], payload["spec_value"], product_id)
        cur.execute(statement2, values2)

        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f"{product_id}"}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"POST /dbproj/product - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Atualizar detalhes produto
##-----------------------------------------------
@app.route("/dbproj/product/<product_id>", methods=["PUT"])
def atualiza_produto(product_id):
    logger.info("PUT /dbproj/product/<product_id>")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"PUT /dbproj/product/<product_id> - payload: {payload}")

    # check if product exists
    stat = "SELECT * FROM produto where id=%s"
    val = (product_id,)
    cur.execute(stat, val)
    if cur.fetchall() == []:
        response = {
            "status": StatusCodes["api_error"],
            "results": "product with chosen id does not exist",
        }
        return flask.jsonify(response)

    # do not forget to validate every argument, e.g.,:
    if "description" not in payload and "price" not in payload and "stock" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "descricao,preco or stock are required to update",
        }
        return flask.jsonify(response)

    if "token" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "token value not in payload"}
        return flask.jsonify(response)

    # para verificar se user ativo é o vendedor do produto a atualizar
    auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")

    # parameterized queries, good for security and performance
    # atualiza descricao
    try:
        # check if spec updates need to be done
        if "spec_name" in payload:
            if "spec_value" not in payload:
                response = {"status": StatusCodes["api_error"], "results": "spec value needed in order to update spec"}
                return flask.jsonify(response)
            # if yes then get product type
            stat = "SELECT tipo from produto WHERE id=%s"
            values = (product_id,)
            cur.execute(stat, values)
            product_type = cur.fetchone()[0]
            # check if spec meets product type
            if product_type == "tv" and payload["spec_name"] not in tv_allowed_specs:
                response = {"status": StatusCodes["api_error"], "results": "spec not allowed for product type tv"}
                return flask.jsonify(response)

            if product_type == "smartphone" and payload["spec_name"] not in smartphone_allowed_specs:
                response = {
                    "status": StatusCodes["api_error"],
                    "results": "spec not allowed for product type smartphone",
                }
                return flask.jsonify(response)

            if product_type == "computer" and payload["spec_name"] not in computer_allowed_specs:
                response = {
                    "status": StatusCodes["api_error"],
                    "results": "spec not allowed for product type computer",
                }
                return flask.jsonify(response)

            # update the spec
            stat1 = "UPDATE especificacao_atual SET valor=%s WHERE produto_id=%s and nome=%s"
            values1 = (payload["spec_value"], product_id, payload["spec_name"])
            cur.execute(stat1, values1)

        statement = (
            "UPDATE produto SET descricao = %s, preco = %s, stock = %s WHERE id = %s RETURNING vendedor_utilizador_id"
        )
        values = (payload["description"], payload["price"], payload["stock"], product_id)

        cur.execute(statement, values)
        # vendedor não corresponde ao user atual
        seller_id = cur.fetchone()[0]

        if seller_id != auth_payload["auth_id"]:
            response = {"status": StatusCodes["api_error"], "results": "current user is not seller of product chosen"}
            conn.rollback()
            return flask.jsonify(response)

        response = {"status": StatusCodes["success"]}
        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Consultar informacao generica de um produto -GET
## FALTA A PARTE DO PREÇO POR CAUSA DO HISTORICO#####
##-----------------------------------------------
@app.route("/dbproj/product/<product_id>", methods=["GET"])
def consultar_info(product_id):
    logger.info("GET /dbproj/product/<product_id>")

    conn = db_connection()
    cur = conn.cursor()

    statement="SELECT description,"
    values=(product_id,)

    try:
        
        cur.execute(statement,values)
        rows = cur.fetchall()

        logger.debug("GET /dbproj/product/<product_id> - parse")
        Results = []
        for row in rows:
            logger.debug(row)
            content = {"description": row[0], "price": row[1], "classificacao": row[2], "comentario": row[3]}
            Results.append(content)  # appending to the payload to be returned

        response = {"status": StatusCodes["success"], "results": Results}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"GET /dbproj/product/<product_id> - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##########################################################
## COMPRA
##########################################################

## Efetuar compra-PUT
##-----------------------------------------------
@app.route("/dbproj/order/", methods=["POST"])
def efetuar_compra():
    logger.info("POST /dbproj/order")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /dbproj/order - payload: {payload}")

    # do not forget to validate every argument, e.g.,:
    if "cart" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "cart is required to make an order",
        }
        return flask.jsonify(response)

    if "token" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "token is required to make an order",
        }
        return flask.jsonify(response)

    # check if current user is a buyer
    auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")
    if auth_payload["auth_role"] != "comprador":
        response = {
            "status": StatusCodes["api_error"],
            "results": "role must be comprador to make an order",
        }
        return flask.jsonify(response)

    # verify cart input
    for order_item in payload["cart"]:
        product_id = int(order_item[0])
        order_quantity = int(order_item[1])

        if order_quantity <= 0 or product_id <= 0:
            response = {
                "status": StatusCodes["api_error"],
                "results": "values not valid",
            }
            return flask.jsonify(response)

        if isinstance(product_id, int) == 0 or isinstance(order_quantity, int) == 0:
            response = {
                "status": StatusCodes["api_error"],
                "results": "cart format not valid",
            }
            return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = "INSERT INTO encomenda (id, data, comprador_utilizador_id) VALUES (DEFAULT, %s, %s) RETURNING id"
    values = (datetime.utcnow(), auth_payload["auth_id"])

    try:
        cur.execute(statement, values)
        id_encomenda = cur.fetchone()[0]
        # insert every order item
        for order_item in payload["cart"]:
            item_product_id = order_item[0]
            item_product_quantity = order_item[1]
            # check stock and insert into sale item table
            statement = "INSERT INTO item_encomenda(quantidade,encomenda_id,produto_id) VALUES(%s,%s,%s)"
            values = (item_product_quantity, id_encomenda, item_product_id)
            cur.execute(statement, values)
            # update stock
            statement = " UPDATE produto SET stock = stock - %s WHERE id=%s"
            values = (item_product_quantity, item_product_id)
            cur.execute(statement, values)

        response = {"status": StatusCodes["success"], "results": f"{id_encomenda}"}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##########################################################
## DEIXAR RATING/FEEDBACK
##########################################################

## Ver ratings de um produto(para teste)-GET
##-----------------------------------------------

## Deixar rating a produto comprado-POST
##-----------------------------------------------
@app.route("/dbproj/rating/<product_id>", methods=["POST"])
def deixar_rating(product_id):
    logger.info("POST /dbproj/rating/<product_id>")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /dbproj/rating/<product_id> - payload: {payload}")

    # do not forget to validate every argument, e.g.,:
    if "rating" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "rating value is required to leave a review",
        }
        return flask.jsonify(response)

    if int(payload["rating"]) > 5 or int(payload["rating"]) < 0:
        response = {
            "status": StatusCodes["api_error"],
            "results": "rating value must be an integer between 1 and 5",
        }
        return flask.jsonify(response)

    if "comment" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "comment is required to leave a review",
        }
        return flask.jsonify(response)

    if "token" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "token is required to make an order",
        }
        return flask.jsonify(response)

    auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")
    # check if current user is a buyer and has bought the product
    if auth_payload["auth_role"] != "comprador":
        response = {
            "status": StatusCodes["api_error"],
            "results": "role must be comprador to leave a review",
        }
        return flask.jsonify(response)
    # check if has bought the product

    statement = "WITH user_orders AS(SELECT id from encomenda WHERE comprador_utilizador_id=%s) SELECT * from item_encomenda WHERE produto_id=%s and encomenda_id IN(SELECT id from user_orders)"
    values = (auth_payload["auth_id"], product_id)
    cur.execute(statement, values)
    # if it returns anything continue
    if (cur.fetchall()) == []:
        response = {
            "status": StatusCodes["api_error"],
            "results": "user must have bought the item before to review it",
        }
        return flask.jsonify(response)

    # store the rating
    # parameterized queries, good for security and performance
    statement = (
        "INSERT INTO rating (classificacao,comentario, comprador_utilizador_id, produto_id) VALUES (%s,%s, %s, %s)"
    )
    values = (payload["rating"], payload["comment"], auth_payload["auth_id"], product_id)

    try:
        cur.execute(statement, values)

        response = {"status": StatusCodes["success"], "results": "rating registered"}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##########################################################
## DEIXAR COMENTÁRIO/PERGUNTA
##########################################################

## Criar thread/fazer pergunta-POST
##-----------------------------------------------
@app.route("/dbproj/questions/<product_id>", methods=["POST"])
def criar_thread(product_id):
    logger.info("POST /dbproj/questions/<product_id>")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /dbproj/questions/<product_id> - payload: {payload}")

    # check if product exists
    statement = "SELECT * FROM produto WHERE id=%s"
    values = (product_id,)
    cur.execute(statement, values)
    if cur.fetchall() == []:
        response = {
            "status": StatusCodes["api_error"],
            "results": "product with chosen id does not exist",
        }
        return flask.jsonify(response)

    # do not forget to validate every argument, e.g.,:
    if "question" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "rating value is required to leave a review",
        }
        return flask.jsonify(response)

    if "token" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "token is required to make an order",
        }
        return flask.jsonify(response)

    auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")

    # check if current user is a buyer
    if auth_payload["auth_role"] != "comprador":
        response = {
            "status": StatusCodes["api_error"],
            "results": "role must be comprador to create a thread",
        }
        return flask.jsonify(response)

    # create thread
    statement1 = "INSERT INTO thread(id,produto_id) VALUES(DEFAULT,%s) RETURNING ID"
    values1 = (product_id,)

    # create main question for new thread
    statement2 = "INSERT INTO pergunta_resposta(id,username,texto,questao_pai_id,thread_id) VALUES(DEFAULT,%s,%s,NULL,%s) RETURNING id"

    try:
        cur.execute(statement1, values1)
        thread_id = cur.fetchone()[0]

        values2 = (auth_payload["auth_user"], payload["question"], thread_id)
        cur.execute(statement2, values2)
        question_id = cur.fetchone()[0]

        response = {"status": StatusCodes["success"], "results": f"{question_id}"}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


# POR TESTAR!!!!
## Responder a pergunta existente-POST
##-----------------------------------------------
@app.route("/dbproj/questions/<product_id>/<parent_question_id>", methods=["POST"])
def responder_a_thread(product_id, parent_question_id):
    logger.info("POST /dbproj/questions/<product_id>/<parent_question_id>")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /dbproj/questions/<product_id>/<parent_question_id> - payload: {payload}")

    # check if product exists
    statement = "SELECT * FROM produto WHERE id=%s"
    values = (product_id,)
    cur.execute(statement, values)
    if cur.fetchall() == []:
        response = {
            "status": StatusCodes["api_error"],
            "results": "product with chosen id does not exist",
        }
        return flask.jsonify(response)

    # check if parent question exists
    statement = "SELECT thread_id FROM pergunta_resposta WHERE id=%s"
    values = (parent_question_id,)
    cur.execute(statement, values)
    thread_id = cur.fetchone()[0]
    # if not leave
    if thread_id == None:
        response = {
            "status": StatusCodes["api_error"],
            "results": "parent question with chosen id does not exist",
        }
        return flask.jsonify(response)

    # if exists check if it is related to the request product id
    statement = "SELECT produto_id FROM thread WHERE id=%s"
    values = (thread_id,)
    parent_question_product_id = cur.fetchone()[0]

    if parent_question_product_id != product_id:
        response = {
            "status": StatusCodes["api_error"],
            "results": "parent question with chosen id does not talk about the product with chosen id",
        }
        return flask.jsonify(response)

    # check

    # do not forget to validate every argument, e.g.,:
    if "question" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "rating value is required to leave a review",
        }
        return flask.jsonify(response)

    if "token" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "token is required to make an order",
        }
        return flask.jsonify(response)

    auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")

    # check if current user is a buyer,admin or seller of the current chosen product
    if auth_payload["auth_role"] == "vendedor":
        statement = "SELECT vendedor_utilizador_id from produto WHERE id=%s"
        values = (product_id,)
        cur.execute(statement, values)
        seller_id = cur.fetchone()[0]
        if seller_id != auth_payload["auth_id"]:
            response = {
                "status": StatusCodes["api_error"],
                "results": "sellers are not allowed to comment on other seller's products",
            }
            return flask.jsonify(response)

    # create response
    statement = "INSERT INTO pergunta_resposta(id,username,texto,questao_pai_id,thread_id) VALUES(DEFAULT,%s,%s,%s)"
    values = (auth_payload["auth_user"], payload["question"], parent_question_id, thread_id)

    try:
        cur.execute(statement, values)
        question_id = cur.fetchone()[0]
        response = {"status": StatusCodes["success"], "results": f"{question_id}"}

        # commit the transaction
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##########################################################
## ESTATÍSTICAS
##########################################################
##FALTA A PARTE DO SELECT PARA SABER COMO É A DATA#
## Obter estatísticas (por mes) dos ultimos 12 meses-GET
##-----------------------------------------------
@app.route("/proj/report/year", methods=["GET"])
def obter_estat():
    logger.info("GET /proj/report/year")

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT ")
        rows = cur.fetchall()

        logger.debug("GET /proj/report/year - parse")
        Results = []
        for row in rows:
            logger.debug(row)
            content = {"mes": row[0], "valor": row[1], "total_vendas": row[2]}
            Results.append(content)  # appending to the payload to be returned

        response = {"status": StatusCodes["success"], "results": Results}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"GET /proj/report/year - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##########################################################
## MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs//log_file.log")
    logger = logging.getLogger("logger")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter("%(asctime)s [%(levelname)s]:  %(message)s", "%H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    time.sleep(1)  # just to let the DB start before this print :-)

    logger.info(
        "\n---------------------------------------------------------------\n"
        + "API v1.1 online: http://localhost:8080/\n\n"
    )

    app.run(host="0.0.0.0", debug=True, threaded=True)
