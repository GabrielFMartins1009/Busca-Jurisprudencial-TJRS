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

# Cria a tabela virtual de vetores (se ainda não existir)
cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS vec_decisoes USING vec0(
        decisao_id INTEGER PRIMARY KEY,
        embedding float[768]
    )
""")

# Busca todos os registros que têm embedding salvo
cursor.execute("SELECT id, embedding FROM decisoes WHERE embedding IS NOT NULL")
registros = cursor.fetchall()

inseridos = 0
for decisao_id, embedding_blob in registros:
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO vec_decisoes(decisao_id, embedding) VALUES (?, ?)",
            (decisao_id, embedding_blob)
        )
        inseridos += 1
    except Exception as e:
        print(f"Erro no id {decisao_id}: {e}")

conn.commit()
conn.close()
print(f"Migração concluída: {inseridos} vetores inseridos na vec_decisoes")