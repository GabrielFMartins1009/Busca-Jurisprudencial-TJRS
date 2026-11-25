"""Compara os tres modos de busca (semantico, lexico e hibrido) com julgamento CEGO.

Nao usa o modelo de linguagem (sem custo de API) e nao altera o banco.

Fluxo (rode com a API PARADA ou nao, tanto faz):
  1) py -3.11 comparar_modos.py gerar
       -> cria julgar.md (decisoes embaralhadas, SEM dizer de qual modo vieram)
          e gabarito_modos.json (o mapeamento; NAO abra antes de julgar)
  2) Abra julgar.md e, em cada decisao, troque "Relevante:" por "Relevante: S" ou "Relevante: N",
     usando SOMENTE o criterio escrito em cada consulta (ele foi definido antes de ver resultados).
  3) py -3.11 comparar_modos.py calcular
       -> imprime e salva resultado_modos.md com a precisao@5 de cada modo
"""
import json
import random
import re
import sys

import main  # carrega o modelo e o banco como a API

CONSULTAS = [
    {
        "texto": "negativação indevida por dívida já paga",
        "criterio": "relevante = a ementa trata de inscrição ou manutenção indevida em cadastro de inadimplentes.",
    },
    {
        "texto": "responsabilidade civil por acidente de trânsito",
        "criterio": "relevante = a ementa trata de responsabilidade civil por acidente de trânsito com veículo automotor "
                    "(colisão, atropelamento, etc.), com pedido de indenização.",
    },
    {
        "texto": "vício oculto em veículo comprado de concessionária",
        "criterio": "relevante = a ementa trata de vício (oculto ou do produto) em veículo adquirido de concessionária ou revendedora.",
    },
    {
        "texto": "Indenização por danos morais decorrente de negativação indevida de consumidor em cadastro de inadimplentes, "
                 "com comprovante de pagamento, sem prévia notificação pelo credor, cumulada com pedido de exclusão do registro.",
        "criterio": "relevante = a ementa trata de inscrição ou manutenção indevida em cadastro de inadimplentes.",
    },
    {
        "texto": "Responsabilidade civil do condutor de automóvel particular por danos causados a motociclista em acidente "
                 "de trânsito, com pedido de indenização pela vítima.",
        "criterio": "relevante = a ementa trata de acidente de trânsito em que um motociclista foi atingido por automóvel, "
                    "com pedido de indenização.",
    },
]
TOP = 5
ARQ_MD, ARQ_GAB, ARQ_RES = "julgar.md", "gabarito_modos.json", "resultado_modos.md"


def rodar_modos(q):
    conn = main.conectar_banco()
    cur = conn.cursor()
    sem = main.busca_semantica(cur, q, top_k=20)[:TOP]
    lex = main.busca_lexica(cur, q, top_k=20)[:TOP]
    conn.close()
    hib = main.executar_busca(q, TOP)
    docs = {}
    out = {"semantico": [], "lexico": [], "hibrido": []}
    for r in sem:
        docs[r[1]] = (r[5], r[2][:500]); out["semantico"].append(r[1])
    for r in lex:
        docs[r[1]] = (r[5], r[2][:500]); out["lexico"].append(r[1])
    for r in hib:
        docs[r["numero_processo"]] = (r["assunto"], r["ementa"][:500]); out["hibrido"].append(r["numero_processo"])
    return out, docs


def gerar():
    rng = random.Random(2026)
    md = ["# Julgamento cego\n",
          "Troque `Relevante:` por `Relevante: S` ou `Relevante: N` em TODAS as decisoes. "
          "Use apenas o criterio de cada consulta. Nao abra gabarito_modos.json antes de terminar.\n"]
    gab = []
    for i, c in enumerate(CONSULTAS, 1):
        modos, docs = rodar_modos(c["texto"])
        chaves = list(docs.keys())
        rng.shuffle(chaves)
        rotulos = {}
        md.append(f"\n## Consulta {i}: {c['texto']}\n\n**Criterio:** {c['criterio']}\n")
        for j, proc in enumerate(chaves, 1):
            rot = f"{i}.{j}"
            rotulos[rot] = proc
            assunto, ementa = docs[proc]
            md.append(f"\n### {rot}\n\nAssunto CNJ: {assunto}\n\nEmenta (500 primeiros caracteres): {ementa}\n\nRelevante:\n")
        gab.append({"consulta": c["texto"], "rotulos": rotulos, "modos": modos})
    open(ARQ_MD, "w", encoding="utf-8").write("\n".join(md))
    json.dump(gab, open(ARQ_GAB, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(len(g["rotulos"]) for g in gab)
    print(f"Gerado {ARQ_MD} com {total} decisoes para julgar. Preencha 'Relevante: S' ou 'Relevante: N'.")


def calcular():
    texto = open(ARQ_MD, encoding="utf-8").read()
    julg = {}
    for m in re.finditer(r"### (\d+\.\d+)\b.*?Relevante:[ \t]*([SsNn])?[ \t]*(?=\n|$)", texto, re.S):
        julg[m.group(1)] = (m.group(2) or "").upper()
    gab = json.load(open(ARQ_GAB, encoding="utf-8"))
    faltam = [r for g in gab for r in g["rotulos"] if julg.get(r, "") not in ("S", "N")]
    if faltam:
        print(f"Faltam {len(faltam)} julgamentos (ex.: {faltam[:5]}). Preencha todos e rode de novo.")
        return
    linhas = ["# Precisao@5 por modo (julgamento cego)\n",
              "| Consulta | Semantico | Lexico | Hibrido |", "|---|---|---|---|"]
    soma = {"semantico": 0, "lexico": 0, "hibrido": 0}
    for i, g in enumerate(gab, 1):
        inv = {proc: rot for rot, proc in g["rotulos"].items()}
        cel = {}
        for modo, procs in g["modos"].items():
            rel = sum(1 for p in procs if julg[inv[p]] == "S")
            soma[modo] += rel
            cel[modo] = f"{rel}/{len(procs)}"
        linhas.append(f"| {i}. {g['consulta'][:60]}... | {cel['semantico']} | {cel['lexico']} | {cel['hibrido']} |")
    n = len(gab)
    linhas.append(f"| **Media da precisao@5** | {soma['semantico']/(5*n):.2f} | {soma['lexico']/(5*n):.2f} | {soma['hibrido']/(5*n):.2f} |")
    linhas.append("\nSobreposicao entre os top-5 (quantas decisoes iguais):\n")
    for i, g in enumerate(gab, 1):
        m = {k: set(v) for k, v in g["modos"].items()}
        linhas.append(f"- Consulta {i}: sem∩lex={len(m['semantico']&m['lexico'])}, "
                      f"sem∩hib={len(m['semantico']&m['hibrido'])}, lex∩hib={len(m['lexico']&m['hibrido'])}")
    saida = "\n".join(linhas)
    print(saida)
    open(ARQ_RES, "w", encoding="utf-8").write(saida)


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    if modo == "gerar":
        gerar()
    elif modo == "calcular":
        calcular()
    else:
        print(__doc__)
