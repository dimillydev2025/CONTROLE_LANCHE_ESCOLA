import logging
import os

import mysql.connector
from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from mysql.connector import Error, IntegrityError

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": "controle_lanche",
}

app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/static/<path:filename>", endpoint="static")
def template_static_file(filename):
    if filename != "script.js":
        abort(404)
    return send_from_directory(app.template_folder, filename)


@app.post("/verificar_qr")
def verificar_qr():
    payload = request.get_json(silent=True)
    id_aluno = payload.get("id_aluno") if isinstance(payload, dict) else None

    if (
        isinstance(id_aluno, bool)
        or not isinstance(id_aluno, (str, int))
        or not str(id_aluno).strip()
    ):
        return jsonify(
            status="erro",
            mensagem="Informe um id_aluno válido.",
        ), 400

    id_aluno = str(id_aluno).strip()
    conexao = None
    cursor = None

    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM historico_lanches
            WHERE id_aluno = %s AND data_lanche = CURDATE()
            LIMIT 1
            """,
            (id_aluno,),
        )

        if cursor.fetchone():
            return jsonify(
                status="bloqueado",
                mensagem=f"O aluno com ID {id_aluno} já recebeu lanche hoje.",
            )

        cursor.execute(
            """
            INSERT INTO historico_lanches (id_aluno, data_lanche)
            VALUES (%s, CURDATE())
            """,
            (id_aluno,),
        )
        conexao.commit()
        return jsonify(
            status="sucesso",
            mensagem=f"Lanche liberado para o aluno com ID {id_aluno}.",
        )
    except IntegrityError as erro:
        if conexao is not None:
            conexao.rollback()
        if erro.errno == 1062:
            return jsonify(
                status="bloqueado",
                mensagem=f"O aluno com ID {id_aluno} já recebeu lanche hoje.",
            )
        logging.exception("Erro de integridade ao registrar o lanche.")
        return jsonify(status="erro", mensagem="Não foi possível registrar o lanche."), 500
    except Error:
        if conexao is not None:
            conexao.rollback()
        logging.exception("Erro ao acessar o banco de dados.")
        return jsonify(status="erro", mensagem="Não foi possível acessar o banco de dados."), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None and conexao.is_connected():
            conexao.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
