"""Cria o banco jurisprudencia.db com as tres estruturas usadas pelo sistema:

- decisoes:     tabela relacional (fonte unica dos dados)
- vec_decisoes: indice vetorial sqlite-vec (embeddings BERTimbau, 768 dimensoes)
- fts_decisoes: indice lexico FTS5 (BM25), ligado a tabela decisoes

Nao apaga nada: usa CREATE ... IF NOT EXISTS, entao e seguro rodar sobre um banco ja existente.
Uso: py -3.11 criar_banco.py
"""
import sqlite3
import sqlite_vec

conn = sqlite3.connect("jurisprudencia.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

cursor = conn.cursor()

cursor.executescript("""
    CREATE TABLE IF NOT EXISTS decisoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_processo TEXT UNIQUE,
        ementa_completa TEXT,
        nome_relator TEXT,
        orgao_julgador TEXT,
        data_julgamento TEXT,
        data_publicacao TEXT,
        nome_assunto_cnj TEXT,
        tipo_processo TEXT,
        nome_tribunal TEXT,
        secao TEXT,
        url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS vec_decisoes USING vec0(
        decisao_id INTEGER PRIMARY KEY,
        embedding float[768]
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS fts_decisoes USING fts5(
        numero_processo,
        ementa_completa,
        content='decisoes',
        content_rowid='id'
    );
""")

conn.commit()
conn.close()
print("Banco criado com sucesso!")
