import sqlite3

def conectar():

    conn = sqlite3.connect("destinatarios.db")

    return conn


def criar_tabela():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS destinatarios (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT NOT NULL,

        setor TEXT NOT NULL,

        whatsapp TEXT NOT NULL

    )

    """)

    conn.commit()

    conn.close()


def listar():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM destinatarios ORDER BY nome")

    dados = cursor.fetchall()

    conn.close()

    return dados


def listar_por_setor(setor):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM destinatarios WHERE setor=?",
        (setor,)
    )

    dados = cursor.fetchall()

    conn.close()

    return dados


def inserir(nome,setor,whatsapp):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO destinatarios (nome,setor,whatsapp)

    VALUES (?,?,?)

    """,(nome,setor,whatsapp))

    conn.commit()

    conn.close()


def excluir(id):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM destinatarios WHERE id=?",
        (id,)
    )

    conn.commit()

    conn.close()


def buscar(id):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM destinatarios WHERE id=?",
        (id,)
    )

    dado = cursor.fetchone()

    conn.close()

    return dado


def atualizar(id,nome,setor,whatsapp):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE destinatarios

    SET nome=?, setor=?, whatsapp=?

    WHERE id=?

    """,(nome,setor,whatsapp,id))

    conn.commit()

    conn.close()