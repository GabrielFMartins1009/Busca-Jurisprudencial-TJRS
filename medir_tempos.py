"""Mede tempos do sistema (somente leitura no banco). Uso: py -3.11 medir_tempos.py"""
import time, statistics as st
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
RESP1, RESP2 = "Sim, tenho comprovante", "Preciso embasar pedido de danos morais"

def med(xs): return f"média {st.mean(xs):.3f}s | mediana {st.median(xs):.3f}s | mín {min(xs):.3f}s | máx {max(xs):.3f}s"

main.executar_busca(CONSULTAS[0], 5)  # aquecimento (não conta)

direta, sem_t, lex_t = [], [], []
for q in CONSULTAS:
    t = time.perf_counter(); main.executar_busca(q, 5); direta.append(time.perf_counter() - t)
    conn = main.conectar_banco(); cur = conn.cursor()
    t = time.perf_counter(); main.busca_semantica(cur, q, top_k=20); sem_t.append(time.perf_counter() - t)
    t = time.perf_counter(); main.busca_lexica(cur, q, top_k=20); lex_t.append(time.perf_counter() - t)
    conn.close()

ref1, ref2 = [], []
for q in CONSULTAS:
    t = time.perf_counter(); main.refinar(main.ConsultaRequest(consulta=q)); ref1.append(time.perf_counter() - t)
    t = time.perf_counter()
    main.buscar_refinado(main.RefinamentoRequest(consulta=q, resposta1=RESP1, resposta2=RESP2))
    ref2.append(time.perf_counter() - t)

print("\nDispositivo:", main.device)
print("Busca direta (total)      :", med(direta))
print("  só busca semântica      :", med(sem_t))
print("  só busca léxica         :", med(lex_t))
print("Refinar (perguntas, LLM)  :", med(ref1))
print("Buscar refinado (LLM+busca):", med(ref2))
