import sqlite3
import sqlite_vec

def conectar_banco():
    conn = sqlite3.connect("jurisprudencia.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

conn = conectar_banco()
cursor = conn.cursor()

# Cria tabela virtual FTS5 com as ementas
cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_decisoes USING fts5(
        numero_processo,
        ementa_completa,
        content='decisoes',
        content_rowid='id'
    )
""")

# Popula com os dados existentes
cursor.execute("""
    INSERT INTO fts_decisoes(rowid, numero_processo, ementa_completa)
    SELECT id, numero_processo, ementa_completa FROM decisoes
""")

conn.commit()
conn.close()
print("Tabela FTS5 criada e populada com sucesso!")