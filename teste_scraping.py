import requests

def buscar_tjrs(termo, pagina=0):
    url = "https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php"
    
    parametros = (
        f"aba=jurisprudencia&realizando_pesquisa=1&pagina_atual={pagina+1}"
        f"&q_palavra_chave={termo}&conteudo_busca=ementa_completa"
        f"&filtroComAExpressao=&filtroComQualquerPalavra=&filtroSemAsPalavras="
        f"&filtroTribunal=-1&filtroRelator=-1&filtroOrgaoJulgador=-1"
        f"&filtroTipoProcesso=-1&filtroClasseCnj=-1&assuntoCnj=-1"
        f"&data_julgamento_de=&data_julgamento_ate=&filtroNumeroProcesso="
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
    resultado = resposta.json()
    docs = resultado.get("response", {}).get("docs", [])
    print(f"Encontrei {len(docs)} decisões\n")
    
    for i, doc in enumerate(docs[:3]):
        print(f"--- Decisão {i+1} ---")
        print(f"Processo: {doc.get('numero_processo', 'N/A')}")
        print(f"Relator: {doc.get('nome_relator', 'N/A')}")
        ementa = doc.get('ementa_completa', ['N/A'])
        print(f"Ementa: {ementa[0][:300] if ementa else 'N/A'}")
        print()


def ver_campos(termo):
    url = "https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php"
    
    parametros = (
        f"aba=jurisprudencia&realizando_pesquisa=1&pagina_atual=1"
        f"&q_palavra_chave={termo}&conteudo_busca=ementa_completa"
        f"&filtroComAExpressao=&filtroComQualquerPalavra=&filtroSemAsPalavras="
        f"&filtroTribunal=-1&filtroRelator=-1&filtroOrgaoJulgador=-1"
        f"&filtroTipoProcesso=-1&filtroClasseCnj=-1&assuntoCnj=-1"
        f"&data_julgamento_de=&data_julgamento_ate=&filtroNumeroProcesso="
        f"&data_publicacao_de=&data_publicacao_ate="
        f"&facet=on&facet.sort=index&facet.limit=index&wt=json&ordem=desc&start=0"
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
    resultado = resposta.json()
    docs = resultado.get("response", {}).get("docs", [])
    
    print("Campos disponíveis:")
    for campo, valor in docs[0].items():
        if campo != "documento_text":
            print(f"{campo}: {valor}")


ver_campos("conversao+beneficio+b31+para+b91")