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


@app.route("/")
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

## Criar novo user
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
    
    statement = "INSERT INTO utilizador (id, username, email, password) VALUES (DEFAULT, %s, %s,%s)"
    values = (payload["username"], payload["email"], payload["password"])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f'Created new user {payload["username"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"POST /user - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Autenticar user
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

        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f'Inserted new product {payload["descricao"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"POST /products - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


## Atualizar produto existente
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
        response = {"status": StatusCodes["success"], "results": f"Updated: product with id: {product_id}"}

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
## COMPRA
##########################################################


##########################################################
## DEIXAR RATING/FEEDBACK
##########################################################

##########################################################
## DEIXAR COMENTÁRIO/PERGUNTA
##########################################################

##########################################################
## ESTATÍSTICAS
##########################################################

"""

##
## Demo GET
##
## Obtain all departments in JSON format
##
## To use it, access:
##
## http://localhost:8080/departments/
##


@app.route("/departments/", methods=["GET"])
def get_all_departments():
    logger.info("GET /departments")

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT ndep, nome, local FROM dep")
        rows = cur.fetchall()

        logger.debug("GET /departments - parse")
        Results = []
        for row in rows:
            logger.debug(row)
            content = {"ndep": int(row[0]), "nome": row[1], "localidade": row[2]}
            Results.append(content)  # appending to the payload to be returned

        response = {"status": StatusCodes["success"], "results": Results}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"GET /departments - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##
## Demo GET
##
## Obtain department with ndep <ndep>
##
## To use it, access:
##
## http://localhost:8080/departments/10
##


@app.route("/dbproj/product/<product_id>/", methods=["GET"])
def get_department(ndep):
    logger.info("GET /dbproj/product/<product_id>")

    logger.debug(f"ndep: {ndep}")

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT ndep, nome, local FROM dep where ndep = %s", (ndep,))
        rows = cur.fetchall()

        row = rows[0]

        logger.debug("GET /dbproj/product/<product_id> - parse")
        logger.debug(row)
        content = {"ndep": int(row[0]), "nome": row[1], "localidade": row[2]}

        response = {"status": StatusCodes["success"], "results": content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"GET /dbproj/product/<product_id> - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##
## Demo POST
##
## Add a new department in a JSON payload
##
## To use it, you need to use postman or curl:
##
## curl -X POST http://localhost:8080/departments/ -H 'Content-Type: application/json' -d '{'localidade': 'Polo II', 'ndep': 69, 'nome': 'Seguranca'}'
##


@app.route("/departments/", methods=["POST"])
def add_departments():
    logger.info("POST /departments")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"POST /departments - payload: {payload}")

    # do not forget to validate every argument, e.g.,:
    if "ndep" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "ndep value not in payload"}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = "INSERT INTO dep (ndep, nome, local) VALUES (%s, %s, %s)"
    values = (payload["ndep"], payload["localidade"], payload["nome"])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {"status": StatusCodes["success"], "results": f'Inserted dep {payload["ndep"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"POST /departments - error: {error}")
        response = {"status": StatusCodes["internal_error"], "errors": str(error)}

        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


##
## Demo PUT
##
## Update a department based on a JSON payload
##
## To use it, you need to use postman or curl:
##
## curl -X PUT http://localhost:8080/departments/ -H 'Content-Type: application/json' -d '{'ndep': 69, 'localidade': 'Porto'}'
##


@app.route("/dbproj/product/<product_id>", methods=["PUT"])
def update_departments(ndep):
    logger.info("PUT /dbproj/product/<product_id>")
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f"PUT /dbproj/product/<product_id> - payload: {payload}")

    # do not forget to validate every argument, e.g.,:
    if "localidade" not in payload:
        response = {"status": StatusCodes["api_error"], "results": "localidade is required to update"}
        return flask.jsonify(response)

    # parameterized queries, good for security and performance
    statement = "UPDATE dep SET local = %s WHERE ndep = %s"
    values = (payload["localidade"], ndep)

    try:
        res = cur.execute(statement, values)
        response = {"status": StatusCodes["success"], "results": f"Updated: {cur.rowcount}"}

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

"""


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
