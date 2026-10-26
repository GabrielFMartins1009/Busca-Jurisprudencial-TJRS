"""Regera TODOS os embeddings da vec_decisoes com vetores normalizados (norma 1).

Com vetores normalizados, o ranking por distancia L2 e equivalente ao ranking por
similaridade de cosseno. Rode com o servidor (uvicorn) PARADO:
    py -3.11 regerar_embeddings.py

O banco so e alterado depois que todos os embeddings foram calculados, e a troca
acontece em uma unica transacao (se der erro, nada muda).
"""
import sqlite3
import sqlite_vec
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Dispositivo: {device}")
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased', device=device)

conn = sqlite3.connect("jurisprudencia.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
cur = conn.cursor()

rows = cur.execute("SELECT id, ementa_completa FROM decisoes ORDER BY id").fetchall()
ids = [r[0] for r in rows]
ementas = [r[1] or "" for r in rows]
print(f"Decisoes a processar: {len(ids)}")

embeddings = model.encode(
    ementas, batch_size=32, normalize_embeddings=True, show_progress_bar=True
).astype(np.float32)

normas = np.linalg.norm(embeddings, axis=1)
print(f"Norma dos vetores: min={normas.min():.4f} max={normas.max():.4f}")

print("Gravando no banco...")
cur.execute("DELETE FROM vec_decisoes")
cur.executemany(
    "INSERT INTO vec_decisoes(decisao_id, embedding) VALUES (?, ?)",
    [(i, e.tobytes()) for i, e in zip(ids, embeddings)],
)
conn.commit()

total_dec = cur.execute("SELECT COUNT(*) FROM decisoes").fetchone()[0]
total_vec = cur.execute("SELECT COUNT(*) FROM vec_decisoes").fetchone()[0]
print(f"decisoes: {total_dec} | vec_decisoes: {total_vec}")

amostra = cur.execute("SELECT embedding FROM vec_decisoes LIMIT 3").fetchall()
for (b,) in amostra:
    print("Norma na amostra do banco:", round(float(np.linalg.norm(np.frombuffer(b, dtype=np.float32))), 4))
conn.close()
print("Concluido.")
