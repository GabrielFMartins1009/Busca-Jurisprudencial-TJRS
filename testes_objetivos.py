"""Teste objetivo e reprodutivel (sem LLM, sem julgamento humano) do sistema de busca.

Para cada uma das 10 consultas de medir_tempos.py compara os tres modos
(semantico, lexical, hibrido/RRF) e mede:
  - sobreposicao do top-5 entre os modos;
  - procedencia do top-5 hibrido (so semantica, so lexical, ambas as listas top-20);
  - quantos documentos do top-5 hibrido NAO estao no top-5 de nenhum dos dois modos
    (ou seja, foram promovidos pela fusao);
  - sobreposicao das listas top-20 que entram no RRF.

Somente leitura no banco. Uso: py -3.11 testes_objetivos.py
Saidas: resultado_objetivo.md e resultado_objetivo.csv
"""
import csv
import statistics as st
import main  # carrega modelo e banco como a API

CONSULTAS = [
    "negativação indevida por dívida já paga",
    "responsabilidade civil por acidente de trânsito",
    "vício oculto em veículo comprado de concessionária",
    "união estável e partilha de bens",
    "fiança locatícia e fiador",
    "erro médico em cirurgia",
    "dano moral em relação de consumo",
    "execução de título extrajudicial",
    "inventário e partilha de herança",
    "plano de saúde negativa de cobertura",
]
K = 5      # top-k avaliado
N = 20     # tamanho das listas que entram no RRF (igual ao sistema)

conn = main.conectar_banco()
cur = conn.cursor()

linhas = []
for q in CONSULTAS:
    sem = main.busca_semantica(cur, q, top_k=N)
    lex = main.busca_lexica(cur, q, top_k=N)
    ranking, _ = main.rrf(sem, lex)

    sem_ids = [r[0] for r in sem]
    lex_ids = [r[0] for r in lex]
    hib_ids = [d for d, _ in ranking]

    s5, l5, h5 = set(sem_ids[:K]), set(lex_ids[:K]), set(hib_ids[:K])
    s20, l20 = set(sem_ids), set(lex_ids)

    so_sem = sum(1 for d in hib_ids[:K] if d in s20 and d not in l20)
    so_lex = sum(1 for d in hib_ids[:K] if d in l20 and d not in s20)
    ambas = sum(1 for d in hib_ids[:K] if d in s20 and d in l20)
    promovidos = len(h5 - s5 - l5)  # no top-5 hibrido, mas em nenhum top-5 isolado

    linhas.append({
        "consulta": q,
        "n_sem": len(sem_ids), "n_lex": len(lex_ids),
        "sem_lex_top5": len(s5 & l5),
        "sem_hib_top5": len(s5 & h5),
        "lex_hib_top5": len(l5 & h5),
        "sem_lex_top20": len(s20 & l20),
        "hib_so_sem": so_sem, "hib_so_lex": so_lex, "hib_ambas": ambas,
        "hib_promovidos": promovidos,
    })
conn.close()

cols = list(linhas[0].keys())
with open("resultado_objetivo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(linhas)


def media(c):
    return st.mean(l[c] for l in linhas)


def mediana(c):
    return st.median(l[c] for l in linhas)


md = ["# Teste objetivo (sem julgamento humano)\n",
      f"{len(CONSULTAS)} consultas, top-{K} por modo, listas de {N} no RRF (k=60).\n",
      "| # | Consulta | Sem∩Lex@5 | Sem∩Híb@5 | Lex∩Híb@5 | Sem∩Lex@20 | Híb: só sem | Híb: só lex | Híb: ambas | Promovidos |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for i, l in enumerate(linhas, 1):
    md.append(f"| {i} | {l['consulta']} | {l['sem_lex_top5']} | {l['sem_hib_top5']} | "
              f"{l['lex_hib_top5']} | {l['sem_lex_top20']} | {l['hib_so_sem']} | "
              f"{l['hib_so_lex']} | {l['hib_ambas']} | {l['hib_promovidos']} |")
md.append("| | **Média** | " + " | ".join(
    f"{media(c):.2f}" for c in ["sem_lex_top5", "sem_hib_top5", "lex_hib_top5", "sem_lex_top20",
                                 "hib_so_sem", "hib_so_lex", "hib_ambas", "hib_promovidos"]) + " |")
md.append("| | **Mediana** | " + " | ".join(
    f"{mediana(c):.1f}" for c in ["sem_lex_top5", "sem_hib_top5", "lex_hib_top5", "sem_lex_top20",
                                   "hib_so_sem", "hib_so_lex", "hib_ambas", "hib_promovidos"]) + " |")
md.append("\nLegenda: Sem∩Lex@5 = documentos em comum entre o top-5 semântico e o lexical (0 a 5). "
          "Híb: só sem/só lex/ambas = em quais listas top-20 estão os 5 resultados do híbrido. "
          "Promovidos = documentos do top-5 híbrido que não estão no top-5 de nenhum modo isolado.\n")
texto = "\n".join(md)
with open("resultado_objetivo.md", "w", encoding="utf-8") as f:
    f.write(texto)
print(texto)
print("\nSalvo em resultado_objetivo.md e resultado_objetivo.csv")
