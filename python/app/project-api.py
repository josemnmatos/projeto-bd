import flask
import logging, psycopg2, time
import jwt
from datetime import date

jwt_secret = "bdprojeto"

app = flask.Flask(__name__)

StatusCodes = {"success": 200, "api_error": 400, "internal_error": 500}

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
        cur.execute("SELECT id, descricao, preco,stock FROM produto ORDER BY id")
        rows = cur.fetchall()

        logger.debug("GET /dbproj/product - parse")
        Results = []
        for row in rows:
            logger.debug(row)
            content = {"id": int(row[0]), "descricao": row[1], "preco": row[2], "stock": row[3]}
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
    if "descricao" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "descricao value not in payload"}
        return flask.jsonify(response)

    if "preco" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "preco value not in payload"}
        return flask.jsonify(response)

    if "stock" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "stock value not in payload"}
        return flask.jsonify(response)

    if "token" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "token value not in payload"}
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
    statement = "INSERT INTO produto (id, descricao, preco, stock, vendedor_utilizador_id) VALUES (DEFAULT, %s, %s,%s,%s) RETURNING id"
    values = (payload["descricao"], float(payload["preco"]), int(payload["stock"]), auth_token["auth_id"])

    try:
        # executa e retorna id para adicionar ao produto
        cur.execute(statement, values)
        ret_id = cur.fetchone()[0]
        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f"{ret_id}"}

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

    # do not forget to validate every argument, e.g.,:
    if "descricao" not in payload or "preco" not in payload or "stock" not in payload:
        response = {
            "status": StatusCodes["api_error"],
            "results": "descricao,preco and stock are required to update",
        }
        return flask.jsonify(response)

    if "token" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "token value not in payload"}
        return flask.jsonify(response)

    # para verificar se user ativo é o vendedor do produto a atualizar
    auth_payload = jwt.decode(payload["token"], jwt_secret, algorithms="HS256")

    # parameterized queries, good for security and performance
    # atualiza descricao
    statement = (
        "UPDATE produto SET descricao = %s, preco = %s, stock = %s WHERE id = %s RETURNING vendedor_utilizador_id"
    )
    values = (payload["descricao"], payload["preco"], payload["stock"], product_id)

    try:
        cur.execute(statement, values)

        # vendedor não corresponde ao user atual
        seller_id = cur.fetchone()

        if seller_id is None:
            response = {"status": StatusCodes["api_error"], "results": "product with chosen id does not exist"}
            conn.rollback()
            return flask.jsonify(response)

        if seller_id[0] != auth_payload["auth_id"]:
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
##-----------------------------------------------

##########################################################
## COMPRA
##########################################################

## Efetuar compra-PUT
##-----------------------------------------------
@app.route("/dbproj/order/", methods=["POST"])
def efetuar_compra(product_id):
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

    # verify cart input
    for order_item in payload["cart"]:
        product_id = order_item[0]
        order_quantity = order_item[1]
        if isinstance(product_id, int) == 0 or isinstance(order_quantity, int) == 0:
            response = {
                "status": StatusCodes["api_error"],
                "results": "cart format not valid",
            }
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = "INSERT INTO encomenda (id, data, preco, stock) VALUES (DEFAULT, %s, %s,%s) RETURNING id"
    values = (payload["descricao"], payload["preco"], payload["stock"], product_id)

    try:
        res = cur.execute(statement, values)
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


##########################################################
## DEIXAR RATING/FEEDBACK
##########################################################

## Ver ratings de um produto(para teste)-GET
##-----------------------------------------------

## Deixar rating a produto comprado-PUT
##-----------------------------------------------


##########################################################
## DEIXAR COMENTÁRIO/PERGUNTA
##########################################################

## Criar thread/fazer pergunta-POST
##-----------------------------------------------

## Responder a pergunta existente-POST
##-----------------------------------------------

##########################################################
## ESTATÍSTICAS
##########################################################

## Obter estatísticas (por mes) dos ultimos 12 meses-GET
##-----------------------------------------------


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
