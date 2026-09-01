import requests
import sqlite3
import sqlite_vec
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
import time

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Usando: {device}")
print("Carregando modelo de embeddings...")
model = SentenceTransformer('neuralmind/bert-base-portuguese-cased', device=device)
print("Modelo carregado!\n")

def conectar_banco():
    conn = sqlite3.connect("jurisprudencia.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

def buscar_e_salvar(termo, paginas=1):
    conn = conectar_banco()
    cursor = conn.cursor()

    total_salvas = 0
    total_duplicadas = 0

    for pagina in range(paginas):
        print(f"Buscando página {pagina+1} para '{termo}'...")

        url = "https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php"

        parametros = (
            f"aba=jurisprudencia&realizando_pesquisa=1&pagina_atual={pagina+1}"
            f"&q_palavra_chave={termo}&conteudo_busca=ementa_completa"
            f"&filtroComAExpressao=&filtroComQualquerPalavra=&filtroSemAsPalavras="
            f"&filtroTribunal=-1&filtroRelator=-1&filtroOrgaoJulgador=-1"
            f"&filtroTipoProcesso=-1&filtroClasseCnj=-1&assuntoCnj=-1"
            f"&data_julgamento_de=01/01/2010&data_julgamento_ate=&filtroNumeroProcesso="
            f"&data_publicacao_de=&data_publicacao_ate="
            f"&facet=on&facet.sort=index&facet.limit=index&wt=json&ordem=desc&start={pagina*10}"
        )

        data = {
            "action": "consultas_solr_ajax",
            "metodo": "buscar_resultados",
            "parametros": parametros
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.tjrs.jus.br/novo/buscas-solr/"
        }

        resposta = requests.post(url, data=data, headers=headers)
        docs = resposta.json().get("response", {}).get("docs", [])

        for doc in docs:
            numero = doc.get("numero_processo", "")
            ementa = doc.get("ementa_completa", [""])[0] if doc.get("ementa_completa") else ""
            url_processo = f"https://www.tjrs.jus.br/novo/buscas-solr/?aba=jurisprudencia&q={numero}"

            embedding = model.encode(ementa).astype(np.float32)
            embedding_bytes = embedding.tobytes()

            try:
                # 1. Insere na tabela principal
                cursor.execute("""
                    INSERT INTO decisoes 
                    (numero_processo, ementa_completa, nome_relator, orgao_julgador,
                     data_julgamento, data_publicacao, nome_assunto_cnj, 
                     tipo_processo, nome_tribunal, secao, url, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    numero,
                    ementa,
                    doc.get("nome_relator", ""),
                    doc.get("orgao_julgador", ""),
                    doc.get("data_julgamento", ""),
                    doc.get("data_publicacao", ""),
                    doc.get("nome_assunto_cnj", ""),
                    doc.get("tipo_processo", ""),
                    doc.get("nome_tribunal", ""),
                    doc.get("secao", ""),
                    url_processo,
                    embedding_bytes
                ))

                # Pega o id da decisão recém inserida
                decisao_id = cursor.lastrowid

                # 2. Insere na vec_decisoes
                cursor.execute(
                    "INSERT OR IGNORE INTO vec_decisoes(decisao_id, embedding) VALUES (?, ?)",
                    (decisao_id, embedding_bytes)
                )

                # 3. Insere na fts_decisoes
                cursor.execute(
                    "INSERT INTO fts_decisoes(rowid, numero_processo, ementa_completa) VALUES (?, ?, ?)",
                    (decisao_id, numero, ementa)
                )

                total_salvas += 1
                print(f"  Salva: {numero}")

            except sqlite3.IntegrityError:
                total_duplicadas += 1

        conn.commit()
        time.sleep(2)

    conn.close()
    print(f"\nConcluído: {total_salvas} salvas, {total_duplicadas} duplicadas ignoradas")

buscar_e_salvar("rescisão+contratual", paginas=2)