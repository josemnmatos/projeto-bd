import flask
import logging, psycopg2, time


app = flask.Flask(__name__)

StatusCodes = {"success": 200, "api_error": 400, "internal_error": 500}

##########################################################
## DATABASE ACCESS
##########################################################


def db_connection():
    db = psycopg2.connect(user="dev", password="password", host="db", port="5432", database="dbprojeto")

    return db


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

    # parameterized queries, good for security and performance

    statement = "INSERT INTO utilizador (id, username, email, password) VALUES (DEFAULT, %s, %s,%s) RETURNING id"
    values = (payload["username"], payload["email"], payload["password"])

    try:
        cur.execute(statement, values)
        ret_id = cur.fetchone()[0]

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
def autentica_user():
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
    statement = "SELECT password from utilizador WHERE username=%s"
    req_username = payload["username"]
    req_password = payload["password"]

    try:
        res = cur.execute(statement, (req_username,))  # postgres apenas aceita tuplo
        if cur.fetchall()[0][0] == str(req_password):  # passwords match
            response = {"status": StatusCodes["success"], "results": f"User logged in: {req_username}"}
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
def get_all_departments():
    logger.info("GET /dbproj/product")

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, descricao, preco,stock FROM produto")
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

    # parameterized queries, good for security and performance
    statement = "INSERT INTO produto (id, descricao, preco, stock) VALUES (DEFAULT, %s, %s,%s)"
    values = (payload["descricao"], float(payload["preco"]), int(payload["stock"]))

    try:
        cur.execute(statement, values)
        ret_id = cur.fetchone()[0]
        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f"{ret_id}"}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"POST /products - error: {error}")
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

        # parameterized queries, good for security and performance
        # atualiza descricao
    statement = "UPDATE produto SET descricao = %s, preco = %s, stock = %s WHERE id = %s"
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


## Consultar informacao generica de um produto
##-----------------------------------------------

##########################################################
## COMPRA
##########################################################

## Efetuar compra
##-----------------------------------------------

##########################################################
## DEIXAR RATING/FEEDBACK
##########################################################

## Ver ratings de um produto(para teste)
##-----------------------------------------------

## Deixar rating a produto comprado
##-----------------------------------------------

##########################################################
## DEIXAR COMENTÁRIO/PERGUNTA
##########################################################

## Criar thread/fazer pergunta
##-----------------------------------------------

## Responder a pergunta existente
##-----------------------------------------------

##########################################################
## ESTATÍSTICAS
##########################################################

## Obter estatísticas (por mes) dos ultimos 12 meses
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
