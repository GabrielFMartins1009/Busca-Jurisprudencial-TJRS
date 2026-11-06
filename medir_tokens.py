import sqlite3
import numpy as np
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
conn = sqlite3.connect("jurisprudencia.db")
ementas = [r[0] or "" for r in conn.execute("SELECT ementa_completa FROM decisoes")]
conn.close()

tam = []
for i in range(0, len(ementas), 256):
    lote = tok(ementas[i:i+256], add_special_tokens=True, truncation=False)["input_ids"]
    tam.extend(len(x) for x in lote)
tam = np.array(tam)

print(f"Ementas: {len(tam)}")
print(f"Tokens - media: {tam.mean():.0f} | mediana: {np.median(tam):.0f} | p90: {np.percentile(tam,90):.0f} | max: {tam.max()}")
for lim in (128, 256, 512):
    print(f"Acima de {lim} tokens: {(tam>lim).mean()*100:.1f}%")
print(f"Tokens perdidos em media nas ementas truncadas (>512): {(tam[tam>512]-512).mean():.0f}" if (tam>512).any() else "Nenhuma ementa acima de 512")
