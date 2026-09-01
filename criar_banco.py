import sqlite3
import sqlite_vec

# Cria o banco de dados (arquivo jurisprudencia.db)
conn = sqlite3.connect("jurisprudencia.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

cursor = conn.cursor()

# Cria a tabela de decisões
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
""")

conn.commit()
conn.close()
print("Banco criado com sucesso!")