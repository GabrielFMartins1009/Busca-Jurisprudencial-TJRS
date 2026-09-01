from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import sqlite_vec
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased', device=device)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ConsultaRequest(BaseModel):
    consulta: str
    top_k: int = 5

class RefinamentoRequest(BaseModel):
    consulta: str
    resposta1: str
    resposta2: str
    top_k: int = 5

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
    except Exception:
        return []

def rrf(resultados_semanticos, resultados_lexicos, k=60):
    scores = {}
    metadados = {}

    for posicao, row in enumerate(resultados_semanticos):
        doc_id = row[0]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + posicao + 1)
        metadados[doc_id] = row[1:7]

    for posicao, row in enumerate(resultados_lexicos):
        doc_id = row[0]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + posicao + 1)
        metadados[doc_id] = row[1:7]

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranking, metadados

def executar_busca(consulta, top_k):
    conn = conectar_banco()
    cursor = conn.cursor()
    sem = busca_semantica(cursor, consulta, top_k=20)
    lex = busca_lexica(cursor, consulta, top_k=20)
    conn.close()

    ranking, metadados = rrf(sem, lex)

    resultados = []
    for doc_id, score in ranking[:top_k]:
        numero, ementa, relator, data, assunto, url = metadados[doc_id]
        resultados.append({
            "numero_processo": numero,
            "ementa": ementa[:500],
            "relator": relator,
            "data_julgamento": data,
            "assunto": assunto,
            "url": url,
            "score_rrf": round(score, 6)
        })
    return resultados

@app.get("/")
def root():
    return {"status": "ok", "mensagem": "API de busca jurisprudencial"}

@app.post("/buscar")
def buscar(request: ConsultaRequest):
    resultados = executar_busca(request.consulta, request.top_k)
    return {
        "consulta": request.consulta,
        "total_resultados": len(resultados),
        "resultados": resultados
    }

@app.post("/refinar")
def refinar(request: ConsultaRequest):
    mensagem = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Você é um assistente especializado em direito brasileiro.
Um profissional do direito fez a seguinte consulta jurisprudencial: "{request.consulta}"

Formule exatamente 2 perguntas curtas e objetivas para refinar o contexto dessa consulta.
As perguntas devem ajudar a identificar o tipo de decisão mais relevante para esse profissional.

Responda APENAS com as 2 perguntas, numeradas, sem explicações adicionais."""
            }
        ]
    )

    perguntas_texto = mensagem.content[0].text
    perguntas = [p.strip() for p in perguntas_texto.strip().split('\n') if p.strip()]

    return {
        "consulta": request.consulta,
        "perguntas": perguntas
    }

@app.post("/buscar_refinado")
def buscar_refinado(request: RefinamentoRequest):
    mensagem = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""Você é um assistente especializado em direito brasileiro.
Um profissional do direito fez a seguinte consulta jurisprudencial: "{request.consulta}"

Para refinar a busca, ele respondeu às seguintes perguntas:
Resposta 1: {request.resposta1}
Resposta 2: {request.resposta2}

Com base na consulta original e nas respostas, reformule a consulta em UMA única frase descritiva em linguagem natural, adequada para busca semântica em jurisprudência.

Responda APENAS com a frase reformulada, sem explicações."""
            }
        ]
    )

    consulta_reformulada = mensagem.content[0].text.strip()
    resultados = executar_busca(consulta_reformulada, request.top_k)

    return {
        "consulta_original": request.consulta,
        "consulta_reformulada": consulta_reformulada,
        "total_resultados": len(resultados),
        "resultados": resultados
    }