import sqlite3
import sqlite_vec
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased', device=device)

def conectar_banco():
    conn = sqlite3.connect("jurisprudencia.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

def buscar(consulta, top_k=5):
    # Gera embedding da consulta
    embedding = model.encode(consulta).astype(np.float32).tobytes()

    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            d.numero_processo,
            d.ementa_completa,
            d.nome_relator,
            d.data_julgamento,
            d.nome_assunto_cnj,
            d.url,
            v.distance
        FROM vec_decisoes v
        JOIN decisoes d ON d.id = v.decisao_id
        WHERE v.embedding MATCH ?
        AND k = ?
        ORDER BY v.distance ASC
    """, (embedding, top_k))

    resultados = cursor.fetchall()
    conn.close()
    return resultados

# Teste
consulta = "comprei um veículo usado com defeito que não foi informado pelo vendedor"
print(f"Buscando: '{consulta}'\n")

resultados = buscar(consulta)

for i, r in enumerate(resultados, 1):
    numero, ementa, relator, data, assunto, url, distance = r
    print(f"--- Resultado {i} ---")
    print(f"Processo : {numero}")
    print(f"Relator  : {relator}")
    print(f"Data     : {data}")
    print(f"Assunto  : {assunto}")
    print(f"Distância: {distance:.4f}")
    print(f"URL      : {url}")
    print(f"Ementa   : {ementa[:200]}...")
    print()