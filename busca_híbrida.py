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

def busca_semantica(cursor, consulta, top_k=20):
    embedding = model.encode(consulta).astype(np.float32).tobytes()
    cursor.execute("""
        SELECT d.id, d.numero_processo, d.ementa_completa, d.nome_relator,
               d.data_julgamento, d.nome_assunto_cnj, d.url, v.distance
        FROM vec_decisoes v
        JOIN decisoes d ON d.id = v.decisao_id
        WHERE v.embedding MATCH ?
        AND k = ?
        ORDER BY v.distance ASC
    """, (embedding, top_k))
    return cursor.fetchall()

def busca_lexica(cursor, consulta, top_k=20):
    try:
        cursor.execute("""
            SELECT d.id, d.numero_processo, d.ementa_completa, d.nome_relator,
                   d.data_julgamento, d.nome_assunto_cnj, d.url,
                   bm25(fts_decisoes) AS score
            FROM fts_decisoes
            JOIN decisoes d ON d.id = fts_decisoes.rowid
            WHERE fts_decisoes MATCH ?
            ORDER BY score ASC
            LIMIT ?
        """, (consulta, top_k))
        return cursor.fetchall()
    except Exception as e:
        print(f"ERRO LÉXICA: {e}")
        return []

def rrf(resultados_semanticos, resultados_lexicos, k=60):
    scores = {}
    metadados = {}

    # Posições da busca semântica
    for posicao, row in enumerate(resultados_semanticos):
        doc_id = row[0]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + posicao + 1)
        metadados[doc_id] = row[1:7]  # numero, ementa, relator, data, assunto, url

    # Posições da busca léxica
    for posicao, row in enumerate(resultados_lexicos):
        doc_id = row[0]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + posicao + 1)
        metadados[doc_id] = row[1:7]

    # Ordena por score RRF decrescente
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranking, metadados

def busca_hibrida(consulta, top_k=5):
    conn = conectar_banco()
    cursor = conn.cursor()

    sem = busca_semantica(cursor, consulta, top_k=20)
    lex = busca_lexica(cursor, consulta, top_k=20)
    conn.close()

    print(f"Semântica: {len(sem)} resultados")
    print(f"Léxica: {len(lex)} resultados")
    print(f"Ranking total: {len(rrf(sem, lex)[0])} itens")

    if not sem and not lex:
        print("PROBLEMA: as duas buscas retornaram vazio.")
        return

    ranking, metadados = rrf(sem, lex)

    for i, (doc_id, score) in enumerate(ranking[:top_k], 1):
        numero, ementa, relator, data, assunto, url = metadados[doc_id]
        print(f"--- Resultado {i} ---")
        print(f"Processo  : {numero}")
        print(f"Relator   : {relator}")
        print(f"Data      : {data}")
        print(f"Assunto   : {assunto}")
        print(f"Score RRF : {score:.6f}")
        print(f"URL       : {url}")
        print(f"Ementa    : {ementa[:200]}...")
        print()

busca_hibrida("acidente de trânsito indenização danos morais veículo")