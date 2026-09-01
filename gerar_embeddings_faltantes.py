import sqlite3
import sqlite_vec
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando: {device}")
print("Carregando modelo...")
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased', device=device)
print("Modelo carregado!\n")

def conectar_banco():
    conn = sqlite3.connect("jurisprudencia.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

conn = conectar_banco()
cursor = conn.cursor()

# Busca só as decisões sem embedding
cursor.execute("SELECT id, ementa_completa FROM decisoes WHERE embedding IS NULL")
registros = cursor.fetchall()
print(f"Decisões sem embedding: {len(registros)}")

# Separa ids e textos
ids = [r[0] for r in registros]
ementas = [r[1] if r[1] else "" for r in registros]

# Gera todos os embeddings de uma vez na GPU (batch)
print("Gerando embeddings em batch...")
embeddings = model.encode(ementas, batch_size=32, show_progress_bar=True)

# Salva no banco
atualizados = 0
for decisao_id, embedding in zip(ids, embeddings):
    embedding_bytes = embedding.astype(np.float32).tobytes()
    cursor.execute(
        "UPDATE decisoes SET embedding = ? WHERE id = ?",
        (embedding_bytes, decisao_id)
    )
    # Insere também na vec_decisoes
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO vec_decisoes(decisao_id, embedding) VALUES (?, ?)",
            (decisao_id, embedding_bytes)
        )
    except Exception as e:
        print(f"Erro vec_decisoes id {decisao_id}: {e}")
    atualizados += 1

conn.commit()
conn.close()
print(f"\nConcluído: {atualizados} embeddings gerados e salvos")