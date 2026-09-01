import sqlite3
import sqlite_vec

def conectar_banco():
    conn = sqlite3.connect("jurisprudencia.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn

def buscar_lexica(consulta, top_k=5):
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
            bm25(fts_decisoes) AS score
        FROM fts_decisoes
        JOIN decisoes d ON d.id = fts_decisoes.rowid
        WHERE fts_decisoes MATCH ?
        ORDER BY score ASC
        LIMIT ?
    """, (consulta, top_k))

    resultados = cursor.fetchall()
    conn.close()
    return resultados

# Teste
consulta = "vício oculto veículo"
print(f"Buscando: '{consulta}'\n")

resultados = buscar_lexica(consulta)

if not resultados:
    print("Nenhum resultado encontrado.")
else:
    for i, r in enumerate(resultados, 1):
        numero, ementa, relator, data, assunto, url, score = r
        print(f"--- Resultado {i} ---")
        print(f"Processo : {numero}")
        print(f"Relator  : {relator}")
        print(f"Data     : {data}")
        print(f"Assunto  : {assunto}")
        print(f"Score BM25: {score:.4f}")
        print(f"URL      : {url}")
        print(f"Ementa   : {ementa[:200]}...")
        print()